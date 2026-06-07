import os
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
        "যেকোনো YouTube লিংক পাঠান।\n"
        "360p তে download করে দেব!\n\n"
        "✅ YouTube\n"
        "✅ Facebook\n"
        "✅ TikTok\n"
        "✅ Instagram\n\n"
        f"{CREDIT}",
        parse_mode="Markdown"
    )


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("⚠️ সঠিক লিংক পাঠান।")
        return

    msg = await update.message.reply_text(
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

        os.remove(filename)

    except Exception as e:
        await msg.edit_text(
            f"❌ *ডাউনলোড ব্যর্থ!*\n\n`{str(e)[:200]}`\n\n{CREDIT}",
            parse_mode="Markdown"
        )
        try:
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
