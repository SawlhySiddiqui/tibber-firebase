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
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": os.getenv("FIREBASE_DB_URL")
    })
    print("Firebase initialized successfully.")
except Exception as e:
    print("Firebase initialization error:", e)

# ------------------------
# Tibber callback
# ------------------------
async def _callback(pkg):
    data = pkg.get("data")
    if not data:
        return

    live = data.get("liveMeasurement")
    if not live:
        return

    power_prod = live.get("powerProduction")
    print("Power Production:", power_prod)

    # Push to Firebase with error handling
    try:
        db.reference("/tibber/powerProduction").set(power_prod)
    except Exception as e:
        print("Firebase push error:", e)

# ------------------------
# Tibber async loop
# ------------------------
# ///copilot update this code///
async def run_tibber():
    async with aiohttp.ClientSession() as session:
        tibber_connection = tibber.Tibber(
            access_token=os.getenv("TIBBER_KEY"),
            websession=session
        )

        try:
            await tibber_connection.update_info()
            home = tibber_connection.get_homes()[0]

            # Subscribe to realtime data using async generator
            print("Subscribing to Tibber RT data...")
            async for measurement in home.rt_subscription():
                power_prod = measurement.get("powerProduction")
                print("Power Production:", power_prod)
                # Push to Firebase with error handling
                try:
                    db.reference("/tibber/powerProduction").set(power_prod)
                except Exception as e:
                    print("Firebase push error:", e)

        except Exception as e:
            print("Tibber connection error:", e)

# async def run_tibber():
#     async with aiohttp.ClientSession() as session:
#         tibber_connection = tibber.Tibber(
#             access_token=os.getenv("TIBBER_KEY"),
#             websession=session
#         )

#         try:
#             await tibber_connection.update_info()
#             home = tibber_connection.get_homes()[0]
           


#             # Subscribe to realtime data
#             print("Subscribing to Tibber RT data...")
#             await home.rt_subscribe(callback=_callback)
#             print("Subscribed successfully.")
#             # Keep alive
#             while True:
#                 await asyncio.sleep(10)

#         except Exception as e:
#             print("Tibber connection error:", e)

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
