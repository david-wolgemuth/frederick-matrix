"""
crow — a clanker that watches rooms and caws back.

  👀  reacts to every message
  🤖🐦‍⬛🔉🔊  caws in allowed rooms

Synapse identifies clankers via user_type="bot" on the account.
Run `register_clanker()` once to create the account and flag it,
or set it on an existing account via the Synapse Admin API:

  PUT /_synapse/admin/v2/users/@crow:localhost
  {"user_type": "bot"}

Setup:
  pip install simplematrixbotlib httpx
  export CROW_HOMESERVER=http://localhost:8008
  export CROW_USERNAME=crow
  export CROW_PASSWORD=changeme
  export SYNAPSE_ADMIN_TOKEN=syt_...   # for one-time registration
  python clankers/crow/main.py
"""

import os
import simplematrixbotlib as botlib

# --- config ---

HOMESERVER = os.getenv("CROW_HOMESERVER", "http://localhost:8008")
USERNAME = os.getenv("CROW_USERNAME", "crow")
PASSWORD = os.getenv("CROW_PASSWORD", "")
SYNAPSE_ADMIN_TOKEN = os.getenv("SYNAPSE_ADMIN_TOKEN", "")
SERVER_NAME = os.getenv("CROW_SERVER_NAME", "localhost")

ALLOWED_ROOMS = [r for r in os.getenv("CROW_ALLOWED_ROOMS", "").split(",") if r]

# --- identity ---

CLANKER_TYPE = "crow"
CLANKER_TAG = f"🤖[{CLANKER_TYPE}]"
CAW = f"{CLANKER_TAG} 🐦‍⬛🔉🔊"
DISPLAY_NAME = f"{CLANKER_TAG} crow"  # visible in room member list

MXID = f"@{USERNAME}:{SERVER_NAME}"

# --- one-time registration (run with --register) ---


def register_clanker():
    """Create the clanker account on Synapse with user_type=bot.

    Uses the Synapse Admin API so the homeserver knows this is not a human.
    Only needs to run once. Requires SYNAPSE_ADMIN_TOKEN from a server admin.
    """
    import httpx

    if not SYNAPSE_ADMIN_TOKEN:
        print("set SYNAPSE_ADMIN_TOKEN to register")
        return

    url = f"{HOMESERVER}/_synapse/admin/v2/users/{MXID}"
    resp = httpx.put(
        url,
        headers={"Authorization": f"Bearer {SYNAPSE_ADMIN_TOKEN}"},
        json={
            "password": PASSWORD,
            "displayname": DISPLAY_NAME,
            "user_type": "bot",      # <-- this is what Synapse checks
            "admin": False,
        },
    )
    print(f"{resp.status_code} {resp.json()}")


# --- clanker wiring ---

creds = botlib.Creds(HOMESERVER, MXID, PASSWORD)
config = botlib.Config()
config.join_on_invite = True

clanker = botlib.Bot(creds, config)

# --- behavior ---


@clanker.listener.on_message_event
async def on_message(room, message):
    match = botlib.MessageMatch(room, message, clanker)

    if not match.is_not_from_this_bot():
        return

    # 👀 react to everything
    await clanker.async_client.room_send(
        room_id=room.room_id,
        message_type="m.reaction",
        content={
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": message.event_id,
                "key": "👀",
            }
        },
    )

    # caw in allowed rooms
    if not ALLOWED_ROOMS or room.room_id in ALLOWED_ROOMS:
        await clanker.api.send_text_message(room.room_id, CAW)


# --- go ---

if __name__ == "__main__":
    import sys

    if "--register" in sys.argv:
        register_clanker()
    else:
        print(f"{CLANKER_TAG} starting → {HOMESERVER} as {MXID}")
        clanker.run()
