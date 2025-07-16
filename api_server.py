from fastapi import FastAPI
import json
import os

app = FastAPI()

DATA_FILE = "market_data.json"
ALERT_FILE = "alerts.json"

@app.get("/market-context")
def get_market_context():
    market_data = {}
    alerts = []

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            market_data = json.load(f)

    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            alerts = json.load(f)

    return {
        "BTCUSDT": market_data.get("BTCUSDT", {}),
        "ETHUSDT": market_data.get("ETHUSDT", {}),
        "SOLUSDT": market_data.get("SOLUSDT", {}),
        "TIAUSDT": market_data.get("TIAUSDT", {}),
        "alerts": alerts
    }