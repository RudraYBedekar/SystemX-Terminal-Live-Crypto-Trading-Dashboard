# SystemX Terminal

> A real-time, event-driven cryptocurrency trading dashboard powered by Apache Kafka, FastAPI, and WebSockets.

Streams live trade data directly from Binance, processes it through a Kafka pipeline to generate algorithmic BUY/SELL signals, and renders everything on a professional dark-mode terminal UI — with zero latency.

---

## Why I Built This

I built this project to learn and test **Apache Kafka** in a real-world scenario — not just follow a tutorial.

The idea was simple: instead of building a boring CRUD app, I wanted to see how Kafka handles a genuinely high-frequency, real-time data stream. Cryptocurrency trade data from Binance is perfect for this — it's fast, continuous, and unpredictable, which makes it a great stress test for an event-driven pipeline.

The goal was to answer a few questions for myself:
- Can Kafka reliably decouple a live data producer from multiple consumers without data loss?
- How does a stream processor behave when it needs to maintain state (like a rolling SMA window) across thousands of messages?
- How do you push real-time Kafka events all the way to a browser with minimal latency?

This project is the result of that experiment — a fully working pipeline from raw WebSocket data to a live trading dashboard, with Kafka sitting at the center of it all.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Ingestion | Binance.US WebSocket |
| Message Broker | Apache Kafka + Zookeeper (Docker) |
| Stream Processor | Python (`kafka-python-ng`) |
| Backend API | FastAPI + `aiokafka` |
| Frontend | Vanilla JS, TailwindCSS, TradingView Lightweight Charts |

---

## Architecture

```
Binance WebSocket
       │
       ▼
  [Producer]  ──►  Kafka: raw_crypto_trades
                          │
                          ▼
                    [Processor]  ──►  Kafka: trading_signals
                                              │
                                              ▼
                                          [FastAPI]
                                              │
                                        WebSocket /ws
                                              │
                                              ▼
                                        [Dashboard]
```

---

## How It Works

**1. Producer**
Connects to the Binance.US WebSocket and receives a live stream of trades for BTC, ETH, SOL, and DOGE. Each trade is serialized and published to the Kafka topic `raw_crypto_trades`.

**2. Apache Kafka**
Acts as the central message bus, decoupling all services so they run independently. Two topics are used:
- `raw_crypto_trades` — raw trade events from Binance
- `trading_signals` — processed BUY/SELL signals

**3. Processor**
Consumes `raw_crypto_trades` and maintains a rolling price window (last 5 trades) per symbol. Calculates the Simple Moving Average (SMA) and emits a signal when the live price deviates by more than 0.01%.

**4. API**
FastAPI server consumes both Kafka topics asynchronously and broadcasts all events to connected browser clients over WebSocket at `ws://localhost:8000/ws`.

**5. Dashboard**
Connects to the WebSocket and renders live data — trade feed, price chart with SMA overlay, and BUY/SELL signal cards with chart markers.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.9+

---

## Quick Start

1. Make sure **Docker Desktop** is running
2. Run from Command Prompt in the project root:
   ```cmd
   start.bat
   ```
3. Open your browser:
   ```
   http://localhost:8000
   ```

`start.bat` handles everything — starts Kafka via Docker, sets up the Python virtual environment, installs dependencies, and launches all 3 services in separate terminal windows.

---

## Manual Start

```bash
# 1. Start Kafka + Zookeeper
docker compose up -d

# 2. API server
cd api && pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Stream processor
cd processor && pip install -r requirements.txt
python app.py

# 4. Trade producer
cd producer && pip install -r requirements.txt
python app.py
```

---

## Configuration

Create a `.env` file in the project root if you need to override defaults:

```env
KAFKA_BROKER=localhost:9092
```

---

## Signal Logic

The processor uses a Simple Moving Average (SMA) deviation strategy:

```
window = last 5 prices per symbol
sma    = average(window)
dev    = (price - sma) / sma

dev >  0.01%  →  SELL  (price overvalued)
dev < -0.01%  →  BUY   (price undervalued)
```

---

## Project Structure

```
├── api/
│   ├── main.py              # FastAPI + WebSocket server
│   └── requirements.txt
├── processor/
│   ├── app.py               # Kafka consumer + SMA signal generator
│   └── requirements.txt
├── producer/
│   ├── app.py               # Binance WebSocket → Kafka producer
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Dashboard UI
│   ├── app.js               # WebSocket client + chart logic
│   └── style.css            # Dark theme styles
├── docker-compose.yml       # Kafka + Zookeeper setup
├── start.bat                # One-click Windows launcher
└── .env                     # Environment config (optional)
```

---

## Screenshots

<table>
  <tr>
    <td align="center">
      <img src="assets/LiveOrderStream.png" alt="Live Order Stream" width="100%"/>
    </td>
    <td align="center">
      <img src="assets/PriceChartwithSMA.png" alt="Price Chart with SMA" width="100%"/>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/SELLSignal.png" alt="SELL Signal" width="100%"/>
    </td>
    <td align="center">
      <img src="assets/SignalCard.png" alt="Signal Cards" width="100%"/>
    </td>
  </tr>
</table>

**Full Dashboard**

![Full Dashboard](FullDashbaord.png)
