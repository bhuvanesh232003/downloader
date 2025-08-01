# Copyright (c) 2025
# This bot is for educational purposes only.
# Downloaded content belongs to its respective copyright holders.

import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Load .env file for BOT_TOKEN
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in the environment or .env file.")

# Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Constants
MAX_FILE_SIZE = 49 * 1024 * 1024  # Telegram file limit
COOKIE_FILE = "cookies.txt"
DOWNLOAD_DIR = "downloads"

COPYRIGHT_NOTICE = (
    "*Copyright Disclaimer*\n\n"
    "This bot is for educational purposes only.\n"
    "Downloaded content belongs to its respective copyright holders.\n"
    "Please respect copyright laws and the terms of service of content providers."
)

def download_hook(msg):
    if msg.get('status') == 'downloading':
        percent = msg.get('_percent_str', '').strip()
        if percent:
            print(f"Download Progress: {percent}")

# === Main download function ===
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("❌ Please send a valid video URL.")
        return

    await update.message.reply_markdown(COPYRIGHT_NOTICE)
    status_msg = await update.message.reply_text("⏳ Processing your request...")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    ydl_opts = {
        'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best',
        'noplaylist': True,
        'progress_hooks': [download_hook],
        'outtmpl': f'{DOWNLOAD_DIR}/%(title).50s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            filename = ydl.prepare_filename(info)
            filesize = info.get('filesize') or info.get('filesize_approx') or 0

            if filesize > MAX_FILE_SIZE:
                await status_msg.edit_text("⚠️ The video is too large for Telegram (50MB limit).")
                return

            await status_msg.edit_text("⬇️ Downloading...")
            ydl.download([url])

            if not os.path.exists(filename):
                await status_msg.edit_text("❌ Download failed: File not found.")
                return

            await status_msg.edit_text("📤 Uploading...")
            with open(filename, 'rb') as f:
                await update.message.reply_video(f, caption=title)

            await status_msg.delete()
            os.remove(filename)

    except Exception as e:
        error_message = str(e)
        if "cookies" in error_message.lower():
            await status_msg.edit_text(
                "⚠️ Login required or rate-limit reached.\n"
                "Please upload a valid `cookies.txt` file from your browser session.\n\n"
                "See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
            )
        else:
            await status_msg.edit_text(f"❌ Error: {error_message}")

# === Main startup ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
