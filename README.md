# AttendPay — Attendance to Payroll Integration

AttendPay is a modern attendance-to-payroll management application for small and medium businesses. It demonstrates how employee data, attendance records and payroll processing can be connected into one practical workflow.

**Live application:** https://attendpay-attendance-payroll-integration-p2s8f7240.vercel.app/

## What it demonstrates

- Employee management with add, edit, delete, search and department filtering
- CSV attendance imports with duplicate and invalid-record detection
- REST-based attendance synchronization
- Transparent monthly payroll calculation
- Integration logs for monitoring processing results
- Payroll and attendance report exports
- A responsive, enterprise-style React dashboard

## Technology

- React and Vite
- Tailwind CSS and Lucide icons
- Recharts
- Python and FastAPI
- SQLAlchemy and SQLite
- Pandas

## Core workflow

1. Add or import employee records.
2. Upload attendance records using CSV.
3. Validate employee IDs, dates, statuses and time formats.
4. Reject duplicates and unknown employees.
5. Generate monthly payroll.
6. Review payslip values and integration logs.
7. Export payroll or attendance reports.

## Local setup

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

FastAPI documentation: http://127.0.0.1:8000/docs

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Demo data

The database is initialized with realistic demo employees and attendance records. The application uses SQLite, so employee, attendance and payroll changes remain after a browser refresh.

The sample attendance file is available at:

`sample_data/attendance.csv`

## Integration endpoints

- `GET /api/integrations/attendance`
- `POST /api/integrations/sync`
- `GET /api/integrations/logs`

## Deployment

The backend is designed for deployment as a Python Web Service on Render. The frontend is deployed on Vercel using the Vite build configuration.

For deployed environments, configure:

- `VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com/api` in Vercel
- `FRONTEND_URL=https://YOUR-VERCEL-DOMAIN.vercel.app` in Render
