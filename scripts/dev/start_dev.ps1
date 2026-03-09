# Start the development environment
# Run from the repo root

Write-Host "Starting PostgreSQL (Docker)..." -ForegroundColor Cyan
docker compose -f infra/docker/docker-compose.yml up db -d

Write-Host "Waiting for DB to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Write-Host "Starting API server..." -ForegroundColor Cyan
$env:DATABASE_URL = "postgresql+asyncpg://referee:referee@localhost:5432/referee_db"
$env:DATABASE_URL_SYNC = "postgresql+psycopg2://referee:referee@localhost:5432/referee_db"
$env:PYTHONPATH = (Get-Location).Path
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$((Get-Location).Path)'; `$env:PYTHONPATH='$((Get-Location).Path)'; uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host "Starting frontend dev server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$((Get-Location).Path)\apps\web'; npm run dev"

Write-Host ""
Write-Host "Dev environment started:" -ForegroundColor Green
Write-Host "  API:      http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
