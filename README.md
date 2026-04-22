# SystemX Terminal — Live Crypto Trading Dashboard

A real-time, event-driven cryptocurrency trading dashboard built with **Apache Kafka**, **FastAPI**, **Python**, and **WebSockets**. Streams live trade data from Binance, processes it to generate algorithmic BUY/SELL signals using Simple Moving Average (SMA), and displays everything on a sleek dark-mode terminal UI.

---

## Screenshots

> Live dashboard running with real Binance trade data and Kafka-powered signal generation.

**Full Terminal View**
![Full Terminal View](Screenshot%202026-04-22%20132338.png)

**Live Order Stream**
![Live Order Stream](Screenshot%202026-04-22%20133409.png)

**Price Chart with SMA Overlay**
![Price Chart with SMA](Screenshot%202026-04-22%20133422.png)

**BUY Signal Generated**
![BUY Signal](Screenshot%202026-04-22%20133452.png)

**SELL Signal Generated**
![SELL Signal](Screenshot%202026-04-22%20133459.png)

**Signal Cards Feed**
![Signal Cards](Screenshot%202026-04-22%20133519.png)

**Chart Markers (BUY/SELL Arrows)**
![Chart Markers](Screenshot%202026-04-22%20133527.png)

---

## How It Works

This project is a fully event-driven pipeline. Here's what happens step by step:

**1. Producer — Fetching Live Data**
The producer connects to the **Binance.US WebSocket** and receives a continuous stream of real trades for BTC, ETH, SOL, and DOGE. Each trade (price, quantity, timestamp, symbol) is immediately published to a **Kafka topic** called `raw_crypto_trades`.

**2. Apache Kafka — The Message Backbone**
Kafka acts as the central message bus between all services. It decouples the producer, processor, and API so each can run independently and at its own pace. Two Kafka topics are used:
- `raw_crypto_trades` — raw trade data from Binance
- `trading_signals` — processed BUY/SELL signals

Kafka is run locally via Docker using the official Confluent images (Kafka + Zookeeper).

**3. Processor — Signal Generation**
The processor is a Kafka consumer that reads from `raw_crypto_trades`. For each symbol it maintains a rolling window of the last 5 prices and calculates the Simple Moving Average (SMA). When the live price deviates from the SMA by more than 0.01%, it publishes a BUY or SELL signal to the `trading_signals` topic.

**4. API — Real-time Bridge**
The FastAPI server consumes both Kafka topics using `aiokafka` and broadcasts every message to all connected browser clients over a **WebSocket** connection at `ws://localhost:8000/ws`.

**5. Dashboard — Live Terminal UI**
The frontend connects to the WebSocket and renders everything in real time:
- Every trade appears in the live order stream
- The price chart updates tick by tick with the SMA line overlaid
- BUY/SELL signals appear as cards and as arrows on the chart

---

```
Binance WebSocket
      │
      ▼
 [Producer]  ──► Kafka Topic: raw_crypto_trades
                        │
                        ▼
                  [Processor]  ──► Kafka Topic: trading_signals
                                          │
                                          ▼
                                      [FastAPI]
                                          │
                                    WebSocket /ws
                                          │
                                          ▼
                                    [Dashboard]
```

| Component | Description |
|-----------|-------------|
| `producer/` | Connects to Binance.US WebSocket and publishes live trades to Kafka topic `raw_crypto_trades` |
| `processor/` | Consumes trades from Kafka, calculates rolling SMA (window=5), emits BUY/SELL signals to `trading_signals` topic |
| `api/` | FastAPI server that consumes both Kafka topics and broadcasts data to the frontend via WebSocket |
| `frontend/` | Dark-mode trading terminal with live price chart, order stream, and signal feed |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Kafka + Zookeeper)
- Python 3.9+

---

## Quick Start (Windows)

1. Make sure **Docker Desktop** is running
2. Double-click `start.bat` or run from Command Prompt:
   ```cmd
   start.bat
   ```
3. Open your browser and go to:
   ```
   http://localhost:8000
   ```
   Or open `frontend/index.html` directly.

The script will automatically:
- Start Kafka and Zookeeper via Docker
- Create a Python virtual environment
- Install all dependencies
- Launch all 3 services in separate terminal windows

---

## Manual Start

**1. Start Kafka (Docker):**
```bash
docker compose up -d
```

**2. Start the API (Terminal 1):**
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**3. Start the Processor (Terminal 2):**
```bash
cd processor
pip install -r requirements.txt
python app.py
```

**4. Start the Producer (Terminal 3):**
```bash
cd producer
pip install -r requirements.txt
python app.py
```

---

## Environment Variables

Create a `.env` file in the root (optional):

```env
KAFKA_BROKER=localhost:9092
```

By default the broker is set to `localhost:9092` which matches the Docker Compose setup.

---

## Data Source

The producer connects to **Binance.US** WebSocket and streams live BTC, ETH, SOL, and DOGE trades. No API key required.

---

## Trading Signal Logic

The processor uses a Simple Moving Average strategy:

- Maintains a rolling price window of the last **5 trades** per symbol
- Calculates SMA from that window
- If `(price - SMA) / SMA > 0.01%` → emits **SELL** signal
- If `(price - SMA) / SMA < -0.01%` → emits **BUY** signal

---

## Dashboard Features

- Live order stream with flash animation (BTC, ETH, SOL, DOGE)
- Real-time price chart with SMA overlay (TradingView Lightweight Charts)
- BUY/SELL signal cards with price, SMA pivot, and chart markers
- Auto-reconnecting WebSocket

---

## Project Structure

```
├── api/
│   ├── main.py              # FastAPI + WebSocket server
│   └── requirements.txt
├── processor/
│   ├── app.py               # SMA signal generator
│   └── requirements.txt
├── producer/
│   ├── app.py               # Binance WebSocket → Kafka
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Dashboard UI
│   ├── app.js               # WebSocket client + chart logic
│   └── style.css            # Dark theme styles
├── docker-compose.yml       # Kafka + Zookeeper
├── start.bat                # One-click Windows launcher
└── .env                     # Environment variables (optional)
```
