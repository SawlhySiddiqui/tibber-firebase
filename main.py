
import asyncio
import aiohttp
import tibber
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase (run once)
cred = credentials.Certificate("tibber-live-data-2efea-firebase-adminsdk-fbsvc-d10c5be4f1.json")  # Path to your service account key
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://tibber-live-data-2efea-default-rtdb.firebaseio.com/"  # Replace with your Firebase DB URL
})

def _callback(pkg):
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

async def run():
    async with aiohttp.ClientSession() as session:
        tibber_connection = tibber.Tibber(
            "25B2F7202370B81FB74584E153E092913648E942F5E10D8F11E09B4F3C5D6AFE-1",
            websession=session,
            user_agent="my_app/1.0"
        )
        await tibber_connection.update_info()

        home = tibber_connection.get_homes()[0]

        # Subscribe to real-time data
        await home.rt_subscribe(_callback)

        # Keep alive
        while True:
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run())


