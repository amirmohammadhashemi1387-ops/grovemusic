import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeAudio
import yt_dlp

# ----------------- تنظیمات -----------------
# این مقادیر از بخش Environment Variables در Render خوانده می‌شوند
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID", "@Grove_street_music")

client = TelegramClient('downloader_session', API_ID, API_HASH)

# تنظیمات دانلود با بالاترین کیفیت (320kbps)
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
    'outtmpl': '/tmp/%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}

def download_audio(song_name):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
        video_info = info['entries'][0]
        file_path = ydl.prepare_filename(video_info)
        
        # اصلاح مسیر فایل بعد از تبدیل شدن به mp3
        if not os.path.exists(file_path):
            file_path = os.path.splitext(file_path)[0] + '.mp3'
            
        return video_info, file_path

# ----------------- دستور /dl -----------------
@client.on(events.NewMessage(pattern=r'^/dl '))
async def handler(event):
    song_name = event.text.split(' ', 1)[1]
    await event.reply(f"⏳ Searching and downloading: {song_name} ...")
    
    try:
        # دانلود در یک ترد جداگانه تا ربات قفل نشود
        video_info, file_path = await asyncio.to_thread(download_audio, song_name)
        
        await event.reply(f"✅ Downloaded. Uploading to channel...")
        
        # آپلود به کانال با متادیتای صوتی صحیح
        await client.send_file(
            TARGET_CHAT_ID,
            file_path,
            caption=f"🎵 **{video_info.get('title', song_name)}**\n🎤 {video_info.get('uploader', 'Unknown')}",
            attributes=[
                DocumentAttributeAudio(
                    duration=int(video_info.get('duration', 0)),
                    title=video_info.get('title', song_name),
                    performer=video_info.get('uploader', 'Unknown')
                )
            ]
        )
        
        # پاک کردن فایل موقت از سرور
        if os.path.exists(file_path):
            os.remove(file_path)
            
        await event.reply("🎉 Successfully uploaded to the channel!")
        
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Downloader is running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
