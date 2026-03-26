@echo off
echo ============================================
echo   KOKORO TTS - INSTALARE WINDOWS
echo ============================================
echo.

echo [1/3] Verificare Python...
python --version
if %errorlevel% neq 0 (
    echo EROARE: Python nu e instalat sau nu e in PATH!
    echo Descarca de la https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/3] Instalare pachete Python...
pip install kokoro>=0.9.4 soundfile
if %errorlevel% neq 0 (
    echo EROARE la instalare pip packages!
    pause
    exit /b 1
)

echo.
echo [3/3] Verificare espeak-ng...
espeak-ng --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo !! espeak-ng NU e instalat !!
    echo.
    echo PASI MANUALI:
    echo   1. Du-te la: https://github.com/espeak-ng/espeak-ng/releases
    echo   2. Descarca fisierul .msi (ex: espeak-ng-20191129-b702b03-x64.msi)
    echo   3. Instaleaza-l (Next, Next, Install)
    echo   4. Deschide CMD ca Administrator si ruleaza:
    echo      setx PATH "%%PATH%%;C:\Program Files\eSpeak NG" /M
    echo   5. Inchide CMD-ul si redeschide-l
    echo   6. Ruleaza din nou acest script
    echo.
    pause
    exit /b 1
) else (
    echo espeak-ng OK!
)

echo.
echo ============================================
echo   TOTUL E INSTALAT! 
echo   Acum ruleaza: python test_voice.py
echo ============================================
pause
