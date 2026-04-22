@echo off
echo Starting Kafka Crypto Dashboard...

:: 1. Start Docker Containers for Kafka and Zookeeper
echo 1. Starting Kafka and Zookeeper via Docker Compose...
docker compose up -d
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Compose failed! Make sure Docker Desktop is running.
    pause
    exit /b %ERRORLEVEL%
)

:: 2. Setup standard Python environment
echo 2. Setting up Python virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate

:: 3. Install requirements
echo 3. Installing dependencies...
pip install -r producer\requirements.txt
pip install -r processor\requirements.txt
pip install -r api\requirements.txt

:: 4. Start the Microservices
echo 4. Starting Python Microservices in separate windows...
start "Kafka Producer (Binance Stream)" cmd /k "call venv\Scripts\activate && python producer\app.py"
start "Kafka Processor (Signal Generator)" cmd /k "call venv\Scripts\activate && python processor\app.py"
start "FastAPI Websocket Server" cmd /k "call venv\Scripts\activate && uvicorn api.main:app --host 0.0.0.0 --port 8000"

echo All services started!
pause
