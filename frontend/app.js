// App logic

// App logic

// 1. WebSocket Connection
let ws;
const statusEl = document.getElementById('connection-status');

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
        statusEl.innerHTML = '<span class="text-green-500 font-bold">● CONNECTED</span>';
    };

    ws.onclose = () => {
        statusEl.innerHTML = '<span class="text-red-500 font-bold">● RECONNECTING...</span>';
        setTimeout(connectWebSocket, 2000); // Try to reconnect every 2 seconds
    };

    ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        handlePayload(payload);
    };

    ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
    };
}
connectWebSocket();

// 2. Initialize Chart
const chartContainer = document.getElementById('chart-container');
let chart, priceSeries, smaSeries;
let chartMarkers = [];
let priceHistory = [];
const SMA_WINDOW = 5;

try {
    chart = LightweightCharts.createChart(chartContainer, {
    layout: {
        background: { color: '#151924' },
        textColor: '#d1d4dc',
    },
    grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
    },
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Normal,
    },
    rightPriceScale: {
        borderColor: 'rgba(197, 203, 206, 0.8)',
    },
    timeScale: {
        borderColor: 'rgba(197, 203, 206, 0.8)',
        timeVisible: true,
        secondsVisible: true,
    },
});

    priceSeries = chart.addLineSeries({
        color: '#2962FF',
        lineWidth: 2,
    });

    smaSeries = chart.addLineSeries({
        color: '#FF9800',
        lineWidth: 2,
        lineStyle: 2,
    });

} catch (e) {
    console.error("Failed to initialize chart:", e);
    chartContainer.innerHTML = '<div class="text-red-500 p-4">Failed to load chart</div>';
}

// 3. UI Update Functions
const tradesContainer = document.getElementById('trades-container');
const signalsContainer = document.getElementById('signals-container');
const currentPriceEl = document.getElementById('current-price');
let tradeCount = 0;

function formatTime(timestampMillis) {
    const d = new Date(timestampMillis);
    return d.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' }) + 
           '.' + d.getMilliseconds().toString().padStart(3, '0');
}

function handlePayload(payload) {
    if (payload.type === 'trade') {
        const trade = payload.data;
        const price = parseFloat(trade.price).toFixed(2);
        
        // Update price text
        currentPriceEl.innerText = `$${price}`;
        currentPriceEl.className = `text-lg font-mono ${trade.is_market_maker ? 'text-sellRed' : 'text-buyGreen'}`;

        // Update chart (only for BTCUSDT to keep the chart clean)
        if (trade.symbol === 'BTCUSDT') {
            try {
                if (priceSeries) {
                    // Ensure we have a valid timestamp in seconds
                    const timeSecs = Math.floor(trade.trade_time / 1000);
                    const val = parseFloat(trade.price);
                    
                    if (isNaN(timeSecs) || isNaN(val)) {
                        console.warn("Invalid trade data for chart:", trade);
                        return;
                    }

                    // Lightweight Charts requires strictly increasing timestamps for different points.
                    // If we get multiple trades in the same second, we update the same point.
                    priceSeries.update({
                        time: timeSecs,
                        value: val
                    });

                    priceHistory.push(val);
                    if (priceHistory.length > SMA_WINDOW) {
                        priceHistory.shift();
                    }
                    
                    if (priceHistory.length === SMA_WINDOW) {
                        const sma = priceHistory.reduce((a, b) => a + b, 0) / SMA_WINDOW;
                        smaSeries.update({
                            time: timeSecs,
                            value: sma
                        });
                    }
                }
            } catch (e) {
                console.error("Error updating chart:", e);
            }
        }

        // Add to trade feed (limit to 50 items)
        const row = document.createElement('div');
        row.className = 'flex justify-between items-center py-1.5 px-2 border-b border-gray-800 text-xs font-mono flash-row';
        const isSell = trade.is_market_maker;
        row.innerHTML = `
            <span class="text-gray-500">${formatTime(trade.trade_time)}</span>
            <span class="text-white font-bold text-xs bg-gray-800 px-1 rounded">${trade.symbol.replace('USDT', '')}</span>
            <span class="${isSell ? 'text-sellRed' : 'text-buyGreen'}">$${price}</span>
            <span class="text-gray-400">${parseFloat(trade.quantity).toFixed(4)}</span>
        `;
        tradesContainer.prepend(row);
        tradeCount++;
        
        if (tradesContainer.children.length > 50) {
            tradesContainer.removeChild(tradesContainer.lastChild);
        }

    } else if (payload.type === 'signal') {
        // Remove waiting text if present
        if (signalsContainer.innerHTML.includes('Waiting for signal edge...')) {
            signalsContainer.innerHTML = '';
        }

        const sig = payload.data;
        const isBuy = sig.signal === 'BUY';
        const colorClass = isBuy ? 'bg-buyGreen text-black' : 'bg-sellRed text-white';
        const ringClass = isBuy ? 'ring-buyGreen' : 'ring-sellRed';

        const card = document.createElement('div');
        card.className = `signal-card bg-gray-900 border border-gray-700 rounded p-3 relative overflow-hidden`;
        card.innerHTML = `
            <div class="absolute top-0 right-0 py-1 px-3 text-xs font-bold ${colorClass} rounded-bl-lg shadow-sm">
                ${sig.signal}
            </div>
            <div class="text-xs text-gray-500 mb-1">${formatTime(sig.time)} &middot; ${sig.symbol}</div>
            <div class="text-lg font-mono text-white">$${parseFloat(sig.price).toFixed(2)}</div>
            <div class="text-xs font-mono text-gray-400 mt-2 flex justify-between">
                <span>SMA Pivot:</span>
                <span>$${parseFloat(sig.sma).toFixed(2)}</span>
            </div>
            <div class="mt-2 text-xs font-bold ${isBuy ? 'text-buyGreen' : 'text-sellRed'}">
                ${isBuy ? 'Price undervalued.' : 'Price overvalued.'} Executing order.
            </div>
        `;
        signalsContainer.prepend(card);
        
        if (signalsContainer.children.length > 20) {
            signalsContainer.removeChild(signalsContainer.lastChild);
        }

        if (priceSeries && sig.symbol === 'BTCUSDT') {
            chartMarkers.push({
                time: Math.floor(sig.time / 1000),
                position: isBuy ? 'belowBar' : 'aboveBar',
                color: isBuy ? '#00C853' : '#D50000',
                shape: isBuy ? 'arrowUp' : 'arrowDown',
                text: sig.signal
            });
            chartMarkers.sort((a, b) => a.time - b.time);
            priceSeries.setMarkers(chartMarkers);
        }
    }
}
