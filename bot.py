# Copyright (c) 2025 Your Name or Organization
# This bot is for educational purposes only.
# Downloaded content belongs to its respective copyright holders.
# Please respect copyright laws and the terms of service of content providers.

import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Load BOT_TOKEN from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN is not set in the environment or .env file.")

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# File size limit (Telegram max is 50MB)
MAX_FILE_SIZE = 49 * 1024 * 1024  # 49 MB

# Copyright message
COPYRIGHT_NOTICE = (
    "*Copyright Disclaimer*\n\n"
    "This bot is for educational purposes only.\n"
    "Downloaded content belongs to its respective copyright holders.\n"
    "Please respect copyright laws and the terms of service of content providers."
)

# Optional: Console progress log
def download_hook(msg):
    if msg.get('status') == 'downloading':
        percent = msg.get('_percent_str', '').strip()
        if percent:
            print(f"Progress: {percent}")

# Main handler function
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text("Please send a valid video URL.")
        return

    # Send the copyright message
    await update.message.reply_markdown(COPYRIGHT_NOTICE)

    status_message = await update.message.reply_text("Processing your request...")

    ydl_opts = {
        'format': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best',
        'noplaylist': True,
        'progress_hooks': [download_hook],
        'outtmpl': 'downloads/%(title).50s.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }

    try:
        os.makedirs("downloads", exist_ok=True)
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            filename = ydl.prepare_filename(info)
            total_bytes = info.get("filesize") or info.get("filesize_approx") or 0

            if total_bytes and total_bytes > MAX_FILE_SIZE:
                await status_message.edit_text("The video is too large for Telegram (50 MB limit).")
                return

            await status_message.edit_text("Downloading...")

            ydl.download([url])

            await status_message.edit_text("Uploading...")

            if not os.path.exists(filename):
                await status_message.edit_text("Download failed: file not found.")
                return

            with open(filename, "rb") as f:
                await update.message.reply_video(f, caption=title)

            await status_message.delete()
            try:
                os.remove(filename)
            except Exception:
                pass

    except Exception as e:
        error_message = str(e).lower()

        if "instagram" in error_message and ("login required" in error_message or "cookies" in error_message or "rate-limit" in error_message):
            await status_message.edit_text("This Instagram video is private, restricted, or requires login. Please try another public post.")
        elif "requested content is not available" in error_message:
            await status_message.edit_text("The video is unavailable or has been removed. Try a different link.")
        else:
            await status_message.edit_text(f"An error occurred: {str(e)}")

# Start the bot
def main():
    os.makedirs("downloads", exist_ok=True)
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.run_polling()

if __name__ == "__main__":
    main()
