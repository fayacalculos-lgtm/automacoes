@echo off
REM Sobe o painel do escritorio (PAINEL/servidor.py) e abre o navegador. So neste computador (127.0.0.1:8765).
cd /d "%~dp0.."
start "" /min python PAINEL\servidor.py
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8765
