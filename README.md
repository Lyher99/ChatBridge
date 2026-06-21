# 🌉 ChatBridge

> **Two-way chat relay between Telegram and Discord.**  
> Messages sent in a Telegram group are instantly forwarded to a Discord channel — and vice versa.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- **↔️ Two-way sync** — Telegram ↔ Discord
- **📸 Media relay** — Photos, videos, documents, audio
- **👤 Username display** — Shows who sent what on each side
- **⏱️ Timestamps** — When the message was sent
- **🔒 Channel-restricted** — Only relays from configured channels
- **⚡ Single-file** — One Python file, zero config frameworks
- **🛡️ Lightweight** — No database, no Redis, just relay

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/ChatBridge.git
cd ChatBridge
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Create bots & get tokens

#### Telegram Bot
1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Get your **API token**
3. Add bot to your group chat
4. Message [@userinfobot](https://t.me/userinfobot) to get your **chat ID**

#### Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. **New Application** → **Bot** → **Add Bot**
3. Copy the **token**
4. Enable **Message Content Intent** (Privileged Gateway Intents)
5. Invite to server: OAuth2 → URL Generator → `bot` scope + `Send Messages` / `Read Message History` permissions
6. Right-click your channel → **Copy ID** (enable Developer Mode first)

### 4. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
DISCORD_TOKEN=ABCdef123GHIjkl456MNOpqr789STUvwx
DISCORD_CHANNEL_ID=123456789012345678
```

### 5. Run

```bash
python bridge.py
```

That's it. Messages now flow both ways. 🎉

---

## 🧠 How It Works

```
Telegram Group                Discord Channel
     │                             │
     │  ┌─────────────────────┐    │
     ├──▶  Telegram Bot       │    │
     │  │  (bridge.py)        │◄───┤
     │  │  Discord Bot        │    │
     │  └─────────────────────┘    │
     │                             │
```

- **Telegram → Discord**: Telegram pushes messages to `bridge.py` → calls Discord's webhook/API → message appears in Discord channel
- **Discord → Telegram**: Discord's `on_message` event fires → `bridge.py` calls Telegram's `sendMessage` API → message appears in Telegram group

---

## 🧩 Project Structure

```
ChatBridge/
├── bridge.py             # 🏠 Main relay (one file, does everything)
├── .env.example          # 🔑 Template for credentials
├── requirements.txt      # 📦 Dependencies
├── .gitignore            # 🚫 Ignored files
└── README.md             # 📖 This file
```

**One file. Zero complexity.**

---

## 📦 Dependencies

- `python-telegram-bot` — Telegram Bot API
- `discord.py` — Discord Bot API
- `python-dotenv` — Load `.env` config
- `aiohttp` — Async HTTP (used by both)

---

## 🤝 Use Cases

- **Bridge communities** — Keep a Discord and Telegram community in sync
- **Cross-platform teams** — Some members prefer Discord, others Telegram
- **Notifications** — Mirror alerts from one platform to the other
- **Migrating** — Slowly move a community while keeping both active

---

## ⚠️ Notes

- Both bots must be members of the respective chat/channel
- The Telegram bot must have **Message Content** intent enabled
- For large groups, consider rate limits (both platforms have them)
- This is designed for **a single chat pair** — one Telegram ↔ one Discord

---

## 📄 License

MIT — do whatever you want with it.

---

**Built with 🌉 by Lyher**
# ChatBridge
# ChatBridge
