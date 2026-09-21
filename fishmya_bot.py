#!/usr/bin/env python3
"""
FishMya Game - Fixed 1000 Requests Bot
Author: GHOST
Version: 22.0 - Fixed 1000 req, show Received/Rejected/Balance
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

# ==================== RATE CONTROL ====================
REQUESTS_PER_CYCLE = 1000        # တစ်ခါ ၁၀၀၀ ခု ပို့
SLEEP_AFTER_CYCLE = 1.0          # cycle ပြီး ၁ စက္ကန့် နား
PING_INTERVAL = 5
RECV_TIMEOUT = 0.1
RECV_WINDOW = 3.0                # 3 စက္ကန့် အတွင်း response အားလုံး ဖတ်

# ==================== TARGET ROUTE ====================
TARGET_ROUTE = {"route": "claimItemOnline", "data": {"package": 5}, "desc": "Pkg 5", "coins": 1500}

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
owner_chat_id = None

# ==================== STATE ====================
bot_state = {
    'is_running': False,
    'found_routes': [],
    'total_claimed': 0,
    'current_balance': 0,
    'start_balance': 0,
    'sent_total': 0,
    'received_total': 0,
    'rejected_total': 0,
    'timeout_total': 0,
    'cycle_count': 0,
    'errors': 0,
    'last_error': 'None',
    'auto_restart_count': 0,
    'start_time': None,
    'coins_per_second': 0,
    'current_requests_per_second': 0,
    'last_cycle': {},
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
            [{"text": "💰 Balance", "callback_data": "balance"},
             {"text": "📈 Stats", "callback_data": "stats"}]
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

        ws.settimeout(15)
        for _ in range(30):
            try:
                m = ws.recv()
                d = msgpack.unpackb(m, raw=False)
                inner = d.get("data", {})
                if not isinstance(inner, dict):
                    inner = {}
                if d.get("msgId") == 1 or d.get("route") == "mytelLogin":
                    if inner.get("ok"):
                        return ws, inner
                    else:
                        logger.error(f"Login rejected: {inner}")
                        try:
                            ws.close()
                        except:
                            pass
                        return None, None
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                logger.error(f"Login recv error: {e}")
                break
        try:
            ws.close()
        except:
            pass
        return None, None
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return None, None

# ==================== SINGLE CYCLE (1000 requests) ====================
def send_1000_requests(ws):
    """
    Send exactly 1000 requests and count:
    - received (reloadCash positive)
    - rejected (ok:false)
    - timeouts
    Returns dict with counts
    """
    logger.info(f"📤 Sending {REQUESTS_PER_CYCLE} requests...")

    sent = 0
    received = 0
    rejected = 0
    timeouts = 0
    coins_cycle = 0

    msg_id = int(time.time() * 1000) % 100000000

    # ---- Send 1000 requests ----
    for i in range(REQUESTS_PER_CYCLE):
        if not bot_state['is_running']:
            break
        try:
            ws.send(msgpack.packb({
                "route": TARGET_ROUTE['route'],
                "data": TARGET_ROUTE['data'],
                "msgId": msg_id
            }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
            sent += 1
            msg_id += 1
        except Exception as e:
            logger.error(f"Send error at #{i}: {e}")
            break
        # small delay to avoid local buffer overflow
        if i % 100 == 99:
            time.sleep(0.01)

    logger.info(f"✅ Sent {sent}/{REQUESTS_PER_CYCLE}. Reading responses for {RECV_WINDOW}s...")

    # ---- Read responses for RECV_WINDOW seconds ----
    ws.settimeout(RECV_TIMEOUT)
    recv_end = time.time() + RECV_WINDOW

    while time.time() < recv_end:
        try:
            m = ws.recv()
            if not m:
                continue
            d = msgpack.unpackb(m, raw=False)
            route = d.get("route", "")
            inner = d.get("data", {})

            if route == "reloadCash":
                change = inner.get("changeCash", 0)
                if change > 0:
                    received += 1
                    coins_cycle += change
                    with state_lock:
                        bot_state['total_claimed'] += change
                        bot_state['current_balance'] = inner.get("newCash", bot_state['current_balance'])

            elif inner.get("ok") is False:
                rejected += 1

        except websocket.WebSocketTimeoutException:
            timeouts += 1
            continue
        except ssl.SSLError as e:
            logger.error(f"SSL error: {e}")
            break
        except Exception as e:
            logger.error(f"Recv error: {e}")
            break

    result = {
        'sent': sent,
        'received': received,
        'rejected': rejected,
        'timeouts': timeouts,
        'coins': coins_cycle,
        'time': datetime.now().strftime('%H:%M:%S'),
    }

    with state_lock:
        bot_state['sent_total'] += sent
        bot_state['received_total'] += received
        bot_state['rejected_total'] += rejected
        bot_state['timeout_total'] += timeouts
        bot_state['cycle_count'] += 1
        bot_state['last_cycle'] = result

    logger.info(
        f"📊 CYCLE #{bot_state['cycle_count']} | "
        f"Sent: {sent} | ✅ Received: {received} | "
        f"❌ Rejected: {rejected} | ⏰ Timeouts: {timeouts} | "
        f"💰 Coins: {coins_cycle:,}"
    )

    return result


# ==================== EXPLOIT LOOP ====================
def exploit_loop():
    global bot_state
    if not bot_state['found_routes']:
        return

    bot_state['is_running'] = True
    bot_state['start_time'] = datetime.now()

    retry_delay = 5
    while bot_state['is_running']:
        ws, login_data = connect_and_login()
        if not ws or not login_data:
            bot_state['errors'] += 1
            bot_state['last_error'] = "Login failed"
            logger.error(f"Login failed, retry in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay + 5, 30)
            continue
        else:
            retry_delay = 5

        bot_state['current_balance'] = login_data.get("cash", bot_state['current_balance'])
        if bot_state['start_balance'] == 0:
            bot_state['start_balance'] = bot_state['current_balance']

        try:
            ws.send(msgpack.packb({
                "route": "play",
                "data": {"roomId": 1},
                "msgId": 2
            }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
        except:
            pass
        time.sleep(1)

        if owner_chat_id:
            asyncio.run(send_telegram(
                owner_chat_id,
                f"⚡ *Bot Started!*\n\n"
                f"🎯 Target: Pkg 5 (1500 coins/claim)\n"
                f"📤 Rate: {REQUESTS_PER_CYCLE} requests per cycle\n"
                f"⏱️ Cycle: {REQUESTS_PER_CYCLE} req + {SLEEP_AFTER_CYCLE}s sleep\n\n"
                f"💡 Use *Status* button."
            ))

        last_ping_time = time.time()
        connection_broken = False

        try:
            while bot_state['is_running'] and not connection_broken:
                # ---- Ping ----
                if time.time() - last_ping_time >= PING_INTERVAL:
                    try:
                        ws.send(msgpack.packb({
                            "route": "ping",
                            "data": {},
                            "msgId": 0
                        }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
                        last_ping_time = time.time()
                    except:
                        pass

                # ---- Send 1000 requests + receive ----
                cycle_start = time.time()
                try:
                    send_1000_requests(ws)
                except Exception as e:
                    logger.error(f"Cycle error: {e}")
                    connection_broken = True
                    break

                cycle_elapsed = time.time() - cycle_start
                if cycle_elapsed > 0:
                    rps = REQUESTS_PER_CYCLE / cycle_elapsed
                    with state_lock:
                        bot_state['current_requests_per_second'] = rps

                # ---- Sleep after cycle ----
                time.sleep(SLEEP_AFTER_CYCLE)

        except Exception as e:
            logger.error(f"Exploit error: {e}")
            bot_state['errors'] += 1
            bot_state['last_error'] = str(e)
            bot_state['auto_restart_count'] += 1
        finally:
            try:
                ws.close()
            except Exception:
                pass

        if bot_state['is_running']:
            logger.info(f"🔄 Auto restart #{bot_state['auto_restart_count']}...")
            time.sleep(8)

    logger.info("Exploit stopped")

# ==================== AUTO MAIN LOOP ====================
def auto_main_loop():
    while True:
        try:
            logger.info("🔄 Starting bot...")
            bot_state['found_routes'] = [TARGET_ROUTE]
            bot_state['best_route'] = TARGET_ROUTE
            exploit_loop()
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
        status_text = (
            "🤖 *FishMya 1000-Req Bot*\n\n"
            f"🎯 Target: Pkg 5 (1500 coins/claim)\n"
            f"📤 Rate: {REQUESTS_PER_CYCLE} req/cycle\n\n"
            f"💰 Balance: {bot_state.get('current_balance', 0):,}\n"
            f"📈 Gained: +{bot_state.get('total_claimed', 0):,}\n"
            f"📤 Sent: {bot_state.get('sent_total', 0):,}\n"
            f"✅ Received: {bot_state.get('received_total', 0):,}\n"
            f"❌ Rejected: {bot_state.get('rejected_total', 0):,}\n\n"
            "Use buttons to control."
        )
        await send_telegram(chat_id, status_text, get_main_keyboard())
    elif text in ['/stop']:
        bot_state['is_running'] = False
        await send_telegram(chat_id, "🛑 *Stopped by user.*")
    elif text in ['/status']:
        status = "🟢 Running" if bot_state['is_running'] else "🔴 Stopped"
        elapsed = (datetime.now() - bot_state['start_time']).seconds if bot_state['start_time'] else 0
        lc = bot_state.get('last_cycle', {}) or {}
        text_msg = (
            f"📊 *Status*\n\n"
            f"State: {status}\n"
            f"⏱️ Elapsed: {elapsed}s\n"
            f"🔁 Cycles: {bot_state.get('cycle_count', 0):,}\n\n"
            f"💰 *Balance:* {bot_state.get('current_balance', 0):,}\n"
            f"📈 *Gained:* +{bot_state.get('total_claimed', 0):,}\n\n"
            f"📤 *Sent Total:* {bot_state.get('sent_total', 0):,}\n"
            f"✅ *Received Total:* {bot_state.get('received_total', 0):,}\n"
            f"❌ *Rejected Total:* {bot_state.get('rejected_total', 0):,}\n"
            f"⏰ *Timeouts:* {bot_state.get('timeout_total', 0):,}\n\n"
            f"*Last Cycle:*\n"
            f"  Sent: {lc.get('sent', 0)} | Recv: {lc.get('received', 0)} | Rej: {lc.get('rejected', 0)}\n"
            f"  Coins: {lc.get('coins', 0):,}\n\n"
            f"🚀 RPS: {int(bot_state.get('current_requests_per_second', 0))}\n"
            f"🔄 Restarts: {bot_state.get('auto_restart_count', 0)}"
        )
        await send_telegram(chat_id, text_msg, get_main_keyboard())
    elif text in ['/balance']:
        await send_telegram(
            chat_id,
            f"💰 *Balance*\n\n"
            f"Current: {bot_state.get('current_balance', 0):,}\n"
            f"Start: {bot_state.get('start_balance', 0):,}\n"
            f"Gained: +{bot_state.get('total_claimed', 0):,}"
        )
    elif text in ['/stats']:
        lc = bot_state.get('last_cycle', {}) or {}
        stats_text = "📊 *Detailed Stats*\n\n"
        stats_text += f"🎯 Target: Pkg 5 (1500/claim)\n"
        stats_text += f"📤 Rate: {REQUESTS_PER_CYCLE} req/cycle\n\n"
        stats_text += f"🔁 Cycles: {bot_state.get('cycle_count', 0):,}\n"
        stats_text += f"📤 Sent: {bot_state.get('sent_total', 0):,}\n"
        stats_text += f"✅ Received: {bot_state.get('received_total', 0):,}\n"
        stats_text += f"❌ Rejected: {bot_state.get('rejected_total', 0):,}\n"
        stats_text += f"⏰ Timeouts: {bot_state.get('timeout_total', 0):,}\n\n"
        stats_text += f"💰 Balance: {bot_state.get('current_balance', 0):,}\n"
        stats_text += f"📈 Gained: +{bot_state.get('total_claimed', 0):,}\n\n"
        stats_text += f"*Last Cycle:*\n"
        stats_text += f"  {lc.get('time', '')}\n"
        stats_text += f"  Sent: {lc.get('sent', 0)}\n"
        stats_text += f"  Recv: {lc.get('received', 0)}\n"
        stats_text += f"  Rej: {lc.get('rejected', 0)}\n"
        stats_text += f"  Timeout: {lc.get('timeouts', 0)}\n"
        stats_text += f"  Coins: {lc.get('coins', 0):,}\n"
        await send_telegram(chat_id, stats_text, get_main_keyboard())

async def handle_callback(chat_id: str, data: str):
    if data == "stop":
        bot_state['is_running'] = False
        await send_telegram(chat_id, "🛑 *Stopped.*")
    elif data == "status":
        await process_command(chat_id, "/status")
    elif data == "balance":
        await process_command(chat_id, "/balance")
    elif data == "stats":
        await process_command(chat_id, "/stats")

# ==================== MAIN ====================
async def main():
    global last_update_id, owner_chat_id
    print("Starting FishMya 1000-Req Bot...")
    threading.Thread(target=auto_main_loop, daemon=True).start()
    while True:
        try:
            updates = await get_updates(last_update_id + 1)
            for update in updates:
                if not isinstance(update, dict):
                    continue
                update_id = update.get('update_id', 0)
                if update_id > last_update_id:
                    last_update_id = update_id

                cb = update.get('callback_query')
                if isinstance(cb, dict):
                    msg = cb.get('message') or {}
                    chat = msg.get('chat') or {}
                    chat_id = str(chat.get('id', ''))
                    data = cb.get('data', '')
                    if chat_id and data:
                        await handle_callback(chat_id, data)
                    continue

                msg = update.get('message')
                if isinstance(msg, dict):
                    chat = msg.get('chat') or {}
                    chat_id = str(chat.get('id', ''))
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
