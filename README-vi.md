# 🚀 Agent Telegram Notifier

Công cụ gọn nhẹ, không phụ thuộc thư viện ngoài (zero-dependency), giúp gửi thông báo đẩy (push notification) tức thời tới **Telegram Bot** của bạn mỗi khi các AI Coding Agent (**Antigravity**, **Claude Code**, **Grok**, v.v.) hoàn thành task, kết thúc lượt làm việc (turn), hoặc cần người dùng xác nhận / trả lời câu hỏi lựa chọn (`ask_question`).

Công cụ được thiết kế để đăng ký trực tiếp vào **vòng đời Hooks nguyên bản (Native Hooks)** của từng agent (`~/.gemini/config/hooks.json`, `~/.claude/settings.json`, `~/.grok/hooks/`), đảm bảo hoạt động bền vững, chạy ngầm không gây trễ (non-blocking) trên mọi phiên làm việc và môi trường terminal.

---

## ✨ Tính Năng Nổi Bật

- 🤖 **Hỗ Trợ Đa Agent**: Tự động nhận diện chính xác agent đang chạy với huy hiệu và emoji tương ứng (🟢 Antigravity, 🟣 Claude Code, ⚡ Grok, 🔵 Cursor, 🟠 Codex, ✨ Gemini).
- 📁 **Nhận Diện Dự Án & Kho Mã Nguồn**: Tự động trích xuất tên project, thư mục gốc Git và nhánh đang làm việc.
- 🌿 **Hỗ Trợ Toàn Diện Git Worktree**: Phân biệt rõ ràng giữa làm việc tại nhánh chính và làm việc trong Git Worktree (ví dụ: `Worktree: feat-auth-module (nhánh feat/auth-module)` so với `Nhánh: main (nhánh chính)`).
- 📝 **Tự Động Đọc Tóm Tắt Task**: Tự động phân tích transcript và payload của phiên làm việc để trích xuất câu lệnh/task gần nhất mà bạn vừa giao cho agent.
- ❓ **Thông Báo Khi Agent Hỏi / Cần Lựa Chọn**: Báo ngay về điện thoại khi agent gọi các công cụ tương tác như `ask_question`, liệt kê rõ nội dung câu hỏi và danh sách các phương án để bạn kịp thời phản hồi.
- 📸 **Tích Hợp Agent Skill (`send-to-telegram`)**: Cung cấp skill cho Agent để khi bạn yêu cầu "chụp màn hình gửi cho tôi" hoặc "tìm file/ảnh trong project gửi qua telegram", agent có thể chụp ảnh (macOS/Android) hoặc tìm file và bắn ngay về Telegram.
- 🛡️ **Lọc Subagent & Chống Spam**: Tự động bỏ qua các sự kiện từ subagent chạy ngầm để tránh bắn thông báo rác; tích hợp bộ đệm thời gian (debounce mặc định 3 giây) chống gửi lặp.
- ⚡ **Zero-Dependency & Non-Blocking**: Chạy hoàn toàn bằng thư viện chuẩn của Python 3 (`urllib`, `json`, `subprocess`, `html`). Không cần `pip install`. Tốc độ thực thi cực nhanh (< 0.5 giây), không gây trễ cho agent.

---

## 📂 Cấu Trúc Thư Mục

```text
agent-telegram-notifier/
├── .env                          # Thông tin cấu hình Bot Telegram (được gitignore bảo vệ)
├── .env.example                  # File mẫu cấu hình biến môi trường
├── notify.py                     # Bộ xử lý trung tâm (nhận diện git, đọc transcript, gửi Telegram API & Files)
├── notify.sh                     # Script shell wrapper để các agent hook gọi ngầm
├── test_notification.py          # Script kiểm tra kết nối tới Telegram Bot
├── install.py                    # Script tự động đăng ký Native Hooks & Skills vào các agent
├── install.sh                    # Tiện ích gọi nhanh install.py
├── skills/
│   └── send-to-telegram/
│       └── SKILL.md              # Skill chụp màn hình, tìm file và gửi tới Telegram
├── agent_notifier.log            # File nhật ký hoạt động (được gitignore bảo vệ)
├── README.md                     # Tài liệu tiếng Anh
└── README-vi.md                  # Tài liệu tiếng Việt (file này)
```

---

## ⚙️ Hướng Dẫn Cài Đặt Nhanh (3 Bước)

### Bước 1: Tạo Telegram Bot
1. Mở ứng dụng Telegram, tìm bot **`@BotFather`**.
2. Gửi lệnh `/newbot` và làm theo hướng dẫn để đặt tên hiển thị và username cho bot.
3. Lưu lại chuỗi **HTTP API Token** (dạng: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`).

### Bước 2: Lấy Chat ID & Bấm Start Bot
1. Trên Telegram, tìm bot **`@userinfobot`** (hoặc `@RawDataBot`).
2. Gửi lệnh `/start` để lấy mã số ID tài khoản của bạn (ví dụ: `987654321`).
3. **BƯỚC QUAN TRỌNG:** Mở bot bạn vừa tạo ở Bước 1, bấm nút **Start** (`/start`). *Telegram bắt buộc người dùng phải bấm Start với bot trước thì bot mới có quyền gửi tin nhắn cho bạn.*

### Bước 3: Cấu Hình File `.env`
Trong thư mục dự án, sao chép file `.env.example` thành `.env`:

```bash
cp .env.example .env
```

Mở file `.env` và điền thông tin của bạn:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=987654321
TELEGRAM_THREAD_ID=
DEBOUNCE_SECONDS=3
```
*(Nếu gửi vào một Topic trong Supergroup Telegram, hãy điền ID của topic vào `TELEGRAM_THREAD_ID`, nếu gửi vào chat cá nhân hãy để trống).*

---

## 🧪 Kiểm Tra Hoạt Động

### 1. Kiểm Tra Kết Nối Telegram Thực Tế
Chạy lệnh kiểm tra gửi tin nhắn:

```bash
python3 test_notification.py
```
Nếu cấu hình đúng, điện thoại của bạn sẽ lập tức nhận được:
> 🔔 **Test Thông Báo Telegram Bot Thành Công!**

### 2. Xem Thử Định Dạng Tin Nhắn (Dry Run)
Kiểm tra cách hiển thị nội dung tin nhắn mà không gửi qua mạng:

```bash
python3 notify.py --dry-run \
  --agent antigravity \
  --cwd /Users/yourname/projects/my-app \
  --task "Tối ưu hoá database connection pool"
```

---

## 🛠️ Cài Đặt & Quản Lý Hooks Cho Các Agent

Trình cài đặt tự động đăng ký hook trực tiếp vào các file cấu hình Native của từng agent:
- **Antigravity**: `~/.gemini/config/hooks.json`
- **Claude Code**: `~/.claude/settings.json`
- **Grok**: `~/.grok/hooks/agent-telegram-notifier.json`

### 1. Kiểm Tra Trạng Thái Cài Đặt:
```bash
./install.sh --status
# Hoặc: python3 install.py --status
```

### 2. Cài Đặt Hooks Vào Tất Cả Các Agent:
```bash
./install.sh --install
# Hoặc: python3 install.py --install
```
*(Script sẽ tự động sao lưu bản gốc sang file `.bak` trước khi chỉnh sửa).*

### 3. Gỡ Bỏ Hooks (Khôi Phục Nguyên Trạng):
```bash
./install.sh --uninstall
# Hoặc: python3 install.py --uninstall
```

---

## 🤖 Câu Lệnh Dành Cho AI Agent Cài Đặt Tự Động

Nếu bạn đang làm việc với một trợ lý AI (như Claude Code, Antigravity, Cursor, Grok) và muốn agent tự cài đặt toàn bộ công cụ này cho bạn, hãy copy đoạn yêu cầu dưới đây và dán cho agent:

```text
Hãy giúp tôi thiết lập Agent Telegram Notifier trong dự án này:
1. Kiểm tra xem file .env đã có chưa. Nếu chưa có, copy từ .env.example sang .env và hỏi tôi cung cấp TELEGRAM_BOT_TOKEN cùng TELEGRAM_CHAT_ID.
2. Chạy `python3 test_notification.py` để kiểm tra kết nối đến Telegram.
3. Chạy `./install.sh --install` để đăng ký Native Hooks cho các agent (Antigravity, Claude, Grok).
4. Chạy `./install.sh --status` để kiểm tra và xác nhận các Native Hooks đã được kích hoạt thành công.
```

---

## 📬 Mẫu Tin Nhắn Thông Báo Trên Telegram

### 1. Khi Agent Hoàn Thành Task Trong Git Worktree
```html
🎯 Agent Đã Triển Khai Xong Task!

Agent: 🟣 Claude
📁 Dự án: ecommerce-core
🌿 Worktree: feat-checkout-flow (nhánh feat/checkout-flow)
📝 Task: Tích hợp cổng thanh toán Apple Pay
⏰ Thời gian: 22/09/2026 15:30:00
```

### 2. Khi Agent Hoàn Thành Task Ở Nhánh Chính
```html
🎯 Agent Đã Triển Khai Xong Task!

Agent: 🟢 Antigravity
📁 Dự án: personal_intelligence
🌿 Nhánh: main (nhánh chính)
📝 Task: Tối ưu CI pipeline kiểm thử trên VPS
⏰ Thời gian: 22/09/2026 15:30:00
```

### 3. Khi Agent Cần Bạn Chọn Phương Án
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

## 📄 Giấy Phép (License)

MIT License. Hoàn toàn miễn phí cho mục đích cá nhân và thương mại.
