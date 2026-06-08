import os
import re
import math
import subprocess
import yt_dlp
import imageio_ffmpeg
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN")
STORAGE_CHANNEL = os.environ.get("STORAGE_CHANNEL")
DOWNLOAD_DIR    = "./downloads"
COOKIES_FILE    = "cookies.txt"
CREDIT          = "👨‍💻 Developer : RH .RATUL"
MAX_FILE_MB     = 1900
FFMPEG          = imageio_ffmpeg.get_ffmpeg_exe()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_video(url, output_path):
    ydl_opts = {
        "format"             : "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[height<=360]/best",
        "outtmpl"            : output_path,
        "merge_output_format": "mp4",
        "ffmpeg_location"    : FFMPEG,
        "quiet"              : True,
        "no_warnings"        : True,
        "geo_bypass"         : True,
        "geo_bypass_country" : "BD",
        "cookiefile"         : COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "http_headers"       : {
            "User-Agent"     : "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "extractor_args"     : {
            "youtube": {
                "player_client": ["android", "android_vr", "web", "mweb"],
            }
        },
        "retries"            : 5,
        "fragment_retries"   : 5,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info  = ydl.extract_info(url, download=True)
        fname = ydl.prepare_filename(info)
        for ext in [".webm", ".mkv"]:
            fname = fname.replace(ext, ".mp4")
        return fname, info


def get_duration(path):
    result = subprocess.run([FFMPEG, '-i', path], capture_output=True, text=True)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', result.stderr)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    return 0


def split_video(inp, max_mb=MAX_FILE_MB):
    size_mb = os.path.getsize(inp) / (1024 * 1024)
    if size_mb <= max_mb:
        return [inp]
    total = get_duration(inp)
    n     = math.ceil(size_mb / max_mb)
    part_dur = total / n
    parts = []
    base  = inp.replace('.mp4', '')
    for i in range(n):
        p = f"{base}_part{i+1}.mp4"
        subprocess.run([
            FFMPEG, '-i', inp,
            '-ss', str(i * part_dur),
            '-t', str(part_dur),
            '-c', 'copy', '-y', p
        ], capture_output=True)
        if os.path.exists(p):
            parts.append(p)
    return parts if parts else [inp]


def cleanup(*paths):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except:
            pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *RH Ratul Video Downloader*\n\n"
        "যেকোনো ভিডিও লিংক পাঠান অথবা\n"
        "Notification forward করুন!\n\n"
        "✅ YouTube\n"
        "✅ Full Episode\n"
        "✅ 2GB পর্যন্ত\n\n"
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


async def download_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        await msg.edit_text("📦 *প্রস্তুত করছি...*", parse_mode="Markdown")
        parts = split_video(filename)
        total = len(parts)

        for i, part in enumerate(parts, 1):
            await msg.edit_text(
                f"📤 *আপলোড হচ্ছে... Part {i}/{total}*",
                parse_mode="Markdown"
            )
            with open(part, "rb") as vf:
                sent = await context.bot.send_video(
                    chat_id            = STORAGE_CHANNEL,
                    video              = vf,
                    caption            = (
                        f"🎬 *{title}*\n"
                        f"⏱️ {dur_str} | 📺 360p | 📦 {size_mb:.1f} MB\n"
                        f"Part {i}/{total}\n"
                        f"{CREDIT}"
                    ),
                    parse_mode         = "Markdown",
                    supports_streaming = True,
                )

            video_link = f"https://t.me/c/{str(STORAGE_CHANNEL).replace('-100', '')}/{sent.message_id}"

            await message.reply_text(
                f"✅ *Part {i}/{total} সম্পন্ন!*\n"
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

        await msg.delete()

    except Exception as e:
        err = str(e)
        if "Requested format is not available" in err:
            await msg.edit_text(
                f"❌ *Format পাওয়া যাচ্ছে না!*\n\nকিছুক্ষণ পরে আবার চেষ্টা করুন।\n\n{CREDIT}",
                parse_mode="Markdown"
            )
        else:
            await msg.edit_text(
                f"❌ *ডাউনলোড ব্যর্থ!*\n\n`{err[:200]}`\n\n{CREDIT}",
                parse_mode="Markdown"
            )
    finally:
        cleanup(raw)
        for part in split_video.__globals__.get('_parts', []):
            cleanup(part)


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Downloader Bot চালু হয়েছে")
    print("  Developer : RH .RATUL")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
        download_video_handler
    ))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
