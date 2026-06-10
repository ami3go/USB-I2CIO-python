@echo off
setlocal

python -m venv .venv
if errorlevel 1 goto error

call .venv\Scripts\activate.bat
if errorlevel 1 goto error

python -m pip install --upgrade pip
if errorlevel 1 goto error

python -m pip install -e .[blinka]
if errorlevel 1 goto error

python -c "from devasys_usbi2cio import DevasysUsbI2cIo, DevasysBlinkaI2C; print('Import OK')"
if errorlevel 1 goto error

echo.
echo Installation complete.
echo Run scan:
echo   devasys-i2c-scan --dll UsbI2cIo.dll
goto end

:error
echo Installation failed.
exit /b 1

:end
endlocal
