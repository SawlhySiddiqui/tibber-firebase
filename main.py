import os
import json
import asyncio
import aiohttp
import tibber
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask
import threading

# ------------------------
# Flask setup (keeps Render service alive)
# ------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "Tibber-Firebase worker is running!"

# ------------------------
# Firebase setup
# ------------------------
cred_dict = json.loads(os.getenv("FIREBASE_CREDS"))
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred, {
    "databaseURL": os.getenv("FIREBASE_DB_URL")
})

# ------------------------
# Tibber callback
# ------------------------
async def _callback(pkg):
    data = pkg.get("data")
    if data is None:
        return

    live = data.get("liveMeasurement")
    if live is None:
        return

    power_prod = live.get("powerProduction")
    print("Power Production:", power_prod)

    # Push to Firebase
    ref = db.reference("/tibber/powerProduction")
    ref.set(power_prod)  # Overwrites with latest value

# ------------------------
# Tibber async loop
# ------------------------
async def run_tibber():
    async with aiohttp.ClientSession() as session:
        tibber_connection = tibber.Tibber(
            os.getenv("TIBBER_KEY"),
            websession=session
        )
        await tibber_connection.update_info()
        home = tibber_connection.get_homes()[0]

        # Subscribe to real-time data
        await home.rt_subscribe(_callback,loop=asyncio.get_event_loop())

        # Keep alive
        while True:
            await asyncio.sleep(10)

# ------------------------
# Run asyncio in separate thread
# ------------------------
def start_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_tibber())

threading.Thread(target=start_loop, daemon=True).start()

# ------------------------
# Start Flask server
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
