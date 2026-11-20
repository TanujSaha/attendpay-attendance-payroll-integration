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

## Deploy on Render and Vercel

### 1. Deploy the FastAPI backend on Render

1. Push the repository to GitHub.
2. In Render, select **New > Blueprint** and connect this repository.
3. Render will read `render.yaml` and create `attendpay-api`.
4. After deployment, copy the Render URL, for example `https://attendpay-api.onrender.com`.
5. The backend uses a persistent SQLite disk mounted at `/var/data`.

If deploying manually instead of a Blueprint, use:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variable: `DATABASE_URL=sqlite:////var/data/attendpay.db`
- Environment variable: `FRONTEND_URL=https://YOUR-VERCEL-DOMAIN.vercel.app`
- Add a persistent disk mounted at `/var/data` if SQLite data must survive restarts.

### 2. Deploy the React frontend on Vercel

1. Import the GitHub repository in Vercel.
2. Set **Root Directory** to `frontend`.
3. Add this environment variable:
   `VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com/api`
4. Deploy the project. Vercel detects Vite automatically.

After the Vercel URL is known, return to Render and set `FRONTEND_URL` to that exact Vercel URL, then restart the backend service.
