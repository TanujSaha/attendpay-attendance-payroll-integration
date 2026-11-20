# AttendPay

AttendPay is a full-stack attendance-to-payroll integration MVP built with React, Vite, Tailwind CSS, FastAPI, SQLAlchemy, SQLite and Pandas.

## Features

- Employee CRUD
- CSV attendance import with validation, duplicate detection and integration logs
- Monthly payroll preview and generation
- REST integration endpoints and field mapping view
- Dashboard charts, reports and CSV exports
- Demo SQLite database with seeded employees and payroll data

## Setup

### Backend

```powershell
cd backend
C:/Python314/python.exe -m pip install -r requirements.txt
C:/Python314/python.exe seed.py
C:/Python314/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation: http://127.0.0.1:8000/docs

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Demo CSV

Use `sample_data/attendance.csv` for a mixed-validity import test. It includes valid, duplicate and unknown-employee records.

## Integration Endpoints

- `GET /api/integrations/attendance`
- `POST /api/integrations/sync`
- `GET /api/integrations/logs`
