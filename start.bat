@echo off
echo ==========================================
echo   MedAI - Clinical Intelligence Platform
echo ==========================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo [2/4] Installing dependencies...
pip install -r requirements.txt

echo [3/4] Setting up environment...
if not exist .env (
    copy .env.example .env
    echo.
    echo  ** IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY **
    echo.
    notepad .env
)

echo [4/4] Starting MedAI...
python run.py
