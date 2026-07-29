@echo off
echo Starting Developer Brain via Docker...

:: Handle .env file
if not exist .env (
    echo Creating .env from .env.docker.example...
    copy .env.docker.example .env
)

echo.
echo ==========================================
echo Starting Docker Containers...
echo This may take a few minutes on the first run.
echo ==========================================
echo.

:: We use --no-cache to ensure a completely fresh build
:: This solves the stubborn "ModuleNotFoundError" cache issues
echo Building containers (this will take a few minutes)...
docker-compose build --no-cache
echo.
echo Starting containers...
docker-compose up

pause
