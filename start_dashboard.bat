@echo off
echo Starting VectorEco Dashboard...

:: Start Docker Compose in the background
docker compose up -d

:: Wait a few seconds for the server to become ready
timeout /t 5 /nobreak > nul

:: Open the dashboard in the default browser
start http://localhost:8000/dashboard/

echo Dashboard is running at http://localhost:8000/dashboard/
echo To stop it, run: docker compose down