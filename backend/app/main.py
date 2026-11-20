from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from calendar import monthrange
from io import BytesIO, StringIO
import pandas as pd
import re
import os

from app.database import engine, Base, get_db
from app.models import Employee, Attendance, Payroll, IntegrationLog, MappingRule

Base.metadata.create_all(bind=engine)
app = FastAPI(title="AttendPay API", version="1.0.0")

allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL").rstrip("/"))
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class EmployeeIn(BaseModel):
    employee_id: str
    full_name: str
    email: str
    department: str
    designation: str
    joining_date: date
    basic_salary: float
    bank_last_four: str
    status: str = "Active"

class SyncIn(BaseModel):
    records: list[dict]

def log(db: Session, name: str, operation: str, processed=0, success=0, failed=0, status="Success", error=None):
    db.add(IntegrationLog(integration_name=name, operation_type=operation, records_processed=processed,
                          successful_records=success, failed_records=failed, status=status, error_message=error))
    db.commit()

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail":"An unexpected server error occurred","error":str(exc)})

@app.get("/api/dashboard/stats")
def dashboard(db: Session = Depends(get_db)):
    month = "2026-11"
    employees = db.query(Employee).count()
    today = date(2026,11,21)
    present_today = db.query(Attendance).filter(Attendance.date==today, Attendance.status=="Present").count()
    absent_today = db.query(Attendance).filter(Attendance.date==today, Attendance.status=="Absent").count()
    payroll_rows = db.query(Payroll).filter(Payroll.month==month).all()
    return {"totalEmployees":employees, "presentToday":present_today, "absentToday":absent_today,
            "payrollProcessed":len(payroll_rows), "monthlyPayroll":round(sum(p.net_salary for p in payroll_rows),2),
            "activeEmployees":db.query(Employee).filter(Employee.status=="Active").count()}

@app.get("/api/employees")
def employees(search: str="", department: str="", db: Session = Depends(get_db)):
    q = db.query(Employee)
    if search:
        q = q.filter(or_(Employee.full_name.ilike(f"%{search}%"), Employee.employee_id.ilike(f"%{search}%")))
    if department:
        q = q.filter(Employee.department==department)
    return [{"id":e.id,"employee_id":e.employee_id,"full_name":e.full_name,"email":e.email,
             "department":e.department,"designation":e.designation,"joining_date":e.joining_date.isoformat(),
             "basic_salary":e.basic_salary,"bank_last_four":e.bank_last_four,"status":e.status} for e in q.all()]

@app.post("/api/employees", status_code=201)
def create_employee(payload: EmployeeIn, db: Session = Depends(get_db)):
    if db.query(Employee).filter(or_(Employee.employee_id==payload.employee_id, Employee.email==payload.email)).first():
        raise HTTPException(409,"Employee ID or email already exists")
    e = Employee(**payload.model_dump()); db.add(e); db.commit(); db.refresh(e)
    return {"id":e.id,"employee_id":e.employee_id,"full_name":e.full_name}

@app.put("/api/employees/{employee_id}")
def update_employee(employee_id: str, payload: EmployeeIn, db: Session = Depends(get_db)):
    e = db.query(Employee).filter(Employee.employee_id==employee_id).first()
    if not e: raise HTTPException(404,"Employee not found")
    for k,v in payload.model_dump().items(): setattr(e,k,v)
    db.commit(); return {"message":"Employee updated"}

@app.delete("/api/employees/{employee_id}")
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    e = db.query(Employee).filter(Employee.employee_id==employee_id).first()
    if not e: raise HTTPException(404,"Employee not found")
    db.delete(e); db.commit(); return {"message":"Employee deleted"}

@app.get("/api/attendance")
def attendance(date: str="", employee_id: str="", db: Session = Depends(get_db)):
    q=db.query(Attendance).join(Employee)
    if date:
        q=q.filter(Attendance.date==date)
    if employee_id:
        q=q.filter(Employee.employee_id==employee_id)
    rows=q.order_by(Attendance.date.desc()).all()
    return [{"id":a.id,"employee_id":a.employee.employee_id,"employee_name":a.employee.full_name,
             "date":a.date.isoformat(),"check_in":a.check_in,"check_out":a.check_out,"status":a.status} for a in rows]

@app.post("/api/attendance/import")
def import_attendance(file: UploadFile=File(...), db: Session=Depends(get_db)):
    try:
        df=pd.read_csv(file.file)
    except Exception as exc:
        log(db,"CSV Attendance Import","CSV Import",0,0,1,"Failed",str(exc))
        raise HTTPException(400,"Invalid CSV file")
    required={"employee_id","date","check_in","check_out","status"}
    if not required.issubset(set(df.columns)):
        log(db,"CSV Attendance Import","CSV Import",0,0,len(df),"Failed","Missing required CSV columns")
        raise HTTPException(400,"CSV must contain employee_id, date, check_in, check_out, status")
    processed=success=failed=0; errors=[]
    for _,row in df.iterrows():
        processed += 1
        eid=str(row["employee_id"]).strip(); emp=db.query(Employee).filter(Employee.employee_id==eid).first()
        try:
            att_date=pd.to_datetime(row["date"]).date()
        except Exception:
            failed+=1; errors.append({"row":processed,"reason":"Invalid date"}); continue
        status=str(row["status"]).strip().title()
        if status not in ("Present","Absent","Leave"):
            failed+=1; errors.append({"row":processed,"reason":"Invalid attendance status"}); continue
        check_in=None if pd.isna(row["check_in"]) else str(row["check_in"]).strip()
        check_out=None if pd.isna(row["check_out"]) else str(row["check_out"]).strip()
        if status=="Present" and (not valid_time(check_in) or not valid_time(check_out) or not check_in or not check_out):
            failed+=1; errors.append({"row":processed,"reason":"Invalid check-in or check-out time"}); continue
        if status=="Present" and check_in and check_out and check_in >= check_out:
            failed+=1; errors.append({"row":processed,"reason":"Check-out must be after check-in"}); continue
        if not emp:
            failed+=1; errors.append({"row":processed,"reason":"Employee ID does not exist"}); continue
        exists=db.query(Attendance).filter(Attendance.employee_id==emp.id,Attendance.date==att_date).first()
        if exists:
            failed+=1; errors.append({"row":processed,"reason":"Duplicate attendance record"}); continue
        db.add(Attendance(employee_id=emp.id,date=att_date,check_in=check_in,
                          check_out=check_out,status=status))
        success+=1
    db.commit()
    status="Success" if failed==0 else ("Partial Success" if success>0 else "Failed")
    log(db,"CSV Attendance Import","CSV Import",processed,success,failed,status,
        "; ".join(f"Row {e['row']}: {e['reason']}" for e in errors[:5]) or None)
    return {"processed":processed,"successful":success,"failed":failed,"errors":errors}

@app.post("/api/integrations/sync")
def sync(payload: SyncIn, db: Session=Depends(get_db)):
    success=0; failed=0; errors=[]
    for i,record in enumerate(payload.records,1):
        eid=str(record.get("employee_id","")).strip(); emp=db.query(Employee).filter(Employee.employee_id==eid).first()
        if not emp:
            failed+=1; errors.append(f"Row {i}: Employee ID does not exist"); continue
        try:
            att_date=pd.to_datetime(record.get("date")).date(); status=str(record.get("status","")).strip().title()
        except Exception:
            failed+=1; errors.append(f"Row {i}: Invalid date"); continue
        if status not in ("Present","Absent","Leave"):
            failed+=1; errors.append(f"Row {i}: Invalid status"); continue
        check_in=record.get("check_in"); check_out=record.get("check_out")
        if status=="Present" and (not valid_time(check_in) or not valid_time(check_out) or not check_in or not check_out):
            failed+=1; errors.append(f"Row {i}: Invalid check-in or check-out time"); continue
        if status=="Present" and check_in >= check_out:
            failed+=1; errors.append(f"Row {i}: Check-out must be after check-in"); continue
        if db.query(Attendance).filter(Attendance.employee_id==emp.id,Attendance.date==att_date).first():
            failed+=1; errors.append(f"Row {i}: Duplicate record"); continue
        db.add(Attendance(employee_id=emp.id,date=att_date,check_in=check_in,check_out=check_out,status=status)); success+=1
    db.commit(); processed=len(payload.records); status="Success" if failed==0 else ("Partial Success" if success else "Failed")
    log(db,"External Attendance API","API Synchronization",processed,success,failed,status,"; ".join(errors[:5]) or None)
    return {"processed":processed,"successful":success,"failed":failed,"errors":errors}

@app.get("/api/integrations/attendance")
def external_attendance(db: Session=Depends(get_db)):
    return [{"employee_id":a.employee.employee_id,"date":a.date.isoformat(),"check_in":a.check_in,"check_out":a.check_out,"status":a.status}
            for a in db.query(Attendance).order_by(Attendance.date.desc()).limit(100).all()]

@app.get("/api/integrations/mappings")
def mappings(db: Session=Depends(get_db)):
    return [{"source_field":m.source_field,"target_field":m.target_field,"transformation":m.transformation} for m in db.query(MappingRule).all()]

@app.get("/api/payroll")
def payroll(month: str="2026-11", db: Session=Depends(get_db)):
    rows=db.query(Payroll).join(Employee).filter(Payroll.month==month).all()
    return [{"id":p.id,"employee_id":p.employee.employee_id,"employee_name":p.employee.full_name,
             "department":p.employee.department,"month":p.month,"working_days":p.working_days,"present_days":p.present_days,
             "paid_leaves":p.paid_leaves,"unpaid_leaves":p.unpaid_leaves,"basic_salary":p.basic_salary,
             "overtime":p.overtime,"deductions":p.deductions,"net_salary":p.net_salary,"status":p.status} for p in rows]

@app.post("/api/payroll/generate")
def generate_payroll(payload: dict, db: Session=Depends(get_db)):
    month=payload.get("month","2026-11")
    working=int(payload.get("working_days",20)); overtime_rate=float(payload.get("overtime_rate",250)); deduction_rate=float(payload.get("deduction_rate",0.02))
    success=0; skipped=0
    try:
        year,mon=map(int,month.split("-")); start=date(year,mon,1); end=date(year,mon,monthrange(year,mon)[1])
    except Exception: raise HTTPException(400,"Invalid month")
    for emp in db.query(Employee).filter(Employee.status=="Active").all():
        if db.query(Payroll).filter(Payroll.employee_id==emp.id,Payroll.month==month).first(): skipped+=1; continue
        rows=db.query(Attendance).filter(Attendance.employee_id==emp.id,Attendance.date>=start,Attendance.date<=end).all()
        present=sum(r.status=="Present" for r in rows); paid=sum(r.status=="Leave" for r in rows)
        unpaid=max(0,working-present-paid); overtime=round(present * overtime_rate * 0.02,2)
        basic=emp.basic_salary; deductions=round(basic*deduction_rate,2); net=round(basic/working*(present+paid)+overtime-deductions,2)
        db.add(Payroll(employee_id=emp.id,month=month,working_days=working,present_days=present,paid_leaves=paid,
                       unpaid_leaves=unpaid,basic_salary=basic,overtime=round(overtime,2),deductions=deductions,net_salary=net,status="Processed")); success+=1
    db.commit(); log(db,"Payroll Engine","Monthly Payroll Generation",success+skipped,success,0,"Success" if success else "Partial Success",None)
    return {"generated":success,"skipped":skipped,"month":month}

@app.get("/api/integrations/logs")
def logs(status: str="", db: Session=Depends(get_db)):
    q=db.query(IntegrationLog)
    if status: q=q.filter(IntegrationLog.status==status)
    return [{"id":l.id,"integration_name":l.integration_name,"operation_type":l.operation_type,
             "timestamp":l.timestamp.isoformat(),"records_processed":l.records_processed,"successful_records":l.successful_records,
             "failed_records":l.failed_records,"status":l.status,"error_message":l.error_message} for l in q.order_by(IntegrationLog.timestamp.desc()).all()]

@app.get("/api/reports/payroll")
def report_payroll(month: str="2026-11", db: Session=Depends(get_db)):
    rows=db.query(Payroll).join(Employee).filter(Payroll.month==month).all()
    return [{"employee_id":p.employee.employee_id,"employee_name":p.employee.full_name,"department":p.employee.department,
             "month":p.month,"present_days":p.present_days,"paid_leaves":p.paid_leaves,"unpaid_leaves":p.unpaid_leaves,
             "basic_salary":p.basic_salary,"overtime":p.overtime,"deductions":p.deductions,"net_salary":p.net_salary} for p in rows]

@app.get("/api/reports/export")
def export_report(type: str="payroll", month: str="2026-11", db: Session=Depends(get_db)):
    if type=="payroll": data=report_payroll(month,db)
    else:
        rows=db.query(Attendance).join(Employee).all(); data=[{"employee_id":a.employee.employee_id,"employee_name":a.employee.full_name,"date":a.date.isoformat(),"status":a.status,"check_in":a.check_in or "","check_out":a.check_out or ""} for a in rows]
    df=pd.DataFrame(data)
    return StreamingResponse(BytesIO(df.to_csv(index=False).encode()),media_type="text/csv",headers={"Content-Disposition":f'attachment; filename="{type}_{month}.csv"'})

@app.get("/api/payroll/{payroll_id}/payslip")
def payslip(payroll_id:int, db:Session=Depends(get_db)):
    p=db.query(Payroll).filter(Payroll.id==payroll_id).first()
    if not p: raise HTTPException(404,"Payroll record not found")
    text=f"ATTENDPAY PAYSLIP\nEmployee: {p.employee.full_name} ({p.employee.employee_id})\nMonth: {p.month}\nPresent days: {p.present_days}\nPaid leaves: {p.paid_leaves}\nBasic salary: INR {p.basic_salary:.2f}\nOvertime: INR {p.overtime:.2f}\nDeductions: INR {p.deductions:.2f}\nNET SALARY: INR {p.net_salary:.2f}\nStatus: {p.status}"
    return {"filename":f"payslip_{p.employee.employee_id}_{p.month}.txt","content":text}

@app.get("/")
def root(): return {"name":"AttendPay API","docs":"/docs","status":"running"}

def valid_time(value):
    if value is None:
        return True
    text=str(value).strip()
    return bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", text))
