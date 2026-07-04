import os
import asyncio
import logging
from datetime import datetime
import telebot
from telebot import types
import edge_tts
import gc

# ---------------------------------------------------------
# 1. Configuration & Logging
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8823305920:AAE003tEmGC5nN9qqpTX0ueD-GY3SQPH4bQ")

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)

# ---------------------------------------------------------
# 2. TTS Settings
# ---------------------------------------------------------
VOICE = "my-MM-ThihaNeural"
VOICE_RATE = "+40%"
VOICE_VOLUME = "+0%"
VOICE_PITCH = "+0Hz"

async def convert_text_to_mp3(text: str, output_filename: str) -> None:
    communicate = edge_tts.Communicate(
        text,
        VOICE,
        rate=VOICE_RATE,
        volume=VOICE_VOLUME,
        pitch=VOICE_PITCH
    )
    await communicate.save(output_filename)

# ---------------------------------------------------------
# 3. Bot Handlers
# ---------------------------------------------------------

def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_start = types.KeyboardButton("🎙 စာသားကို အသံပြောင်းမည်")
    btn_help = types.KeyboardButton("❓ အကူအညီ")
    markup.add(btn_start, btn_help)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🎬 *Movie Recap Free TTS Bot (1.4x Pro)* မှ ကြိုဆိုပါတယ်!\n\n"
        "စာသား (Script) များကို ပို့ပေးပါ။ ကြည်လင်ပြတ်သားသော မြန်မာ AI အသံဖိုင် (.mp3) "
        "အမြန်နှုန်း *1.4x* ဖြင့် အခမဲ့ ပြောင်းလဲပေးသွားပါ့မယ်။\n\n"
        "💡 _အကြံပြုချက်: ပုဒ်ဖြတ်ပုဒ်ရပ် (၊ ။) များ သေချာထည့်ပေးခြင်းက အသံကို ပိုမိုပီသစေပါသည်။_"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "🎙 စာသားကို အသံပြောင်းမည်")
def prompt_for_text(message):
    bot.send_message(message.chat.id, "📝 အသံပြောင်းလိုသော စာသားများကို ရိုက်ထည့်ပြီး ပို့ပေးပါ။")

@bot.message_handler(func=lambda message: message.text == "❓ အကူအညီ")
def send_help(message):
    help_text = (
        "❓ *အကူအညီ*\n\n"
        "ဤ Bot သည် သင်ပို့သော မြန်မာစာသားများကို ကြည်လင်ပြတ်သားသော AI အသံဖိုင် (1.4x မြန်နှုန်း) အဖြစ် ပြောင်းလဲပေးပါသည်။\n\n"
        "*အသုံးပြုပုံ:*\n"
        "1️⃣ 🎙 စာသားကို အသံပြောင်းမည် ခလုတ်ကို နှိပ်ပါ။\n"
        "2️⃣ စာသားများကို ရိုက်ထည့်ပြီး ပို့ပါ။\n"
        "3️⃣ ခဏအကြာတွင် အသံဖိုင်ကို ပြန်လည်ရရှိပါမည်။\n\n"
        "_မှတ်ချက်: ပုဒ်ဖြတ်ပုဒ်ရပ်များ သေချာထည့်သွင်းပေးခြင်းဖြင့် အသံထွက် ပိုမိုကောင်းမွန်စေပါသည်။_"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    chat_id = message.chat.id

    if text in ["🎙 စာသားကို အသံပြောင်းမည်", "❓ အကူအညီ"]:
        return

    if not text or text.strip() == "":
        bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ အသံပြောင်းလိုသော စာသားများကို ပို့ပေးပါ။")
        return

    status_msg = bot.send_message(
        chat_id,
        "⏳ *1.4x အမြန်နှုန်းဖြင့် အသံဖိုင် ဖန်တီးနေပါသည်...*",
        parse_mode="Markdown"
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"recap_{chat_id}_{timestamp}.mp3"

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(convert_text_to_mp3(text, output_file))
        loop.close()

        with open(output_file, 'rb') as audio:
            caption_text = (
                "🎧 *အသံဖိုင် အဆင်သင့်ဖြစ်ပါပြီ!*\n"
                "⏱ မြန်နှုန်း: 1.4x | 🎙 Thiha Neural"
            )
            bot.send_audio(
                chat_id,
                audio,
                caption=caption_text,
                parse_mode="Markdown",
                title=f"Recap_1.4x_{timestamp}",
                performer="AI Voice Bot"
            )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        bot.send_message(chat_id, "❌ အသံဖိုင်ပြောင်းလဲရာတွင် အမှားအယွင်းရှိနေပါသည်။")

    finally:
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception:
                pass
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass
        gc.collect()

# ---------------------------------------------------------
# 4. Main Execution
# ---------------------------------------------------------
if __name__ == "__main__":
    bot.infinity_polling(none_stop=True, timeout=60, long_polling_timeout=60)
