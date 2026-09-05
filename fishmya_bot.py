#!/usr/bin/env python3
"""
FishMya Game - Auto Scan + Exploit Bot (Self-Restart)
Author: GHOST
Version: 16.0 - Auto Start, Auto Restart, Continuous
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import msgpack
import ssl
import websocket
import threading

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GAME_ACCESS_TOKEN = os.environ.get("GAME_ACCESS_TOKEN", "")
WS_URL = "wss://api-fishmcloud.ugame.vn:2083"

WS_HEADERS = [
    "User-Agent: Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Origin: https://fishmya.ugame.vn",
    "Accept-Language: my-MM,my;q=0.9,en-US;q=0.8,en;q=0.7",
    "X-Requested-With: com.mytel.myid"
]

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ==================== TELEGRAM API ====================
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
last_update_id = 0
owner_chat_id = None   # ပထမဆုံး စာပို့တဲ့သူကို owner အဖြစ်သတ်မှတ်

# ==================== SCAN ROUTES (No Lucky Wheel) ====================
SCAN_ROUTES = [
    {"route": "claimItemOnline", "data": {"package": 1}, "desc": "Pkg 1"},
    {"route": "claimItemOnline", "data": {"package": 2}, "desc": "Pkg 2"},
    {"route": "claimItemOnline", "data": {"package": 3}, "desc": "Pkg 3"},
    {"route": "claimItemOnline", "data": {"package": 4}, "desc": "Pkg 4"},
    {"route": "claimItemOnline", "data": {"package": 5}, "desc": "Pkg 5"},
    {"route": "claimItemOnline", "data": {"package": 6}, "desc": "Pkg 6"},
    {"route": "claimItemOnline", "data": {"package": 7}, "desc": "Pkg 7"},
    {"route": "claimItemOnline", "data": {"package": 8}, "desc": "Pkg 8"},
    {"route": "claimItemOnline", "data": {"package": 9}, "desc": "Pkg 9"},
    {"route": "claimItemOnline", "data": {"package": 10}, "desc": "Pkg 10"},
    {"route": "claimDaily", "data": {}, "desc": "Daily"},
    {"route": "claimDailyReward", "data": {}, "desc": "Daily Reward"},
    {"route": "dailyClaim", "data": {}, "desc": "Daily Claim"},
    {"route": "claimLogin", "data": {}, "desc": "Login"},
    {"route": "loginReward", "data": {}, "desc": "Login Reward"},
    {"route": "dailyBonus", "data": {}, "desc": "Daily Bonus"},
    {"route": "checkin", "data": {}, "desc": "Check-in"},
    {"route": "dailyCheckin", "data": {}, "desc": "Daily Check-in"},
    {"route": "claimGift", "data": {}, "desc": "Gift"},
    {"route": "openGift", "data": {}, "desc": "Open Gift"},
    {"route": "receiveGift", "data": {}, "desc": "Receive Gift"},
    {"route": "giftBox", "data": {}, "desc": "Gift Box"},
    {"route": "openBox", "data": {}, "desc": "Open Box"},
    {"route": "claimBox", "data": {}, "desc": "Claim Box"},
    {"route": "claimReward", "data": {}, "desc": "Claim Reward"},
    {"route": "getReward", "data": {}, "desc": "Get Reward"},
    {"route": "receiveReward", "data": {}, "desc": "Receive Reward"},
    {"route": "claimBonus", "data": {}, "desc": "Claim Bonus"},
    {"route": "getBonus", "data": {}, "desc": "Get Bonus"},
    {"route": "bonusReward", "data": {}, "desc": "Bonus Reward"},
    {"route": "claimItem", "data": {}, "desc": "Claim Item"},
    {"route": "useItem", "data": {"type": 1}, "desc": "Use Item 1"},
    {"route": "useItem", "data": {"type": 2}, "desc": "Use Item 2"},
    {"route": "useItem", "data": {"type": 3}, "desc": "Use Item 3"},
    {"route": "useItem", "data": {"type": 4}, "desc": "Use Item 4"},
    {"route": "useItem", "data": {"type": 5}, "desc": "Use Item 5"},
    {"route": "useItem", "data": {"type": 6}, "desc": "Use Item 6"},
    {"route": "claimMission", "data": {}, "desc": "Mission"},
    {"route": "missionReward", "data": {}, "desc": "Mission Reward"},
    {"route": "completeMission", "data": {}, "desc": "Complete Mission"},
    {"route": "taskReward", "data": {}, "desc": "Task Reward"},
    {"route": "claimTask", "data": {}, "desc": "Claim Task"},
    {"route": "questReward", "data": {}, "desc": "Quest Reward"},
    {"route": "levelReward", "data": {}, "desc": "Level Reward"},
    {"route": "levelUpReward", "data": {}, "desc": "Level Up"},
    {"route": "claimLevel", "data": {}, "desc": "Claim Level"},
    {"route": "eventReward", "data": {}, "desc": "Event Reward"},
    {"route": "claimEvent", "data": {}, "desc": "Claim Event"},
    {"route": "eventBonus", "data": {}, "desc": "Event Bonus"},
    {"route": "onlineReward", "data": {}, "desc": "Online Reward"},
    {"route": "onlineBonus", "data": {}, "desc": "Online Bonus"},
    {"route": "timeReward", "data": {}, "desc": "Time Reward"},
    {"route": "hourlyReward", "data": {}, "desc": "Hourly Reward"},
    {"route": "catchFish", "data": {}, "desc": "Catch Fish"},
    {"route": "fishReward", "data": {}, "desc": "Fish Reward"},
    {"route": "claimFish", "data": {}, "desc": "Claim Fish"},
    {"route": "exchange", "data": {}, "desc": "Exchange"},
    {"route": "exchangeItem", "data": {}, "desc": "Exchange Item"},
    {"route": "convert", "data": {}, "desc": "Convert"},
    {"route": "getBalance", "data": {}, "desc": "Get Balance"},
    {"route": "refreshCash", "data": {}, "desc": "Refresh Cash"},
    {"route": "syncCash", "data": {}, "desc": "Sync Cash"},
    {"route": "updateCash", "data": {}, "desc": "Update Cash"},
    {"route": "reloadCash", "data": {}, "desc": "Reload Cash"},
]

# ==================== STATE ====================
bot_state = {
    'scanning': False,
    'exploiting': False,
    'is_running': False,       # exploit running
    'found_routes': [],
    'total_claimed': 0,
    'current_balance': 0,
    'start_balance': 0,
    'claims_done': 0,
    'total_claims': 0,
    'errors': 0,
    'last_error': 'None',
    'login_ok': False,
    'connected': False,
    'route_stats': {},
    'last_coin_time': None,
    'auto_restart_count': 0,
    'start_time': None,
}

state_lock = threading.Lock()

# ==================== UTILS ====================
def extract_coins(decoded: Dict) -> int:
    if not decoded:
        return 0
    coin_keys = ['cash', 'coin', 'coins', 'gold', 'reward', 'amount',
                 'changeCash', 'newCash', 'balance', 'bonus', 'gift',
                 'point', 'points', 'money', 'diamond', 'gem', 'totalCash']
    def search(obj, depth=0):
        if depth > 10:
            return 0
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_lower = key.lower()
                if any(k in key_lower for k in coin_keys):
                    if isinstance(value, (int, float)) and value > 0:
                        return int(value)
                    elif isinstance(value, str) and value.isdigit() and int(value) > 0:
                        return int(value)
                result = search(value, depth + 1)
                if result > 0:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = search(item, depth + 1)
                if result > 0:
                    return result
        return 0
    return search(decoded)

async def send_telegram(chat_id: str, text: str, keyboard=None):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    if keyboard:
        payload['reply_markup'] = keyboard
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=15) as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Telegram failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False

async def get_updates(offset: int = 0) -> List[Dict]:
    url = f"{TELEGRAM_API}/getUpdates"
    params = {'timeout': 30, 'offset': offset}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=35) as response:
                data = await response.json()
                if data.get('ok'):
                    return data.get('result', [])
    except:
        pass
    return []

def get_main_keyboard():
    return json.dumps({
        "inline_keyboard": [
            [{"text": "🛑 Stop", "callback_data": "stop"},
             {"text": "📊 Status", "callback_data": "status"}],
            [{"text": "💰 Balance", "callback_data": "balance"}]
        ]
    })

# ==================== CONNECT & LOGIN ====================
def connect_and_login():
    try:
        ws = websocket.create_connection(
            WS_URL,
            header=WS_HEADERS,
            sslopt={"cert_reqs": ssl.CERT_NONE},
            timeout=30
        )
        ws.send(msgpack.packb({
            "route": "mytelLogin",
            "data": {"accessToken": GAME_ACCESS_TOKEN, "language": "my"},
            "msgId": 1
        }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
        ws.settimeout(10)
        for _ in range(20):
            try:
                m = ws.recv()
                d = msgpack.unpackb(m, raw=False)
                if d.get("msgId") == 1:
                    inner = d.get("data", {})
                    if inner.get("ok"):
                        return ws, inner
                    else:
                        ws.close()
                        return None, None
            except websocket.WebSocketTimeoutException:
                continue
            except:
                break
        ws.close()
        return None, None
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return None, None

# ==================== SCAN ====================
def scan_routes():
    global bot_state
    bot_state['scanning'] = True
    bot_state['found_routes'] = []
    ws, login_data = connect_and_login()
    if not ws or not login_data:
        bot_state['scanning'] = False
        return False
    bot_state['login_ok'] = True
    bot_state['current_balance'] = login_data.get("cash", 0)
    bot_state['start_balance'] = login_data.get("cash", 0)
    ws.send(msgpack.packb({
        "route": "play",
        "data": {"roomId": 1},
        "msgId": 2
    }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
    time.sleep(1)
    msg_id = 1000
    found = []
    for route_info in SCAN_ROUTES:
        route_name = route_info['route']
        route_data = route_info['data']
        desc = route_info['desc']
        ws.send(msgpack.packb({
            "route": route_name,
            "data": route_data,
            "msgId": msg_id
        }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
        ws.settimeout(0.5)
        coins_found = 0
        try:
            while True:
                m = ws.recv()
                d = msgpack.unpackb(m, raw=False)
                if d.get("route") == "reloadCash":
                    change = d.get("data", {}).get("changeCash", 0)
                    if change > 0:
                        coins_found = change
                        break
                if d.get("msgId") == msg_id:
                    coins_found = extract_coins(d)
                    if coins_found > 0:
                        break
        except websocket.WebSocketTimeoutException:
            pass
        except:
            pass
        msg_id += 1
        if coins_found > 0:
            found_route = {'route': route_name, 'data': route_data, 'desc': desc,
                           'coins': coins_found, 'repeatable': True}
            ws.send(msgpack.packb({
                "route": route_name,
                "data": route_data,
                "msgId": msg_id
            }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
            ws.settimeout(0.5)
            repeat_coins = 0
            try:
                while True:
                    m = ws.recv()
                    d = msgpack.unpackb(m, raw=False)
                    if d.get("route") == "reloadCash":
                        change = d.get("data", {}).get("changeCash", 0)
                        if change > 0:
                            repeat_coins = change
                            break
                    if d.get("msgId") == msg_id:
                        repeat_coins = extract_coins(d)
                        if repeat_coins > 0:
                            break
            except websocket.WebSocketTimeoutException:
                pass
            except:
                pass
            msg_id += 1
            found_route['repeatable'] = repeat_coins > 0
            found.append(found_route)
            logger.info(f"✅ Found: {desc} - {coins_found} coins (Repeat: {found_route['repeatable']})")
        time.sleep(0.05)
    ws.close()
    bot_state['found_routes'] = [r for r in found if r['repeatable']]
    bot_state['scanning'] = False
    return len(bot_state['found_routes']) > 0

# ==================== EXPLOIT ====================
def exploit_loop():
    global bot_state
    if not bot_state['found_routes']:
        return
    bot_state['exploiting'] = True
    bot_state['is_running'] = True
    bot_state['total_claimed'] = 0
    bot_state['claims_done'] = 0
    bot_state['errors'] = 0
    bot_state['auto_restart_count'] = 0
    bot_state['start_time'] = datetime.now()
    bot_state['route_stats'] = {}
    for r in bot_state['found_routes']:
        bot_state['route_stats'][r['desc']] = {'sent': 0, 'received': 0, 'coins': 0}
    CLAIMS_PER_ROUTE = 150
    total_claims = len(bot_state['found_routes']) * CLAIMS_PER_ROUTE
    bot_state['total_claims'] = total_claims
    if owner_chat_id:
        asyncio.run(send_telegram(
            owner_chat_id,
            f"⚡ *Exploit Started!*\n\n"
            f"📍 Routes: {len(bot_state['found_routes'])}\n"
            f"📦 Per Route: {CLAIMS_PER_ROUTE}\n"
            f"🔢 Total: {total_claims}\n\n"
            f"💡 Use *Status* button to check progress.",
            get_main_keyboard()
        ))
    while bot_state['is_running']:
        ws, login_data = connect_and_login()
        if not ws or not login_data:
            bot_state['errors'] += 1
            bot_state['last_error'] = "Login failed"
            bot_state['connected'] = False
            logger.error("Login failed, retrying...")
            time.sleep(3)
            continue
        bot_state['login_ok'] = True
        bot_state['connected'] = True
        bot_state['current_balance'] = login_data.get("cash", bot_state['current_balance'])
        ws.send(msgpack.packb({
            "route": "play",
            "data": {"roomId": 1},
            "msgId": 2
        }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
        time.sleep(1)
        msg_id = 5000
        last_coin_time = time.time()
        try:
            for claim_index in range(CLAIMS_PER_ROUTE):
                if not bot_state['is_running']:
                    break
                for route_info in bot_state['found_routes']:
                    ws.send(msgpack.packb({
                        "route": route_info['route'],
                        "data": route_info['data'],
                        "msgId": msg_id
                    }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
                    msg_id += 1
                    with state_lock:
                        bot_state['route_stats'][route_info['desc']]['sent'] += 1
                ws.settimeout(0.5)
                try:
                    while True:
                        m = ws.recv()
                        d = msgpack.unpackb(m, raw=False)
                        route = d.get("route", "")
                        inner = d.get("data", {})
                        if route == "reloadCash":
                            change = inner.get("changeCash", 0)
                            if change > 0:
                                with state_lock:
                                    bot_state['total_claimed'] += change
                                    bot_state['current_balance'] = inner.get("newCash", bot_state['current_balance'])
                                    bot_state['claims_done'] += 1
                                    last_coin_time = time.time()
                                for ri in bot_state['found_routes']:
                                    if abs(change - ri['coins']) <= 50:
                                        with state_lock:
                                            bot_state['route_stats'][ri['desc']]['received'] += 1
                                            bot_state['route_stats'][ri['desc']]['coins'] += change
                                        break
                except websocket.WebSocketTimeoutException:
                    pass
                except:
                    pass
                if time.time() - last_coin_time > 15:
                    logger.warning("⚠️ Coins stopped! Restarting...")
                    bot_state['auto_restart_count'] += 1
                    break
                time.sleep(0.005)
        except Exception as e:
            logger.error(f"Exploit error: {e}")
            bot_state['errors'] += 1
            bot_state['last_error'] = str(e)
            bot_state['auto_restart_count'] += 1
        finally:
            ws.close()
            bot_state['connected'] = False
        if bot_state['is_running']:
            logger.info(f"🔄 Auto restart #{bot_state['auto_restart_count']}...")
            time.sleep(2)
    bot_state['exploiting'] = False

# ==================== AUTO RUN ====================
def auto_main_loop():
    """Run scan and exploit continuously with auto-restart."""
    while True:
        try:
            logger.info("🔄 Starting scan...")
            if owner_chat_id:
                asyncio.run(send_telegram(owner_chat_id, "🔍 *Auto Scan Started...*"))
            success = scan_routes()
            if success:
                logger.info("✅ Scan found routes, starting exploit...")
                exploit_loop()
            else:
                logger.warning("❌ Scan found no routes, restarting in 10s...")
                if owner_chat_id:
                    asyncio.run(send_telegram(owner_chat_id, "❌ *Scan failed - no routes found. Retrying in 10s...*"))
                time.sleep(10)
        except Exception as e:
            logger.error(f"Auto loop error: {e}")
            time.sleep(5)

# ==================== TELEGRAM HANDLERS ====================
async def process_command(chat_id: str, text: str):
    global owner_chat_id
    text = text.strip()
    if text.startswith('/start'):
        if owner_chat_id is None:
            owner_chat_id = chat_id
        await send_telegram(chat_id, "🤖 *Auto FishMya Bot*\n\nAuto scan/exploit is running.\nUse buttons to stop/check.", get_main_keyboard())
    elif text in ['/stop']:
        bot_state['is_running'] = False
        await send_telegram(chat_id, "🛑 *Stopped by user.*")
    elif text in ['/status']:
        status = "🟢 Running" if bot_state['is_running'] else "🔴 Stopped"
        text_msg = (
            f"📊 *Status*\n\n"
            f"State: {status}\n"
            f"Routes: {len(bot_state['found_routes'])}\n"
            f"Claims: {bot_state['claims_done']:,}/{bot_state['total_claims']:,}\n"
            f"💰 Balance: {bot_state['current_balance']:,}\n"
            f"📈 Gained: +{bot_state['total_claimed']:,}\n"
            f"🔄 Restarts: {bot_state['auto_restart_count']}\n"
            f"⚠️ Errors: {bot_state['errors']}"
        )
        await send_telegram(chat_id, text_msg, get_main_keyboard())
    elif text in ['/balance']:
        await send_telegram(chat_id, f"💰 Balance: {bot_state['current_balance']:,}\nGained: +{bot_state['total_claimed']:,}")

async def handle_callback(chat_id: str, data: str):
    if data == "stop":
        bot_state['is_running'] = False
        await send_telegram(chat_id, "🛑 *Stopped.*")
    elif data == "status":
        await process_command(chat_id, "/status")
    elif data == "balance":
        await process_command(chat_id, "/balance")

# ==================== MAIN ====================
async def main():
    global last_update_id, owner_chat_id
    print("Starting auto FishMya bot...")
    # Start auto scan/exploit in background thread
    threading.Thread(target=auto_main_loop, daemon=True).start()
    while True:
        try:
            updates = await get_updates(last_update_id + 1)
            for update in updates:
                if update.get('update_id', 0) > last_update_id:
                    last_update_id = update['update_id']
                if 'callback_query' in update:
                    cb = update['callback_query']
                    chat_id = str(cb.get('message', {}).get('chat', {}).get('id', ''))
                    data = cb.get('data', '')
                    if chat_id and data:
                        await handle_callback(chat_id, data)
                if 'message' in update:
                    msg = update['message']
                    chat_id = str(msg.get('chat', {}).get('id', ''))
                    text = msg.get('text', '')
                    if chat_id and text:
                        if owner_chat_id is None:
                            owner_chat_id = chat_id
                        await process_command(chat_id, text)
            await asyncio.sleep(2)
        except KeyboardInterrupt:
            bot_state['is_running'] = False
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
