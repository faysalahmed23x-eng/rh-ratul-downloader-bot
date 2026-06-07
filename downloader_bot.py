import os
import re
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
STORAGE_CHANNEL = os.environ.get("STORAGE_CHANNEL")
DOWNLOAD_DIR    = "./downloads"
CREDIT          = "👨‍💻 Developer : RH .RATUL"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *RH Ratul Video Downloader*\n\n"
        "যেকোনো ভিডিও লিংক পাঠান অথবা\n"
        "Notification forward করুন!\n\n"
        "✅ YouTube\n"
        "✅ Facebook\n"
        "✅ TikTok\n"
        "✅ Instagram\n\n"
        f"{CREDIT}",
        parse_mode="Markdown"
    )


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Text বা Caption থেকে content নাও
    text = ""
    if message.text:
        text = message.text.strip()
    elif message.caption:
        text = message.caption.strip()

    # Text থেকে সব link বের করো
    urls = re.findall(r'https?://[^\s\)]+', text)

    if not urls:
        await message.reply_text(
            "⚠️ কোনো লিংক পাওয়া যায়নি।\n"
            "ভিডিও লিংক বা Notification forward করুন।"
        )
        return

    # YouTube/Facebook/TikTok/Instagram link খোঁজো
    url = None
    for u in urls:
        if any(x in u for x in ["youtube.com", "youtu.be", "facebook.com", "tiktok.com", "instagram.com"]):
            url = u
            break

    if not url:
        url = urls[0]

    msg = await message.reply_text(
        "⏳ *ডাউনলোড হচ্ছে... অপেক্ষা করুন*",
        parse_mode="Markdown"
    )

    ydl_opts = {
        "format"             : "best[height<=360]/best",
        "outtmpl"            : f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "noplaylist"         : True,
        "quiet"              : True,
        "merge_output_format": "mp4",
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info     = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title    = info.get("title", "ভিডিও")
            duration = info.get("duration", 0)
            dur_str  = f"{duration//60}:{duration%60:02d}"

        size_mb = os.path.getsize(filename) / (1024 * 1024)

        await msg.edit_text(
            "📤 *আপলোড হচ্ছে... একটু অপেক্ষা করুন*",
            parse_mode="Markdown"
        )

        with open(filename, "rb") as vf:
            sent = await context.bot.send_video(
                chat_id            = STORAGE_CHANNEL,
                video              = vf,
                caption            = (
                    f"🎬 *{title}*\n"
                    f"⏱️ {dur_str} | 📺 360p | 📦 {size_mb:.1f} MB\n"
                    f"{CREDIT}"
                ),
                parse_mode         = "Markdown",
                supports_streaming = True,
            )

        video_link = f"https://t.me/c/{str(STORAGE_CHANNEL).replace('-100', '')}/{sent.message_id}"

        await msg.edit_text(
            f"✅ *ডাউনলোড সম্পন্ন!*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎬 *{title}*\n"
            f"⏱️ Duration : {dur_str}\n"
            f"📺 Quality  : 360p\n"
            f"📦 Size     : {size_mb:.1f} MB\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"[▶️ এখানে দেখুন / ডাউনলোড করুন]({video_link})\n\n"
            f"{CREDIT}",
            parse_mode="Markdown"
        )

    except Exception as e:
        await msg.edit_text(
            f"❌ *ডাউনলোড ব্যর্থ!*\n\n`{str(e)[:200]}`\n\n{CREDIT}",
            parse_mode="Markdown"
        )
    finally:
        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
        except:
            pass


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Downloader Bot চালু হয়েছে")
    print("  Developer : RH .RATUL")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
        download_video
    ))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
