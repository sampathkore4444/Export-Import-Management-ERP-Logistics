@echo off
echo Starting ERP Backend Services...
echo.

echo Starting Auth Service on port 8001...
start "Auth Service" cmd /k "cd /d %~dp0auth-service && uvicorn main:app --port 8001 --reload"

timeout /t 2 /nobreak >nul

echo Starting Import Service on port 8002...
start "Import Service" cmd /k "cd /d %~dp0import-service && uvicorn main:app --port 8002 --reload"

timeout /t 2 /nobreak >nul

echo Starting Fleet Service on port 8003...
start "Fleet Service" cmd /k "cd /d %~dp0fleet-service && uvicorn main:app --port 8003 --reload"

timeout /t 2 /nobreak >nul

echo Starting Master Data Service on port 8004...
start "Master Data Service" cmd /k "cd /d %~dp0master-data-service && uvicorn main:app --port 8004 --reload"

timeout /t 2 /nobreak >nul

echo Starting AI Service on port 8005...
start "AI Service" cmd /k "cd /d %~dp0ai-service && uvicorn main:app --port 8005 --reload"

timeout /t 2 /nobreak >nul

echo Starting Warehouse Service on port 8006...
start "Warehouse Service" cmd /k "cd /d %~dp0warehouse-service && uvicorn main:app --port 8006 --reload"

timeout /t 2 /nobreak >nul

echo Starting API Gateway on port 8000...
start "API Gateway" cmd /k "cd /d %~dp0api-gateway && uvicorn main:app --port 8000 --reload"

echo.
echo All services started!
echo.
echo Auth Service:     http://localhost:8001
echo Import Service:  http://localhost:8002
echo Fleet Service:    http://localhost:8003
echo Master Data:     http://localhost:8004
echo AI Service:      http://localhost:8005
echo Warehouse:       http://localhost:8006
echo API Gateway:     http://localhost:8000
echo.
echo To register a user, use curl:
echo curl -X POST http://localhost:8001/api/auth/register -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"email\":\"admin@test.com\",\"password\":\"admin123\",\"full_name\":\"Admin\",\"role\":\"admin\"}"
echo.
pause
