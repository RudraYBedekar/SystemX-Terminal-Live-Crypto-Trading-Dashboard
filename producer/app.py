import json
import logging
import websocket
import time
import os
from kafka import KafkaProducer
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Kafka Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = 'raw_crypto_trades'

producer = None
for i in range(20):
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        logging.info(f"Connected to Kafka broker at {KAFKA_BROKER}")
        break
    except Exception as e:
        logging.warning(f"Waiting for Kafka broker... retrying in 5 seconds")
        time.sleep(5)

if not producer:
    logging.error("Failed to connect to Kafka. Exiting.")
    exit(1)

def on_message(ws, message):
    try:
        raw_data = json.loads(message)
        
        # 1. Handle Finnhub format (List of trades)
        if raw_data.get("type") == "trade":
            trades = raw_data.get("data", [])
            for data in trades:
                symbol = data.get("s", "").replace("BINANCE:", "")
                trade_payload = {
                    "symbol": symbol,
                    "price": float(data.get("p")),
                    "quantity": float(data.get("v")),
                    "trade_time": data.get("t"),
                    "is_market_maker": False
                }
                producer.send(KAFKA_TOPIC, trade_payload)
                logging.info(f"Produced Finnhub trade: {symbol}")
        
        # 2. Handle Binance combined stream format (e.g., Binance.US or Binance.com)
        elif "stream" in raw_data and "data" in raw_data:
            data = raw_data["data"]
            if "s" in data and "p" in data:
                trade_payload = {
                    "symbol": data["s"],
                    "price": float(data["p"]),
                    "quantity": float(data["q"]),
                    "trade_time": data["T"],
                    "is_market_maker": data["m"]
                }
                producer.send(KAFKA_TOPIC, trade_payload)
                logging.info(f"Produced Binance trade: {data['s']} - ${data['p']}")

        # 3. Handle Binance raw stream format
        elif "s" in raw_data and "p" in raw_data:
            trade_payload = {
                "symbol": raw_data["s"],
                "price": float(raw_data["p"]),
                "quantity": float(raw_data["q"]),
                "trade_time": raw_data["T"],
                "is_market_maker": raw_data["m"]
            }
            producer.send(KAFKA_TOPIC, trade_payload)
            logging.info(f"Produced Raw trade: {raw_data['s']}")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def on_error(ws, error):
    logging.error(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.warning("WebSocket connection closed.")

def on_open(ws):
    logging.info("WebSocket connection opened. Subscribing to trades...")
    # Subscription logic for Finnhub
    if "finnhub" in ws.url:
        symbols = ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:SOLUSDT", "BINANCE:DOGEUSDT"]
        for s in symbols:
            ws.send(json.dumps({"type": "subscribe", "symbol": s}))

if __name__ == "__main__":
    binance_us_url = "wss://stream.binance.us:9443/stream?streams=btcusdt@trade/ethusdt@trade/solusdt@trade/dogeusdt@trade"

    logging.info("Connecting to Binance.US...")
    ws = websocket.WebSocketApp(
        binance_us_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever(ping_interval=10, ping_timeout=5)
