---
name: send-to-telegram
description: Use when asked to capture screenshots, find files or images in the project, or send files, documents, and media to the user via Telegram
---

# Send to Telegram Skill

This skill enables AI coding agents (Antigravity, Claude Code, Grok, etc.) to capture screenshots, locate files/images in the project, and instantly dispatch them to the user's Telegram Bot.

> [!NOTE]
> **Dung lượng & Google Drive Integration**:
> - File **$\le$ 10MB**: Gửi trực tiếp qua Telegram API (`sendPhoto` cho ảnh hoặc `sendDocument` cho tài liệu/code).
> - File **> 10MB**: Công cụ tự động upload file lên **Google Drive**, phân quyền truy cập đọc công khai và gửi đường link xem/tải trực tiếp kèm dung lượng file về Telegram Bot.

## Trigger Scenarios
Activate this skill whenever the user requests:
- "Chụp màn hình gửi cho tôi" / "Chụp ảnh màn hình gửi qua telegram" / "Take screenshot and send to me"
- "Tìm ảnh / file trong project gửi cho tôi" / "Find image or file in project and send to Telegram"
- "Gửi tài liệu / file này qua Telegram" / "Dispatch file/document to Telegram"

---

## 🛠️ CLI Dispatch Tool

All deliveries are handled by the lightweight notifier wrapper:
`NOTIFY_BIN="/Users/trungshin/development/agent-telegram-notifier/notify.sh"`

### 1. Send a Photo / Image
Use `--send-photo` with an optional `--caption`:
```bash
/bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
  --send-photo "/path/to/image.png" \
  --caption "🖼️ <b>Mô tả hình ảnh</b>"
```
*(Supports PNG, JPG, JPEG, WEBP, GIF. If SVG, routes as a document. If >10MB, automatically uploads to Google Drive and sends link).*

### 2. Send a Document / Code / Large File
Use `--send-file` (or `--send-doc`) with an optional `--caption`:
```bash
/bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
  --send-file "/path/to/document.md" \
  --caption "📄 <b>Kế hoạch triển khai</b>"
```
*(Supports any file type. If file > 10MB, the tool automatically uploads it to Google Drive and dispatches the drive link to Telegram).*

### 3. Google Drive Options
- **One-time Setup / Login**:
  ```bash
  /bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh --setup-gdrive
  ```
- **Force Google Drive upload** (regardless of file size):
  ```bash
  /bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
    --send-file "/path/to/file.zip" \
    --force-gdrive \
    --caption "📦 File quan trọng lưu trên Google Drive"
  ```
- **Custom threshold**:
  ```bash
  /bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
    --send-file "/path/to/file.zip" \
    --gdrive-threshold 5
  ```

---

## 📸 Workflow 1: Capture and Send Screenshot

### A. macOS Desktop / Window Screenshot
Run native macOS `screencapture`:
```bash
TIMESTAMP=$(date +%s)
SCREENSHOT_PATH="/tmp/screenshot_${TIMESTAMP}.png"
screencapture -x "${SCREENSHOT_PATH}"

/bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
  --send-photo "${SCREENSHOT_PATH}" \
  --caption "📸 <b>Ảnh chụp màn hình macOS</b>"
```
*(Flag `-x` captures silently without camera shutter sound).*

### B. Mobile / Android Emulator Screenshot
If working on an Android/Flutter project with an active device or emulator:
```bash
TIMESTAMP=$(date +%s)
SCREENSHOT_PATH="/tmp/android_screen_${TIMESTAMP}.png"
adb exec-out screencap -p > "${SCREENSHOT_PATH}"

/bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
  --send-photo "${SCREENSHOT_PATH}" \
  --caption "📱 <b>Ảnh chụp màn hình Android Emulator/Device</b>"
```

### C. Browser Tab Screenshot
If using `conpet` or `browser-skill`, capture the tab/page to a file, then call `notify.sh --send-photo`.

---

## 🔍 Workflow 2: Find File or Image in Project and Send

1. **Locate the file**:
   Use codebase tools (`find`, `glob`, code search) within the project directory:
   ```bash
   find . -type f -name "*keyword*"
   ```
2. **Determine file type & size**:
   - If image (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`) $\le$ 10MB: use `--send-photo`.
   - If document, code, archive, or any file > 10MB: use `--send-file` (automatically routes to Google Drive if >10MB).
3. **Dispatch to Telegram**:
   ```bash
   /bin/sh /Users/trungshin/development/agent-telegram-notifier/notify.sh \
     --send-file "/absolute/path/to/file.ext" \
     --caption "📁 <b>File từ dự án:</b> <code>filename.ext</code>"
   ```
4. **Confirm to User**:
   Provide a clickable link to the file in your response: `[filename.ext](file:///absolute/path/to/file.ext)`.
