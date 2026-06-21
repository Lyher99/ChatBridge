"""
ChatBridge — Relay messages between Telegram and Discord

Telegram bot that forwards messages to Discord, and a Discord bot that
forwards messages to Telegram. Two-way sync for one chat group.

Usage:
  python bridge.py            # Run both bots
  python bridge.py --telegram # Telegram → Discord only
  python bridge.py --discord  # Discord → Telegram only
"""
import os
import sys
import asyncio
import logging
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s'
)
log = logging.getLogger('chatbridge')

# ──────────────────────────────────────────
# SHARED CONFIG
# ──────────────────────────────────────────
TELEGRAM_TOKEN = None
TELEGRAM_CHAT_ID = None
DISCORD_TOKEN = None
DISCORD_CHANNEL_ID = None

MESSAGE_HISTORY = []       # Keep recent messages for context
MAX_HISTORY = 100

def load_config():
    """Load credentials from environment variables."""
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, DISCORD_TOKEN, DISCORD_CHANNEL_ID
    from dotenv import load_dotenv
    load_dotenv()

    TELEGRAM_TOKEN = ***'TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = int(***'TELEGRAM_CHAT_ID', 0))
    DISCORD_TOKEN = ***'DISCORD_TOKEN')
    DISCORD_CHANNEL_ID = int(***'DISCORD_CHANNEL_ID', 0))

# ──────────────────────────────────────────
# TELEGRAM BOT
# ──────────────────────────────────────────
class TelegramBridge:
    """Forwards messages from Telegram → Discord."""

    def __init__(self, discord_send_callback=None):
        self.discord_send = discord_send_callback
        self.application = None

    async def start(self):
        from telegram import Update
        from telegram.ext import Application, MessageHandler, filters, ContextTypes

        if not TELEGRAM_TOKEN:
            log.error("TELEGRAM_TOKEN not set")
            return

        self.application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Handle all text messages
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~frames.STATUS_UPDATE,
            self.handle_message
        ))
        # Handle media
        self.application.add_handler(MessageHandler(
            (filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.Document)
            & ~filters.COMMAND,
            self.handle_media
        ))

        log.info("🤖 Telegram bot starting (polling)...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        # Keep running
        while True:
            await asyncio.sleep(3600)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _check_telegram_user(update):
            return

        user = update.effective_user
        text = update.message.text
        timestamp = update.message.date.strftime('%H:%M')

        # Show who sent it
        display_name = user.full_name or user.username or "Telegram User"
        avatar = f"https://ui-avatars.com/api/?name={display_name}&size=32"

        relay_text = f"**[{display_name}]({avatar})** ({timestamp})\n> {text}"

        if self.discord_send:
            self.discord_send(relay_text, platform='telegram', author=display_name, avatar=avatar, timestamp=timestamp)

        _store_message('telegram', user.id, display_name, text)

        log.info(f"📤 Telegram → Discord: {display_name}: {text[:60]}")

    async def handle_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not _check_telegram_user(update):
            return

        user = update.effective_user
        display_name = user.full_name or user.username or "Telegram User"
        timestamp = update.message.date.strftime('%H:%M')

        # Determine media type and caption
        caption = update.message.caption or ""
        media_type = None
        file_id = None

        if update.message.photo:
            media_type = 'photo'
            file_id = update.message.photo[-1].file_id
        elif update.message.video:
            media_type = 'video'
            file_id = update.message.video.file_id
        elif update.message.audio:
            media_type = 'audio'
            file_id = update.message.audio.file_id
        elif update.message.document:
            media_type = 'document'
            file_id = update.message.document.file_id
            caption = f"📎 {update.message.document.file_name}\n{caption}"

        if self.discord_send:
            msg = f"**[{display_name}]** ({timestamp})\n📷 {caption}" if caption else f"**[{display_name}]** ({timestamp})\n📷"
            self.discord_send(msg, platform='telegram', author=display_name, timestamp=timestamp)

    async def stop(self):
        if self.application:
            await self.application.stop()
            await self.application.shutdown()

    def send_message(self, text: str):
        """Send a message FROM Discord TO Telegram."""
        if not TELEGRAM_CHAT_ID:
            log.warning("TELEGRAM_CHAT_ID not set, can't send")
            return
        asyncio.create_task(self._send(text))

    async def _send(self, text: str):
        if self.application and self.application.bot:
            try:
                await self.application.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as e:
                log.error(f"Failed to send Telegram message: {e}")

# ──────────────────────────────────────────
# DISCORD BOT
# ──────────────────────────────────────────
class DiscordBridge:
    """Forwards messages from Discord → Telegram."""

    def __init__(self, telegram_send_callback=None):
        self.telegram_send = telegram_send_callback
        self.bot = None
        self.loop = None

    async def start(self):
        import discord
        from discord.ext import commands

        if not DISCORD_TOKEN:
            log.error("DISCORD_TOKEN not set")
            return

        intents = discord.Intents.default()
        intents.message_content = True

        self.bot = commands.Bot(command_prefix='!', intents=intents)

        @self.bot.event
        async def on_ready():
            log.info(f"💬 Discord bot logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(message):
            # Don't react to our own messages or DMs
            if message.author == self.bot.user:
                return
            if not message.guild:
                return
            # Only relay from the configured channel
            if DISCORD_CHANNEL_ID and message.channel.id != DISCORD_CHANNEL_ID:
                return

            timestamp = message.created_at.strftime('%H:%M')
            display_name = message.author.display_name or message.author.name

            # Build the message
            content = message.content
            if message.attachments:
                for att in message.attachments:
                    content += f"\n📎 {att.url}"

            relay_text = f"**{display_name}** ({timestamp})\n{content}"

            if self.telegram_send:
                self.telegram_send(relay_text, platform='discord', author=display_name, timestamp=timestamp)

            _store_message('discord', message.author.id, display_name, content)
            log.info(f"📤 Discord → Telegram: {display_name}: {content[:60]}")

            # Still allow commands to work
            await self.bot.process_commands(message)

        self.loop = asyncio.get_event_loop()
        await self.bot.start(DISCORD_TOKEN)

    async def stop(self):
        if self.bot:
            await self.bot.close()

    def send_message(self, text: str):
        """Send a message FROM Telegram TO Discord."""
        if not DISCORD_CHANNEL_ID:
            log.warning("DISCORD_CHANNEL_ID not set, can't send")
            return
        asyncio.create_task(self._send(text))

    async def _send(self, text: str):
        if self.bot and self.bot.is_ready():
            channel = self.bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                try:
                    await channel.send(text)
                except Exception as e:
                    log.error(f"Failed to send Discord message: {e}")

# ──────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────
def _check_telegram_user(update):
    """Only relay from the configured chat."""
    from telegram import Update
    if TELEGRAM_CHAT_ID and update.effective_chat.id != TELEGRAM_CHAT_ID:
        return False
    return True

def _store_message(platform, user_id, name, text):
    """Keep a rolling log of recent messages."""
    MESSAGE_HISTORY.append({
        'platform': platform,
        'user_id': user_id,
        'name': name,
        'text': text,
        'time': datetime.now().isoformat()
    })
    if len(MESSAGE_HISTORY) > MAX_HISTORY:
        MESSAGE_HISTORY.pop(0)

# ──────────────────────────────────────────
# BRIDGE — Connects both bots
# ──────────────────────────────────────────
class Bridge:
    """Coordinates Telegram → Discord and Discord → Telegram relaying."""

    def __init__(self):
        load_config()
        self.telegram = TelegramBridge(discord_send_callback=self.discord_relay)
        self.discord = DiscordBridge(telegram_send_callback=self.telegram_relay)

    def telegram_relay(self, text, **kwargs):
        """Called when Discord receives a message → forward to Telegram."""
        platform = kwargs.get('platform', 'discord')
        author = kwargs.get('author', 'Unknown')
        timestamp = kwargs.get('timestamp', '')

        # Telegram formatting
        if platform == 'discord':
            # Already formatted by Discord handler
            self.telegram.send_message(text)

    def discord_relay(self, text, **kwargs):
        """Called when Telegram receives a message → forward to Discord."""
        platform = kwargs.get('platform', 'telegram')
        author = kwargs.get('author', 'Unknown')
        avatar = kwargs.get('avatar', '')
        timestamp = kwargs.get('timestamp', '')

        # Discord formatting with embed-style text
        if platform == 'telegram':
            self.discord.send_message(text)

    def run_async(self):
        """Run both bots concurrently in the same event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_both():
            await asyncio.gather(
                self.telegram.start(),
                self.discord.start(),
                return_exceptions=True
            )

        try:
            loop.run_until_complete(run_both())
        except KeyboardInterrupt:
            log.info("🛑 Shutting down...")
        finally:
            loop.run_until_complete(asyncio.gather(
                self.telegram.stop(),
                self.discord.stop(),
                return_exceptions=True
            ))
            loop.close()

    def run_threaded(self):
        """Run Telegram and Discord in separate threads (fallback)."""
        tg_thread = threading.Thread(target=self.telegram.start, daemon=True)
        dc_thread = threading.Thread(target=self.discord.start, daemon=True)

        tg_thread.start()
        dc_thread.start()

        try:
            while tg_thread.is_alive() and dc_thread.is_alive():
                tg_thread.join(1)
        except KeyboardInterrupt:
            log.info("🛑 Shutting down...")

# ──────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────
def main():
    load_config()

    if not TELEGRAM_TOKEN and not DISCORD_TOKEN:
        log.error("Neither TELEGRAM_TOKEN nor DISCORD_TOKEN are set. Check .env")
        sys.exit(1)

    bridge = Bridge()
    log.info("🌉 ChatBridge starting...")
    log.info("   Telegram → Discord  |  Discord → Telegram")
    bridge.run_async()

if __name__ == '__main__':
    main()
