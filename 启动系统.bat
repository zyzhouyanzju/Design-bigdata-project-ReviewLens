@echo off
cd /d "%~dp0"
set "PYTHONPATH=%~dp0.local_packages;%PYTHONPATH%"

if exist "D:\Anaconda\python.exe" (
    "D:\Anaconda\python.exe" -m streamlit run demo.py
) else (
    python -m streamlit run demo.py
)
pause
