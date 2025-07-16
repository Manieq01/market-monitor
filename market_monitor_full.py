import requests
import json
import os
import time
import datetime
from pytz import timezone
from colorama import Fore, Style
import threading

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "TIAUSDT"]
TIMEFRAMES = {
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440
}
LOCAL_TIMEZONE = timezone("Europe/Warsaw")
DATA_FILE = "market_data.json"
ALERT_FILE = "alerts.json"

def should_trigger_timeframe(tf_minutes, now_utc):
    local_time = now_utc.astimezone(LOCAL_TIMEZONE)
    minutes = local_time.minute
    hour = local_time.hour
    second = local_time.second

    # Umożliwiamy 15 sekund marginesu czasu
    if second > 15:
        return False

    # === D1 ===
    if tf_minutes == 1440:
        return hour == 2 and minutes == 0
    if tf_minutes == 240:
        return hour % 4 == 2 and minutes == 0
    return (hour * 60 + minutes) % tf_minutes == 0

def load_alerts():
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            return json.load(f)
    return []

def save_alert(message):
    alerts = load_alerts()
    alerts.append(message)
    with open(ALERT_FILE, "w") as f:
        json.dump(alerts[-100:], f, indent=2)

def send_alert(message):
    print(Fore.YELLOW + "🔔 ALERT:", message, Style.RESET_ALL)
    save_alert(message)

def fetch_market_data(symbol):
    url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={symbol}"
    try:
        response = requests.get(url)
        data = response.json()
        return {
            "price": float(data["lastPrice"]),
            "change24h": float(data["priceChangePercent"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"]),
            "volume": float(data["volume"])
        }
    except:
        return None

def load_existing_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_market_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def monitor_timeframes():
    market_data = load_existing_data()
    while True:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        updated = False

        for tf_name, tf_minutes in TIMEFRAMES.items():
            if not should_trigger_timeframe(tf_minutes, now_utc):
                continue

            timestamp = now_utc.astimezone(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n=== [{timestamp}] Świeca zamknięta: {tf_name} ===")

            for symbol in SYMBOLS:
                data = fetch_market_data(symbol)
                if data:
                    market_data.setdefault(symbol, {})[tf_name] = data
                    print(f"{symbol} ({tf_name}): Cena={data['price']}, Zmiana={data['change24h']}%, "
                          f"High={data['high']}, Low={data['low']}, Wolumen={data['volume']}")

                    if tf_name in ["H4", "D1"] and abs(data["change24h"]) > 2:
                        alert_msg = f"{symbol} ({tf_name}): zmiana 24h wynosi {data['change24h']}% ({timestamp})"
                        send_alert(alert_msg)

                    updated = True

        if updated:
            save_market_data(market_data)

        time.sleep(15)

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_timeframes)
    monitor_thread.start()