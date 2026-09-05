#!/usr/bin/env python3
"""
FishMya Game - Full Auto Scan + Exploit Bot
Author: GHOST
Version: 15.0 - No Lucky Wheel + GitHub Secrets
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

# ==================== CONFIGURATION (GitHub Secrets) ====================
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
    'is_running': False,
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
    """Extract coin amount from message"""
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
    """Send Telegram message with optional keyboard"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    
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
    """Get Telegram updates"""
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
    """Get main menu keyboard"""
    return json.dumps({
        "inline_keyboard": [
            [
                {"text": "🔍 Scan", "callback_data": "scan"},
                {"text": "⚡ Exploit", "callback_data": "exploit"}
            ],
            [
                {"text": "📊 Status", "callback_data": "status"},
                {"text": "💰 Balance", "callback_data": "balance"}
            ],
            [
                {"text": "🛑 Stop", "callback_data": "stop"}
            ]
        ]
    })

def get_status_keyboard():
    """Get status keyboard"""
    return json.dumps({
        "inline_keyboard": [
            [
                {"text": "🔄 Refresh", "callback_data": "status"},
                {"text": "🛑 Stop", "callback_data": "stop"}
            ]
        ]
    })

# ==================== CONNECT & LOGIN ====================
def connect_and_login():
    """Connect and login - returns (ws, login_data)"""
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
def scan_routes(chat_id: str):
    """Scan all routes for coins"""
    global bot_state
    
    bot_state['scanning'] = True
    bot_state['found_routes'] = []
    
    asyncio.run(send_telegram(chat_id, "🔍 *Scanning routes...*"))
    
    ws, login_data = connect_and_login()
    
    if not ws or not login_data:
        bot_state['scanning'] = False
        asyncio.run(send_telegram(chat_id, "❌ *Login Failed!* Cannot scan."))
        return
    
    bot_state['login_ok'] = True
    bot_state['current_balance'] = login_data.get("cash", 0)
    bot_state['start_balance'] = login_data.get("cash", 0)
    
    # Enter room
    ws.send(msgpack.packb({
        "route": "play",
        "data": {"roomId": 1},
        "msgId": 2
    }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
    time.sleep(1)
    
    msg_id = 1000
    found = []
    
    for i, route_info in enumerate(SCAN_ROUTES):
        route_name = route_info['route']
        route_data = route_info['data']
        desc = route_info['desc']
        
        # Send test
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
            found_route = {
                'route': route_name,
                'data': route_data,
                'desc': desc,
                'coins': coins_found,
                'repeatable': True
            }
            
            # Test repeatability
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
            
            if repeat_coins > 0:
                found_route['repeatable'] = True
            else:
                found_route['repeatable'] = False
            
            found.append(found_route)
            logger.info(f"✅ Found: {desc} ({route_name}) - {coins_found} coins (Repeat: {found_route['repeatable']})")
        
        time.sleep(0.05)
    
    ws.close()
    
    bot_state['found_routes'] = [r for r in found if r['repeatable']]
    bot_state['scanning'] = False
    
    # Report
    if bot_state['found_routes']:
        report = f"✅ *Scan Complete!*\n\n"
        report += f"💰 Balance: {bot_state['current_balance']:,}\n"
        report += f"🔍 Found {len(bot_state['found_routes'])} repeatable routes:\n\n"
        
        for r in bot_state['found_routes'][:15]:
            report += f"📍 {r['desc']} - {r['coins']:,} coins\n"
        
        report += f"\n⚡ Ready to exploit! Press *Exploit* button."
        
        asyncio.run(send_telegram(chat_id, report, get_main_keyboard()))
    else:
        asyncio.run(send_telegram(chat_id, "❌ *No repeatable routes found!*", get_main_keyboard()))

# ==================== EXPLOIT ====================
def exploit_loop(chat_id: str):
    """Exploit found routes - never stops"""
    global bot_state
    
    if not bot_state['found_routes']:
        asyncio.run(send_telegram(chat_id, "❌ *No routes found!* Run Scan first."))
        return
    
    bot_state['exploiting'] = True
    bot_state['is_running'] = True
    bot_state['total_claimed'] = 0
    bot_state['claims_done'] = 0
    bot_state['errors'] = 0
    bot_state['auto_restart_count'] = 0
    bot_state['start_time'] = datetime.now()
    
    # Initialize route stats
    bot_state['route_stats'] = {}
    for r in bot_state['found_routes']:
        key = f"{r['desc']}"
        bot_state['route_stats'][key] = {'sent': 0, 'received': 0, 'coins': 0}
    
    CLAIMS_PER_ROUTE = 150
    total_claims = len(bot_state['found_routes']) * CLAIMS_PER_ROUTE
    bot_state['total_claims'] = total_claims
    
    asyncio.run(send_telegram(
        chat_id,
        f"⚡ *Exploit Started!*\n\n"
        f"📍 Routes: {len(bot_state['found_routes'])}\n"
        f"📦 Per Route: {CLAIMS_PER_ROUTE}\n"
        f"🔢 Total: {total_claims}\n\n"
        f"💡 Use *Status* button to check progress."
    ))
    
    while bot_state['is_running']:
        # Connect and login
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
        
        # Enter room
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
                
                # Send all routes in parallel
                for route_info in bot_state['found_routes']:
                    ws.send(msgpack.packb({
                        "route": route_info['route'],
                        "data": route_info['data'],
                        "msgId": msg_id
                    }, use_bin_type=True), opcode=websocket.ABNF.OPCODE_BINARY)
                    
                    msg_id += 1
                    
                    with state_lock:
                        bot_state['route_stats'][route_info['desc']]['sent'] += 1
                
                # Receive
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
                                
                                # Match route
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
                
                # Check if coins stopped
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
        
        # Auto restart
        if bot_state['is_running']:
            logger.info(f"🔄 Auto restart #{bot_state['auto_restart_count']}...")
            time.sleep(2)
    
    bot_state['exploiting'] = False
    logger.info("Exploit stopped")

# ==================== CALLBACK HANDLER ====================
async def handle_callback(chat_id: str, callback_data: str):
    """Handle button callbacks"""
    
    if callback_data == "scan":
        if bot_state['scanning']:
            await send_telegram(chat_id, "⚠️ *Already scanning!*")
            return
        
        thread = threading.Thread(target=scan_routes, args=(chat_id,), daemon=True)
        thread.start()
    
    elif callback_data == "exploit":
        if bot_state['exploiting']:
            await send_telegram(chat_id, "⚠️ *Already exploiting!*")
            return
        
        if not bot_state['found_routes']:
            await send_telegram(chat_id, "❌ *Run Scan first!*")
            return
        
        thread = threading.Thread(target=exploit_loop, args=(chat_id,), daemon=True)
        thread.start()
    
    elif callback_data == "status":
        status = "🟢 Running" if bot_state['is_running'] else "🔴 Stopped"
        scan_status = "🟢 Scanning" if bot_state['scanning'] else "✅ Done" if bot_state['found_routes'] else "❌ Not done"
        
        progress = 0
        if bot_state['total_claims'] > 0:
            progress = (bot_state['claims_done'] / bot_state['total_claims']) * 100
        
        text = (
            f"📊 *Status*\n\n"
            f"State: {status}\n"
            f"Scan: {scan_status}\n"
            f"Routes Found: {len(bot_state['found_routes'])}\n"
            f"Progress: {progress:.1f}%\n"
            f"Claims: {bot_state['claims_done']:,}/{bot_state['total_claims']:,}\n"
            f"💰 Balance: {bot_state['current_balance']:,}\n"
            f"📈 Gained: +{bot_state['total_claimed']:,}\n"
            f"🔄 Restarts: {bot_state['auto_restart_count']}\n"
            f"⚠️ Errors: {bot_state['errors']}\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        
        await send_telegram(chat_id, text, get_status_keyboard())
    
    elif callback_data == "balance":
        await send_telegram(
            chat_id,
            f"💰 *Balance*\n\n"
            f"Current: {bot_state['current_balance']:,}\n"
            f"Start: {bot_state['start_balance']:,}\n"
            f"Gained: +{bot_state['total_claimed']:,}"
        )
    
    elif callback_data == "stop":
        bot_state['is_running'] = False
        bot_state['exploiting'] = False
        bot_state['scanning'] = False
        
        await send_telegram(
            chat_id,
            f"🛑 *Stopped!*\n\n"
            f"💰 Total Gained: {bot_state['total_claimed']:,}\n"
            f"📦 Claims: {bot_state['claims_done']:,}"
        )

# ==================== COMMANDS ====================
async def process_command(chat_id: str, command: str):
    """Process text commands"""
    command = command.lower().strip()
    
    if command in ['/start', '/help', '1']:
        keyboard = get_main_keyboard()
        await send_telegram(
            chat_id,
            "🤖 *FishMya Auto Bot*\n\n"
            "1️⃣ *Scan* - Coin routes ရှာမယ်\n"
            "2️⃣ *Exploit* - တွေ့တာတွေ auto claim လုပ်မယ်\n"
            "3️⃣ *Status* - Progress ကြည့်မယ်\n"
            "4️⃣ *Balance* - Balance ကြည့်မယ်\n\n"
            "⚡ *Powered by GHOST AI*",
            keyboard
        )
    
    elif command in ['/scan', '/search']:
        await handle_callback(chat_id, "scan")
    
    elif command in ['/exploit', '/run', '/mine']:
        await handle_callback(chat_id, "exploit")
    
    elif command in ['/status', '/info']:
        await handle_callback(chat_id, "status")
    
    elif command in ['/balance', '/check']:
        await handle_callback(chat_id, "balance")
    
    elif command in ['/stop', '/end']:
        await handle_callback(chat_id, "stop")

# ==================== MAIN ====================
async def main():
    global last_update_id
    
    print("\n" + "=" * 60)
    print("🤖 FishMya Auto Scan + Exploit Bot")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Not set'}")
    print(f"🔑 Game Token: {'✅ Set' if GAME_ACCESS_TOKEN else '❌ Not set'}")
    print(f"📡 WS: {WS_URL}")
    print(f"🔍 Scan Routes: {len(SCAN_ROUTES)}")
    print("=" * 60 + "\n")
    
    if not TELEGRAM_BOT_TOKEN or not GAME_ACCESS_TOKEN:
        logger.error("❌ Tokens not set! Check GitHub Secrets.")
        return
    
    logger.info("🤖 Bot polling...")
    logger.info("💡 Send /start to begin!")
    
    while True:
        try:
            updates = await get_updates(last_update_id + 1)
            
            for update in updates:
                update_id = update.get('update_id', 0)
                
                if update_id > last_update_id:
                    last_update_id = update_id
                
                if 'callback_query' in update:
                    callback = update['callback_query']
                    chat_id = str(callback.get('message', {}).get('chat', {}).get('id', ''))
                    data = callback.get('data', '')
                    
                    if chat_id and data:
                        logger.info(f"🔘 Button: {data}")
                        await handle_callback(chat_id, data)
                
                if 'message' in update:
                    message = update['message']
                    chat_id = str(message.get('chat', {}).get('id', ''))
                    text = message.get('text', '')
                    
                    if chat_id and text:
                        logger.info(f"📩 {chat_id}: {text}")
                        await process_command(chat_id, text)
            
            await asyncio.sleep(2)
            
        except KeyboardInterrupt:
            bot_state['is_running'] = False
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
