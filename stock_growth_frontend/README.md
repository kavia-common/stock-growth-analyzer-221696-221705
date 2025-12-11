# Stock Growth Frontend (React) - minimal notes

Configure backend URL:
- Copy .env.example to .env and set REACT_APP_BACKEND_URL if needed.
  - Local: REACT_APP_BACKEND_URL=http://localhost:3001
  - Cloud: REACT_APP_BACKEND_URL=https://<your-host>:3001

CORS:
- Ensure the backend ALLOWED_ORIGINS includes your frontend origin exactly:
  - Local: http://localhost:3000
  - Cloud: https://<your-host>:3000

Verify:
- Backend health: / (Healthy), /docs, and /cors-info for CORS snapshot.
- Frontend console tools (if using 221706 app): import { diagnosticsRun } from './api/client'; diagnosticsRun();
