import os
import re
import yt_dlp
import imageio_ffmpeg
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

FFMPEG          = imageio_ffmpeg.get_ffmpeg_exe()
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
STORAGE_CHANNEL = os.environ.get("STORAGE_CHANNEL")
DOWNLOAD_DIR    = "./downloads"
CREDIT          = "👨‍💻 Developer : RH .RATUL"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_video(url, output_path):
    ydl_opts = {
    "format"             : "best[height<=480]/best[height<=360]/best",
    "outtmpl"            : f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
    "noplaylist"         : True,
    "quiet"              : True,
    "merge_output_format": "mp4",
    "cookiefile"         : COOKIES_FILE,
}"cookies.txt" if os.path.exists("cookies.txt") else None,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "android_vr", "web", "mweb"],
            }
        },
        "retries": 5,
        "fragment_retries": 5,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        fname = ydl.prepare_filename(info)
        for ext in [".webm", ".mkv"]:
            fname = fname.replace(ext, ".mp4")
        return fname, info


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
            urls.append(text[entity.offset:entity.offset + entity.length])
    for u in urls:
        if any(x in u for x in ["youtube.com", "youtu.be"]):
            return u
    return urls[0] if urls else None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *RH Ratul Video Downloader*\n\n"
        "যেকোনো YouTube লিংক পাঠান অথবা\n"
        "Notification forward করুন!\n\n"
        f"{CREDIT}",
        parse_mode="Markdown"
    )


async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    url = extract_url(message)
    if not url:
        await message.reply_text("⚠️ কোনো লিংক পাওয়া যায়নি।")
        return

    msg = await message.reply_text("⏳ *ডাউনলোড হচ্ছে...*", parse_mode="Markdown")
    uid = str(message.chat_id)
    raw = f"{DOWNLOAD_DIR}/{uid}_raw.mp4"

    try:
        filename, info = download_video(url, raw)
        title    = info.get("title", "ভিডিও")
        duration = info.get("duration", 0)
        dur_str  = f"{duration//60}:{duration%60:02d}"
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
            f"[▶️ দেখুন / ডাউনলোড করুন]({video_link})\n\n"
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
            if os.path.exists(raw):
                os.remove(raw)
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
        download_handler
    ))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
