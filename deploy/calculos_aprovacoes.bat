@echo off
REM Verifica de hora em hora (8h-20h) os OKs da Dra. Faya e envia os rascunhos aprovados. So Python, sem Claude.
REM Agendada como "Faya Barreiros\Calculos - envio dos aprovados". Log em logs\calculos_aprovacoes_AAAA-MM.log
cd /d "%~dp0.."
if not exist logs mkdir logs
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM"') do set "MES=%%d"
echo [%date% %time%] >> "logs\calculos_aprovacoes_%MES%.log"
python CALCULOS\main.py aprovacoes >> "logs\calculos_aprovacoes_%MES%.log" 2>&1