@echo off
REM Windows CMD — delegates to cross-platform install.py
cd /d "%~dp0\.."
where python >nul 2>&1 && python scripts/install.py %* && goto :done
where py >nul 2>&1 && py -3 scripts/install.py %* && goto :done
echo Python not found. Install Python 3.11+ from https://www.python.org/downloads/
exit /b 1
:done
