import json
import logging
import time
from collections import deque
import os
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
INPUT_TOPIC = 'raw_crypto_trades'
OUTPUT_TOPIC = 'trading_signals'

WINDOW_SIZE = 5
THRESHOLD_PERCENT = 0.0001  # 0.01%

def run_processor():
    consumer = None
    producer = None
    for i in range(20):
        try:
            consumer = KafkaConsumer(
                INPUT_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logging.info(f"Processor started. Consuming '{INPUT_TOPIC}', producing '{OUTPUT_TOPIC}'")
            break
        except Exception as e:
            logging.warning(f"Waiting for Kafka broker... retrying in 5 seconds")
            time.sleep(5)
            
    if not consumer or not producer:
        logging.error(f"Failed to connect to Kafka after multiple retries.")
        return

    price_histories = {}

    for message in consumer:
        try:
            trade = message.value
            current_price = trade['price']
            symbol = trade['symbol']
            
            if symbol not in price_histories:
                price_histories[symbol] = deque(maxlen=WINDOW_SIZE)
                
            history = price_histories[symbol]
            history.append(current_price)
            
            if len(history) == WINDOW_SIZE:
                sma = sum(history) / WINDOW_SIZE
                
                # Deviation
                dev = (current_price - sma) / sma
                
                signal = None
                if dev > THRESHOLD_PERCENT:
                    signal = "SELL" # price is unusually high, sell!
                elif dev < -THRESHOLD_PERCENT:
                    signal = "BUY"  # price is unusually low, buy!
                    
                if signal:
                    signal_payload = {
                        "symbol": symbol,
                        "price": current_price,
                        "sma": sma,
                        "signal": signal,
                        "time": trade['trade_time']
                    }
                    producer.send(OUTPUT_TOPIC, signal_payload)
                    logging.info(f"Generated {signal} signal at price {current_price} (SMA: {sma:.2f})")
                    
        except Exception as e:
            logging.error(f"Error processing trade: {e}")

if __name__ == "__main__":
    run_processor()
