@echo off
REM =============================================================================
REM  Rotina diaria dos pedidos de calculo por e-mail (CALCULOS/ + .claude/commands/rotina-calculos.md).
REM  Agendada pelo Agendador do Windows: "Faya Barreiros\Calculos por e-mail", todo dia.
REM  Roda o Claude Code sem tela (claude -p), com o login do Claude deste usuario. Log em logs\.
REM  Para rodar a mao: deploy\rotina_calculos.bat
REM =============================================================================
setlocal EnableExtensions
cd /d "%~dp0.."
if not exist logs mkdir logs
for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmm"') do set "QUANDO=%%d"
set "LOG=logs\rotina_calculos_%QUANDO%.log"

REM claude.exe: o do PATH ou o da extensao do VS Code mais nova (a pasta muda a cada atualizacao)
set "CLAUDE="
for /f "delims=" %%c in ('where claude 2^>nul') do if not defined CLAUDE set "CLAUDE=%%c"
if not defined CLAUDE for /f "delims=" %%c in ('powershell -NoProfile -Command "(Get-ChildItem \"$env:USERPROFILE\.vscode\extensions\" -Directory -Filter anthropic.claude-code-* | Sort-Object LastWriteTime -Descending | ForEach-Object { Join-Path $_.FullName 'resources\native-binary\claude.exe' } | Where-Object { Test-Path $_ } | Select-Object -First 1)"') do set "CLAUDE=%%c"
if not defined CLAUDE (
  echo [%date% %time%] ERRO: claude.exe nao encontrado. Instale o Claude Code ou abra o VS Code com a extensao. > "%LOG%"
  exit /b 1
)

set "PASTA_CALC=C:\Users\Faya\OneDrive\ADVOCACIA\CALCULOS 2026"
echo [%date% %time%] Inicio - %CLAUDE% > "%LOG%"
"%CLAUDE%" -p "/rotina-calculos" --permission-mode acceptEdits --add-dir "%PASTA_CALC%" ^
  --allowedTools "Bash(python CALCULOS/main.py:*)" "Bash(python KIT_PREVIDENCIARIO/pecas/gerar_peca.py:*)" ^
  "Bash(python KIT_PREVIDENCIARIO/calculos/simular.py:*)" "Bash(python KIT_PREVIDENCIARIO/leis/buscar_lei.py:*)" ^
  "Read" "Write" "Edit" "Glob" "Grep" "ArtifactData" >> "%LOG%" 2>&1
echo [%date% %time%] Fim (codigo %errorlevel%) >> "%LOG%"
endlocal
