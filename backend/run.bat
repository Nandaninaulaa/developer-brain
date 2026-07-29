@echo off
echo Starting Developer Brain (Django Edition)...

:: Handle .env file
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

:: Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment and install requirements
echo Activating virtual environment and checking dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

:: Run migrations
echo Preparing database...
python manage.py migrate

:: Start the server
echo.
echo ==========================================
echo Server starting at http://127.0.0.1:8000
echo ==========================================
python manage.py runserver 0.0.0.0:8000
pause
