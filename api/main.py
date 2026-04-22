import json
import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaConsumer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TRADES_TOPIC = 'raw_crypto_trades'
SIGNALS_TOPIC = 'trading_signals'

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

async def consume_kafka_topic(topic: str, msg_type: str):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest"
    )
    
    # Try connecting with retries
    connected = False
    for i in range(20):
        try:
            await consumer.start()
            connected = True
            break
        except Exception as e:
            print(f"Waiting for Kafka ({topic})...")
            await asyncio.sleep(5)
            
    if not connected:
        print(f"Failed to connect to Kafka for topic {topic}")
        return
    
    try:
        async for msg in consumer:
            payload = {
                "type": msg_type,
                "data": msg.value
            }
            await manager.broadcast(payload)
    finally:
        await consumer.stop()

@app.on_event("startup")
async def startup_event():
    # Start background tasks to consume Kafka
    asyncio.create_task(consume_kafka_topic(TRADES_TOPIC, "trade"))
    asyncio.create_task(consume_kafka_topic(SIGNALS_TOPIC, "signal"))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the client, just keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mount the static frontend directory so users can just visit the API URL
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

