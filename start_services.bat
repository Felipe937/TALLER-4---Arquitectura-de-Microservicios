@echo off
setlocal

set "ROOT=%~dp0"

echo ================================================
echo   Tienda Virtual - Microservicios FastAPI
echo ================================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: No se encontro el lanzador de Python ^(py^).
    echo Instale Python 3.11 o superior y vuelva a intentarlo.
    pause
    exit /b 1
)

echo Cerrando instancias anteriores de los microservicios...
taskkill /FI "WINDOWTITLE eq Products Service" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Customers Service" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Orders Service" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Payments Service" /T /F >nul 2>&1
timeout /t 1 /nobreak >nul

echo Instalando dependencias...
py -m pip install -r "%ROOT%requirements.txt"
if errorlevel 1 (
    echo ERROR: No fue posible instalar las dependencias.
    pause
    exit /b 1
)

echo.
echo Iniciando Productos en http://localhost:8001 ...
start "Products Service" /D "%ROOT%products_service" cmd /k "py main.py"

timeout /t 2 /nobreak >nul

echo Iniciando Clientes en http://localhost:8002 ...
start "Customers Service" /D "%ROOT%customers_service" cmd /k "py main.py"

timeout /t 2 /nobreak >nul

echo Iniciando Pedidos en http://localhost:8003 ...
start "Orders Service" /D "%ROOT%orders_service" cmd /k "py main.py"

timeout /t 2 /nobreak >nul

echo Iniciando Pagos en http://localhost:8004 ...
start "Payments Service" /D "%ROOT%payments_service" cmd /k "py main.py"

timeout /t 2 /nobreak >nul

echo Iniciando Dashboard Web en http://localhost:5500/index.html ...
start "Web Dashboard" /D "%ROOT%" cmd /k "py -m http.server 5500"
start "" "http://localhost:5500/index.html"

echo.
echo Servicios iniciados.
echo Dashboard Web:      http://localhost:5500/index.html
echo Swagger Productos: http://localhost:8001/docs
echo Swagger Clientes:  http://localhost:8002/docs
echo Swagger Pedidos:   http://localhost:8003/docs
echo Swagger Pagos:     http://localhost:8004/docs
echo.
pause
