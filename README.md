# 🚀 Agent Telegram Notifier

A lightweight, zero-dependency utility that sends instant push notifications to your **Telegram Bot** whenever AI coding agents (**Antigravity**, **Claude Code**, **Grok**, etc.) complete a task, turn, or require user input/confirmation (such as multiple-choice questions).

Designed to hook directly into each AI agent's **native configuration lifecycle** (e.g. `~/.gemini/config/hooks.json`, `~/.claude/settings.json`, `~/.grok/hooks/`), ensuring persistent, non-blocking execution across terminal sessions and environments.

---

## ✨ Key Features

- 🤖 **Multi-Agent Support**: Automatically detects and formats messages with unique badges and emojis for each agent (🟢 Antigravity, 🟣 Claude Code, ⚡ Grok, 🔵 Cursor, 🟠 Codex, ✨ Gemini).
- 📁 **Project & Repository Context**: Resolves project name, git root, and current branch.
- 🌿 **First-Class Git Worktree Support**: Differentiates between main branch repositories and active worktrees (e.g. `Worktree: feat-auth-module (branch feat/auth-module)` vs `Branch: main (main branch)`).
- 📝 **Intelligent Task Extraction**: Reads session transcripts and hook payloads to extract and summarize the exact user prompt or task the agent just worked on.
- ❓ **Interactive Question Alerts**: Triggers high-priority notifications when an agent calls interactive tools like `ask_question` with selectable options, so you know immediately when your input is needed.
- 📸 **Send-to-Telegram Agent Skill**: Equips agents to take macOS/Android screenshots or locate files/images in the project and dispatch them directly to Telegram on demand via `/bin/sh notify.sh --send-photo ...` or `--send-file ...`.
- 🛡️ **Subagent & Anti-Spam Filtering**: Intelligently ignores background subagents to prevent false notifications; includes a configurable debounce timer (default 3 seconds) to suppress rapid duplicate events.
- ⚡ **Zero-Dependency & Non-Blocking**: Built entirely with the Python 3 standard library (`urllib`, `json`, `subprocess`, `html`). No `pip install` required. Hook execution finishes in < 0.5s.

---

## 📂 Project Structure

```text
agent-telegram-notifier/
├── .env                          # Telegram Bot credentials (ignored by git)
├── .env.example                  # Sample environment configuration template
├── notify.py                     # Core engine (git detection, transcript parser, Telegram API & Files)
├── notify.sh                     # Shell wrapper for agent hooks
├── test_notification.py          # Standalone test script to verify Telegram credentials
├── install.py                    # Automated installer for native agent hooks & skills
├── install.sh                    # Quick CLI wrapper for install.py
├── skills/
│   └── send-to-telegram/
│       └── SKILL.md              # Skill for screenshot capture, file lookup & Telegram dispatch
├── agent_notifier.log            # Local activity log (ignored by git)
├── README.md                     # English documentation (this file)
└── README-vi.md                  # Vietnamese documentation
```

---

## ⚙️ Quick Setup (3 Steps)

### Step 1: Create a Telegram Bot
1. Open Telegram and chat with **`@BotFather`**.
2. Send `/newbot` and follow the prompts to choose a name and username.
3. Save the **HTTP API Token** (format: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`).

### Step 2: Get Your Chat ID & Start the Bot
1. Open Telegram and search for **`@userinfobot`** (or `@RawDataBot`).
2. Send `/start` to retrieve your numeric user ID (e.g., `987654321`).
3. **CRITICAL STEP**: Open the bot you created in Step 1 and press **Start** (`/start`). *Telegram blocks bots from sending messages to users who haven't started a conversation with the bot first.*

### Step 3: Configure `.env`
In the project directory, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=987654321
TELEGRAM_THREAD_ID=
DEBOUNCE_SECONDS=3
```
*(Leave `TELEGRAM_THREAD_ID` empty unless sending to a specific topic inside a forum supergroup).*

---

## 🧪 Verification & Testing

### 1. Test Telegram Delivery
Verify that your bot token and chat ID work:

```bash
python3 test_notification.py
```
If successful, your phone will receive:
> 🔔 **Test Thông Báo Telegram Bot Thành Công!**

### 2. Test Message Formats (Dry Run)
Preview how notifications will look without sending any network requests:

```bash
python3 notify.py --dry-run \
  --agent antigravity \
  --cwd /Users/yourname/projects/my-app \
  --task "Refactor database connection pool"
```

---

## 🛠️ Hook Installation & Management

The installer registers notification hooks directly into each agent's native configuration files:
- **Antigravity**: `~/.gemini/config/hooks.json`
- **Claude Code**: `~/.claude/settings.json`
- **Grok**: `~/.grok/hooks/agent-telegram-notifier.json`

### Check Current Hook Status
```bash
./install.sh --status
# Or: python3 install.py --status
```

### Install Hooks Into All Agents
```bash
./install.sh --install
# Or: python3 install.py --install
```
*(The script automatically creates `.bak` backups before modifying any configuration).*

### Uninstall Hooks (Restore Originals)
```bash
./install.sh --uninstall
# Or: python3 install.py --uninstall
```

---

## 🤖 AI Agent Automated Setup Prompt

If you are using an AI assistant (such as Claude Code, Antigravity, Cursor, or Grok) and want the agent to set this up for you automatically, simply copy and paste the prompt below into your agent:

```text
Please help me set up the Agent Telegram Notifier in this repository:
1. Check if .env exists. If not, copy .env.example to .env and prompt me to provide TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
2. Run `python3 test_notification.py` to confirm Telegram connectivity.
3. Run `./install.sh --install` to register native hooks for Antigravity, Claude, and Grok.
4. Run `./install.sh --status` to verify that all native hooks are active.
```

---

## 📬 Sample Telegram Notifications

### 1. Task Completed in a Git Worktree
```html
🎯 Agent Đã Triển Khai Xong Task!

Agent: 🟣 Claude
📁 Dự án: ecommerce-core
🌿 Worktree: feat-checkout-flow (nhánh feat/checkout-flow)
📝 Task: Add Apple Pay payment gateway integration
⏰ Thời gian: 22/09/2026 15:30:00
```

### 2. Task Completed in Main Branch
```html
🎯 Agent Đã Triển Khai Xong Task!

Agent: 🟢 Antigravity
📁 Dự án: personal_intelligence
🌿 Nhánh: main (nhánh chính)
📝 Task: Fix CI test suite pipeline on VPS
⏰ Thời gian: 22/09/2026 15:30:00
```

### 3. Agent Asking Multiple-Choice Questions
```html
❓ Agent Cần Bạn Trả Lời / Chọn Phương Án!

Agent: 🟢 Antigravity
📁 Dự án: personal_intelligence
🌿 Nhánh: main (nhánh chính)

Câu hỏi: Bạn muốn xử lý migration SQLite theo cách nào?
Các phương án lựa chọn:
  1. (Khuyến nghị) Tự động migrate và backup database trước
  2. Chỉ chạy migrate thủ công qua CLI

⏰ Thời gian: 22/09/2026 15:31:00
```

---

## 📄 License

MIT License. Free for personal and commercial use.
