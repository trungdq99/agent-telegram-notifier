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
- ☁️ **Automatic Google Drive Upload for Large Files (> 10MB)**: For files exceeding 10MB, the system automatically uploads them to Google Drive with public read access and delivers a formatted view/download link via the Telegram Bot.
- 🛡️ **Subagent & Anti-Spam Filtering**: Intelligently ignores background subagents to prevent false notifications; includes a configurable debounce timer (default 3 seconds) to suppress rapid duplicate events.
- ⚡ **Zero-Dependency & Non-Blocking**: Built with the Python 3 standard library and Google API Client. Hook execution finishes in < 0.5s.

---

## 📂 Project Structure

```text
agent-telegram-notifier/
├── .env                          # Telegram Bot & Google Drive credentials (ignored by git)
├── .env.example                  # Sample environment configuration template
├── gdrive.py                     # Google Drive authentication & upload module (OAuth 2.0 / Service Account)
├── notify.py                     # Core engine (git detection, transcript parser, Telegram API & Files)
├── notify.sh                     # Shell wrapper for agent hooks
├── test_notification.py          # Standalone test script to verify Telegram credentials
├── test_gdrive_upload.py         # Unit tests for Google Drive routing and threshold
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

### Step 4: (Optional) Google Drive Setup for Large Files (> 10MB)
To bypass Telegram's 10MB photo and 50MB bot upload limits, follow the [Google Cloud & Google Drive Setup](#-google-cloud--google-drive-setup-files--10mb) section below to authenticate Google Drive. Once configured, large files are automatically routed to Google Drive and shared with a public download link.

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

## ☁️ Google Cloud & Google Drive Setup (Files > 10MB)

### Why Google Drive Integration?
Telegram Bot API imposes strict limits on direct media uploads:
- **Photos (`sendPhoto`)**: Capped at **10 MB** (and rejects non-image or uncompressed formats).
- **Documents (`sendDocument`)**: Standard bot limit is **50 MB**, and uploading large files directly through bot HTTP endpoints can frequently fail due to network timeouts, rate-limiting, and slow uploads.

To overcome these constraints, **Agent Telegram Notifier** provides seamless, automated Google Drive routing:
- **Files $\le$ 10MB**: Dispatched directly via Telegram Bot API for instant inline viewing.
- **Files > 10MB** (or when forced via `--force-gdrive`): Automatically uploaded to Google Drive with resumable chunked upload, given public read access ("Anyone with the link can view"), and delivered to your Telegram chat with an elegant message containing a direct view/download link and file size metadata.

---

### 📦 1. Install Google Drive Dependencies

If you are running in an environment that does not yet include Google client libraries, install them:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
*(If you are running inside the `mcp_servers` Conda environment on macOS, these dependencies are already bundled).*

---

### 🔑 2. Step-by-Step Google Cloud Platform (GCP) Setup

Follow these steps to obtain your OAuth 2.0 credentials for personal use:

#### Step 1: Create or Select a Google Cloud Project
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. In the top navigation bar, click the project selector dropdown and click **New Project**.
3. Name your project (e.g. `Agent Telegram Notifier`) and click **Create**.
4. Make sure your newly created project is selected in the top bar.

#### Step 2: Enable the Google Drive API
1. In the navigation menu (left sidebar), go to **APIs & Services** > **Library** (or visit [Google Drive API Library](https://console.cloud.google.com/apis/library/drive.googleapis.com)).
2. In the search box, type `Google Drive API` and select it.
3. Click **Enable**.

#### Step 3: Configure the OAuth Consent Screen
1. In the left sidebar, navigate to **APIs & Services** > **OAuth consent screen** (or visit [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)).
2. Select User Type: **External** and click **Create**.
3. Fill in the required application information:
   - **App name**: `Agent Telegram Notifier`
   - **User support email**: Select your Google email.
   - **Developer contact information**: Enter your Google email.
4. Click **Save and Continue**.
5. **Scopes**: Click **Save and Continue** (the application will automatically request the minimal `https://www.googleapis.com/auth/drive.file` scope during login).
6. ⚠️ **CRITICAL STEP - Test Users**:
   - Under the **Test users** section, click **+ ADD USERS**.
   - Enter your personal Google email address (the account whose Google Drive will store the uploaded files).
   - Click **Add**, then click **Save and Continue**.
   > [!IMPORTANT]
   > While your GCP app status is "Testing", **only email accounts explicitly listed under "Test users" can authorize**. If you skip this, Google will block your sign-in with `Error 403: access_denied`.
7. Review the summary and click **Back to Dashboard**.

#### Step 4: Create OAuth 2.0 Client ID Credentials
1. In the left sidebar, navigate to **APIs & Services** > **Credentials**.
2. Click **+ CREATE CREDENTIALS** at the top, then select **OAuth client ID**.
3. In the **Application type** dropdown, select **Desktop App** *(Recommended)*.
   *(Alternatively, select Web Application with redirect URI `http://localhost`).*
4. **Name**: `Telegram Notifier Desktop Client`.
5. Click **Create**.
6. A dialog titled "OAuth client created" will appear. Click **Download JSON** (or find your client under *OAuth 2.0 Client IDs* and click the download icon ⬇️).

#### Step 5: Save Credentials to the Project
1. Rename the downloaded file to `client_secrets.json`.
2. Move it into your `agent-telegram-notifier` repository root:
   ```bash
   mv ~/Downloads/client_secret_*.json ./client_secrets.json
   ```
   *(Note: `client_secrets.json` and `.gdrive_token.json` are already in `.gitignore` so your credentials will never be committed to git).*
3. *(Optional)* If you prefer keeping the file elsewhere, specify its path in `.env`:
   ```env
   GDRIVE_CLIENT_SECRETS_FILE=/custom/path/to/client_secrets.json
   ```

---

### 🚀 3. Run One-Time Setup & Authentication

Run the setup command to link your Google account:

```bash
/bin/sh notify.sh --setup-gdrive
# Or:
python3 install.py --setup-gdrive
# Or:
python3 gdrive.py --setup
```

**What to expect during authorization:**
1. A browser window will automatically launch asking you to sign in with your Google account.
2. Choose the Google account you added as a **Test User** in Step 3.
3. If you see the warning **"Google hasn't verified this app"**, click **Advanced** (Nâng cao) -> **Go to Agent Telegram Notifier (unsafe)** (Tiếp tục truy cập).
4. Check the box to grant permission to create and manage files on Google Drive (`drive.file`).
5. Click **Continue**.
6. Return to your terminal. You should see:
   ```text
   =================================================================
   ✅ ĐĂNG NHẬP GOOGLE DRIVE THÀNH CÔNG!
   👤 Người dùng : Your Name (your.email@gmail.com)
   💾 Token lưu tại: /path/to/agent-telegram-notifier/.gdrive_token.json
   =================================================================
   ```
From now on, authentication is 100% autonomous. The refresh token stored in `.gdrive_token.json` is refreshed in the background automatically whenever it expires.

---

### 🖥️ Alternative: Service Account Setup (For Headless Servers / VPS)

If your agents run on a remote headless server without graphical browser access:
1. In GCP Console -> **APIs & Services** > **Credentials** -> Click **+ CREATE CREDENTIALS** > **Service account**.
2. Name it (e.g. `agent-notifier-uploader`), click **Create and Continue**, then **Done**.
3. Click on the newly created Service Account email -> Go to **Keys** tab -> Click **Add Key** > **Create new key** > Select **JSON** > Click **Create** to download.
4. Copy the JSON key to your server and configure `.env`:
   ```env
   GDRIVE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
   ```
5. ⚠️ **Grant Folder Permission**: In your personal Google Drive, create a folder (e.g. `Agent Uploads`), click **Share**, and give **Editor** access to your Service Account email address (`xxx@xxx.iam.gserviceaccount.com`).
6. Copy the Folder ID from the URL (`https://drive.google.com/drive/folders/<FOLDER_ID>`) and set:
   ```env
   GDRIVE_FOLDER_ID=<FOLDER_ID>
   ```

---

### ⚙️ Environment Variables Reference (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GDRIVE_THRESHOLD_MB` | `10` | Size threshold in MB. Files exceeding this size route to Google Drive. |
| `GDRIVE_CLIENT_SECRETS_FILE` | `./client_secrets.json` | Path to downloaded OAuth 2.0 client credentials JSON. |
| `GDRIVE_TOKEN_FILE` | `./.gdrive_token.json` | Path where authorized OAuth tokens and refresh tokens are stored. |
| `GDRIVE_SERVICE_ACCOUNT_FILE` | *(empty)* | Optional path to Service Account JSON key (for headless servers). |
| `GDRIVE_FOLDER_ID` | *(auto)* | Optional Drive folder ID to save files in. If empty, uses an `Agent Telegram Notifier` folder. |

---

### 🧪 4. Testing & Verification

Check installation and configuration status:
```bash
./install.sh --status
# Or: python3 install.py --status
```
You will see:
```text
☁️ 4. GOOGLE DRIVE UPLOAD (Hỗ trợ file dung lượng > 10MB)
=================================================================
  Google Drive   : ✅ ĐÃ CẤU HÌNH (OAuth 2.0 Token: .gdrive_token.json)
```

Run unit tests to verify threshold detection and mock uploads:
```bash
python3 test_gdrive_upload.py
```

Test file uploads via CLI:
```bash
# Test 1: Upload a file directly via gdrive.py
python3 gdrive.py --upload "/path/to/test_file.zip"

# Test 2: Full pipeline (upload to Drive and notify Telegram)
/bin/sh notify.sh --send-file "/path/to/large_file.zip" --caption "📦 Large dataset test"

# Test 3: Force Google Drive upload even for small files
/bin/sh notify.sh --send-file "/path/to/small_file.txt" --force-gdrive

# Test 4: Custom threshold (e.g., 5MB)
/bin/sh notify.sh --send-file "/path/to/file.mp4" --gdrive-threshold 5
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
5. Check Google Drive setup with `python3 install.py --status`. If client_secrets.json is present, guide me to run `./install.sh --setup-gdrive`.
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
