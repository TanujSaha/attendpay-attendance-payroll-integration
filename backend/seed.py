from app.database import engine, SessionLocal, Base
from app.models import Employee, Attendance, Payroll, MappingRule
from datetime import date, datetime
import random

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Employee).count() == 0:
    employees = [
        ("EMP001","Aarav Sharma","aarav.sharma@attendpay.demo","Engineering","Senior Developer",45000),
        ("EMP002","Maya Patel","maya.patel@attendpay.demo","Engineering","Frontend Developer",38000),
        ("EMP003","Rohan Mehta","rohan.mehta@attendpay.demo","Finance","Payroll Analyst",42000),
        ("EMP004","Ananya Gupta","ananya.gupta@attendpay.demo","Human Resources","HR Manager",48000),
        ("EMP005","Vikram Singh","vikram.singh@attendpay.demo","Sales","Account Executive",36000),
        ("EMP006","Priya Nair","priya.nair@attendpay.demo","Marketing","Marketing Lead",44000),
        ("EMP007","Kabir Das","kabir.das@attendpay.demo","Operations","Operations Analyst",34000),
        ("EMP008","Ishita Roy","ishita.roy@attendpay.demo","Engineering","QA Engineer",37000),
        ("EMP009","Arjun Kapoor","arjun.kapoor@attendpay.demo","Finance","Financial Analyst",41000),
        ("EMP010","Neha Verma","neha.verma@attendpay.demo","Human Resources","HR Executive",32000),
        ("EMP011","Dev Malhotra","dev.malhotra@attendpay.demo","Sales","Sales Manager",52000),
        ("EMP012","Sara Khan","sara.khan@attendpay.demo","Operations","Team Coordinator",35000),
    ]
    for i, (eid, name, email, dept, role, salary) in enumerate(employees):
        emp = Employee(employee_id=eid, full_name=name, email=email, department=dept,
                       designation=role, joining_date=date(2024, (i % 12)+1, 10),
                       basic_salary=salary, bank_last_four=f"{1000+i*137%9000:04d}", status="Active")
        db.add(emp)
    db.flush()
    month = "2026-11"
    for emp in db.query(Employee).all():
        for day in range(1, 22):
            d = date(2026, 11, day)
            if d.weekday() >= 5:
                continue
            r = random.random()
            status = "Absent" if r < 0.06 else ("Leave" if r < 0.11 else "Present")
            db.add(Attendance(employee_id=emp.id, date=d, check_in="09:00" if status == "Present" else None,
                              check_out="18:00" if status == "Present" else None, status=status))
    db.flush()
    for emp in db.query(Employee).all():
        present = db.query(Attendance).filter(Attendance.employee_id==emp.id, Attendance.status=="Present").count()
        leaves = db.query(Attendance).filter(Attendance.employee_id==emp.id, Attendance.status=="Leave").count()
        working = 20
        overtime = round(present * 250 * 0.04, 2)
        net = emp.basic_salary / working * (present + leaves) + overtime - emp.basic_salary * 0.02
        db.add(Payroll(employee_id=emp.id, month=month, working_days=working, present_days=present,
                       paid_leaves=leaves, unpaid_leaves=max(0, working-present-leaves), basic_salary=emp.basic_salary,
                       overtime=overtime, deductions=round(emp.basic_salary*0.02,2), net_salary=round(net,2), status="Processed"))

for source, target, transform in [("employee_id","employee_id","Trim"),("date","date","ISO date"),("status","status","Normalize")]:
    if not db.query(MappingRule).filter_by(source_field=source).first():
        db.add(MappingRule(source_field=source, target_field=target, transformation=transform))
db.commit()
db.close()
print("AttendPay database seeded successfully")
