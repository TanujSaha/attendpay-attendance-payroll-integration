from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    department: Mapped[str] = mapped_column(String(80))
    designation: Mapped[str] = mapped_column(String(80))
    joining_date: Mapped[date] = mapped_column(Date)
    basic_salary: Mapped[float] = mapped_column(Float)
    bank_last_four: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(20), default="Active")
    attendance = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    payroll = relationship("Payroll", back_populates="employee", cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    check_in: Mapped[str | None] = mapped_column(String(5), nullable=True)
    check_out: Mapped[str | None] = mapped_column(String(5), nullable=True)
    status: Mapped[str] = mapped_column(String(20))
    employee = relationship("Employee", back_populates="attendance")

class Payroll(Base):
    __tablename__ = "payroll"
    __table_args__ = (UniqueConstraint("employee_id", "month", name="uq_payroll_employee_month"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    month: Mapped[str] = mapped_column(String(7))
    working_days: Mapped[int] = mapped_column(Integer)
    present_days: Mapped[int] = mapped_column(Integer)
    paid_leaves: Mapped[int] = mapped_column(Integer)
    unpaid_leaves: Mapped[int] = mapped_column(Integer)
    basic_salary: Mapped[float] = mapped_column(Float)
    overtime: Mapped[float] = mapped_column(Float, default=0)
    deductions: Mapped[float] = mapped_column(Float, default=0)
    net_salary: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="Processed")
    employee = relationship("Employee", back_populates="payroll")

class IntegrationLog(Base):
    __tablename__ = "integration_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    integration_name: Mapped[str] = mapped_column(String(120))
    operation_type: Mapped[str] = mapped_column(String(80))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    successful_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20))
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

class MappingRule(Base):
    __tablename__ = "mapping_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_field: Mapped[str] = mapped_column(String(80), unique=True)
    target_field: Mapped[str] = mapped_column(String(80))
    transformation: Mapped[str] = mapped_column(String(80), default="Direct")
