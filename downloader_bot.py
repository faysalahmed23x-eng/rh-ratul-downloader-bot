import os
import re
from pytubefix import YouTube
from pytubefix.cli import on_progress
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
        "যেকোনো YouTube লিংক পাঠান অথবা\n"
        "Notification forward করুন!\n\n"
        "✅ YouTube\n\n"
        f"{CREDIT}",
        parse_mode="Markdown"
    )


def extract_url(message):
    urls = []
    text = message.text or message.caption or ""
    found = re.findall(r'https?://[^\s\)]+', text)
    urls.extend(found)

    entities = message.entities or message.caption_entities or []
    for entity in entities:
        if entity.type == "text_link":
            urls.append(entity.url)
        elif entity.type == "url":
            start = entity.offset
            end   = entity.offset + entity.length
            urls.append(text[start:end])

    for u in urls:
        if any(x in u for x in ["youtube.com", "youtu.be"]):
            return u

    return urls[0] if urls else None


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    url = extract_url(message)

    if not url:
        await message.reply_text("⚠️ কোনো লিংক পাওয়া যায়নি।")
        return

    msg = await message.reply_text("⏳ *ডাউনলোড হচ্ছে...*", parse_mode="Markdown")

    filename = None
    try:
        yt = YouTube(url, on_progress_callback=on_progress, use_oauth=False, allow_oauth_cache=True)
        
        # 360p stream খোঁজো
        stream = yt.streams.filter(
            progressive=True,
            file_extension="mp4",
            res="360p"
        ).first()
        
        if not stream:
            stream = yt.streams.filter(
                progressive=True,
                file_extension="mp4"
            ).order_by("resolution").first()

        title    = yt.title
        duration = yt.length
        dur_str  = f"{duration//60}:{duration%60:02d}"

        filename = stream.download(output_path=DOWNLOAD_DIR)
        size_mb  = os.path.getsize(filename) / (1024 * 1024)

        await msg.edit_text("📤 *আপলোড হচ্ছে...*", parse_mode="Markdown")

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
