@echo off
echo Iniciando Microservicios de Tienda Virtual
echo ========================================

echo.
echo Instalando dependencias...
cd products_service
pip install -r requirements.txt
cd ..\customers_service
pip install -r requirements.txt
cd ..\orders_service
pip install -r requirements.txt
cd ..

echo.
echo Iniciando servicio de Productos (puerto 8001)...
start "Products Service" cmd /k "cd products_service && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo Iniciando servicio de Clientes (puerto 8002)...
start "Customers Service" cmd /k "cd customers_service && python main.py"

timeout /t 3 /nobreak >nul

echo.
echo Iniciando servicio de Pedidos (puerto 8003)...
start "Orders Service" cmd /k "cd orders_service && python main.py"

echo.
echo Todos los servicios iniciados!
echo.
echo Servicios disponibles:
echo - Productos: http://localhost:8001
echo - Clientes: http://localhost:8002
echo - Pedidos: http://localhost:8003
echo.
echo Presione cualquier tecla para cerrar esta ventana...
pause >nul
