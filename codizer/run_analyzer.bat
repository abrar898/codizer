@echo off
cd python_backend
call venv\Scripts\activate
cd ..
python analyze_complexity.py
pause 