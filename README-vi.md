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
- ☁️ **Tự Động Upload Google Drive Cho File Lớn (> 10MB)**: Với các file hoặc hình ảnh vượt quá ngưỡng 10MB, hệ thống tự động tải file lên Google Drive, phân quyền đọc công khai ("anyone with link can view") và gửi đường link xem/tải trực tiếp kèm thông tin dung lượng file vào Telegram Bot.
- 🛡️ **Lọc Subagent & Chống Spam**: Tự động bỏ qua các sự kiện từ subagent chạy ngầm để tránh bắn thông báo rác; tích hợp bộ đệm thời gian (debounce mặc định 3 giây) chống gửi lặp.
- ⚡ **Zero-Dependency & Non-Blocking**: Chạy hoàn toàn bằng thư viện chuẩn của Python 3 (`urllib`, `json`, `subprocess`, `html`) và Google Client API (`googleapiclient`). Tốc độ thực thi cực nhanh, không gây trễ cho agent.

---

## 📂 Cấu Trúc Thư Mục

```text
agent-telegram-notifier/
├── .env                          # Cấu hình Bot Telegram & Google Drive (được gitignore bảo vệ)
├── .env.example                  # File mẫu cấu hình biến môi trường
├── gdrive.py                     # Module xác thực và upload file lên Google Drive (OAuth 2.0 / Service Account)
├── notify.py                     # Bộ xử lý trung tâm (nhận diện git, đọc transcript, gửi Telegram API & Files)
├── notify.sh                     # Script shell wrapper để các agent hook gọi ngầm
├── test_notification.py          # Script kiểm tra kết nối tới Telegram Bot
├── test_gdrive_upload.py         # Bộ kiểm thử Unit Test cho tính năng Google Drive & ngưỡng 10MB
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

### Bước 4: (Tùy chọn) Cấu Hình Google Drive Cho File Dung Lượng Lớn (> 10MB)
Để vượt qua giới hạn 10MB ảnh và 50MB tài liệu của Telegram, hãy xem mục [Hướng Dẫn Cấu Hình Google Cloud & Google Drive](#-hướng-dẫn-cấu-hình-google-cloud--google-drive-file--10mb) bên dưới để lấy file `client_secrets.json` và chạy `/bin/sh notify.sh --setup-gdrive`. Sau khi cấu hình, các file dung lượng lớn sẽ được tự động đưa lên Google Drive và gửi kèm link tải công khai.

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

## ☁️ Hướng Dẫn Cấu Hình Google Cloud & Google Drive (File > 10MB)

### Tại Sao Cần Tích Hợp Google Drive?
Telegram Bot API áp dụng giới hạn dung lượng khá khắt khe khi truyền tải tệp qua bot:
- **Ảnh (`sendPhoto`)**: Giới hạn tối đa **10 MB** (và từ chối các định dạng ảnh không nén hoặc raw).
- **Tài liệu/Tệp (`sendDocument`)**: Giới hạn bot thông thường là **50 MB**. Việc gửi file dung lượng lớn qua giao thức HTTP của Bot API rất dễ bị gián đoạn (timeout), nghẽn mạng hoặc gặp lỗi rate-limit.

Để giải quyết triệt để vấn đề này, **Agent Telegram Notifier** được tích hợp cơ chế tự động định tuyến thông minh:
- **File $\le$ 10MB**: Gửi trực tiếp qua Telegram Bot API để hiển thị ngay trong khung chat.
- **File > 10MB** (hoặc khi bật cờ `--force-gdrive`): Tự động tải lên Google Drive với cơ chế phân mảnh (resumable chunked upload), tự động cấp quyền đọc công khai ("Bất kỳ ai có đường liên kết đều có thể xem/tải"), đồng thời gửi ngay tin nhắn về Telegram kèm đường link xem/tải trực tiếp và thông tin kích thước file.

---

### 📦 1. Cài Đặt Thư Viện Cần Thiết

Nếu bạn đang chạy trên môi trường Python độc lập chưa cài sẵn Google Client Library, hãy chạy lệnh sau:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```
*(Nếu bạn đang sử dụng môi trường Conda `mcp_servers` trên macOS theo cấu hình mặc định, các thư viện này đã được tích hợp sẵn).*

---

### 🔑 2. Các Bước Thiết Lập Google Cloud Platform (GCP) Chi Tiết

Thực hiện theo các bước sau để tạo thông tin xác thực OAuth 2.0 cho tài khoản Google của bạn:

#### Bước 1: Tạo Dự Án Mới (Google Cloud Project)
1. Truy cập vào [Google Cloud Console](https://console.cloud.google.com/).
2. Trên thanh điều hướng trên cùng, nhấn vào thanh chọn dự án (Project dropdown) -> Chọn **New Project** (Dự án mới).
3. Đặt tên cho dự án (ví dụ: `Agent Telegram Notifier`) rồi bấm **Create** (Tạo).
4. Chờ vài giây và đảm bảo dự án vừa tạo đang được chọn trên thanh điều hướng trên cùng.

#### Bước 2: Kích Hoạt Google Drive API
1. Mở menu điều hướng bên trái (biểu tượng ☰) -> Chọn **APIs & Services** > **Library** (hoặc truy cập trực tiếp [Thư viện Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)).
2. Trong ô tìm kiếm, gõ `Google Drive API` và chọn dịch vụ này.
3. Bấm **Enable** (Bật).

#### Bước 3: Cấu Hình Màn Hình Đồng Ý OAuth (OAuth Consent Screen)
1. Ở menu bên trái, chọn **APIs & Services** > **OAuth consent screen** (hoặc truy cập [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)).
2. Tại mục User Type, chọn **External** (Bên ngoài) -> Bấm **Create** (Tạo).
3. Điền các thông tin cơ bản của ứng dụng:
   - **App name**: `Agent Telegram Notifier`
   - **User support email**: Chọn email Google của bạn.
   - **Developer contact information**: Nhập email của bạn.
4. Bấm **Save and Continue** (Lưu và tiếp tục).
5. **Scopes** (Phạm vi): Bấm **Save and Continue** (Bỏ qua bước này, hệ thống sẽ tự động yêu cầu quyền tối thiểu `https://www.googleapis.com/auth/drive.file` khi bạn đăng nhập).
6. ⚠️ **BƯỚC CỰC KỲ QUAN TRỌNG - Thêm Test Users**:
   - Tại mục **Test users** (Người dùng thử nghiệm), bấm nút **+ ADD USERS**.
   - Nhập chính xác địa chỉ email Google mà bạn dự định đăng nhập để lưu trữ file trên Drive.
   - Bấm **Add**, sau đó bấm **Save and Continue**.
   > [!IMPORTANT]
   > Khi ứng dụng GCP đang ở trạng thái thử nghiệm ("Testing"), **chỉ những tài khoản email được thêm vào danh sách "Test users" mới có quyền cấp phép đăng nhập**. Nếu bỏ qua bước này, bạn sẽ gặp lỗi `Error 403: access_denied` khi đăng nhập.
7. Xem lại màn hình tóm tắt rồi bấm **Back to Dashboard**.

#### Bước 4: Tạo Thông Tin Xác Thực (OAuth 2.0 Client ID)
1. Ở menu bên trái, chọn **APIs & Services** > **Credentials** (Thông tin xác thực).
2. Nhấn nút **+ CREATE CREDENTIALS** ở trên cùng -> Chọn **OAuth client ID**.
3. Tại ô **Application type** (Loại ứng dụng), chọn **Desktop App** (Ứng dụng cho máy tính để bàn) *(Khuyên dùng)*.
   *(Hoặc chọn Web Application và thêm `http://localhost` vào Authorized redirect URIs).*
4. **Name**: `Telegram Notifier Desktop Client`.
5. Bấm **Create** (Tạo).
6. Một hộp thoại "OAuth client created" xuất hiện. Bấm **Download JSON** (hoặc tìm đến mục *OAuth 2.0 Client IDs* và bấm vào biểu tượng tải xuống ⬇️).

#### Bước 5: Đưa File Vào Thư Mục Dự Án
1. Đổi tên file vừa tải về thành `client_secrets.json`.
2. Di chuyển file vào thư mục gốc của dự án `agent-telegram-notifier`:
   ```bash
   mv ~/Downloads/client_secret_*.json ./client_secrets.json
   ```
   *(Lưu ý: `client_secrets.json` và `.gdrive_token.json` đã được đưa vào `.gitignore` nên thông tin bảo mật của bạn sẽ không bao giờ bị đẩy lên git).*
3. *(Tùy chọn)* Nếu muốn đặt file ở thư mục khác, bạn có thể chỉ định đường dẫn tuyệt đối trong file `.env`:
   ```env
   GDRIVE_CLIENT_SECRETS_FILE=/đường/dẫn/tới/client_secrets.json
   ```

---

### 🚀 3. Chạy Lệnh Xác Thực Đăng Nhập Một Lần Duy Nhất

Sau khi đã có file `client_secrets.json`, chạy lệnh sau trong terminal:

```bash
/bin/sh notify.sh --setup-gdrive
# Hoặc:
python3 install.py --setup-gdrive
# Hoặc:
python3 gdrive.py --setup
```

**Quá trình xác thực trên trình duyệt:**
1. Trình duyệt mặc định của máy tính sẽ tự động mở trang đăng nhập Google.
2. Chọn đúng tài khoản Google mà bạn đã thêm vào danh sách **Test Users** ở Bước 3.
3. Nếu gặp màn hình cảnh báo bảo mật **"Google chưa xác minh ứng dụng này" (Google hasn't verified this app)**, bạn hãy yên tâm vì đây là ứng dụng cá nhân do chính bạn tạo. Bấm **Nâng cao (Advanced)** -> Chọn **Đi tới Agent Telegram Notifier (không an toàn) / Go to Agent Telegram Notifier (unsafe)**.
4. Tích chọn đồng ý cấp quyền xem, sửa, tạo và xóa các tệp Google Drive mà ứng dụng sử dụng (`drive.file`).
5. Bấm **Tiếp tục (Continue)**.
6. Quay lại màn hình terminal, bạn sẽ nhận được thông báo:
   ```text
   =================================================================
   ✅ ĐĂNG NHẬP GOOGLE DRIVE THÀNH CÔNG!
   👤 Người dùng : Tên của bạn (email@gmail.com)
   💾 Token lưu tại: /path/to/agent-telegram-notifier/.gdrive_token.json
   =================================================================
   ```
Từ nay về sau, việc xác thực diễn ra hoàn toàn tự động! Token làm mới (refresh token) được lưu trong `.gdrive_token.json` và sẽ tự động làm mới ngầm mỗi khi hết hạn mà bạn không cần phải đăng nhập lại lần nào nữa.

---

### 🖥️ Phương Thức Phụ: Cấu Hình Service Account (Cho Server Headless / VPS)

Nếu bạn chạy các agent trên một máy chủ đám mây không có giao diện đồ họa / trình duyệt:
1. Trong GCP Console -> **APIs & Services** > **Credentials** -> Bấm **+ CREATE CREDENTIALS** > **Service account**.
2. Đặt tên (ví dụ: `agent-notifier-uploader`), bấm **Create and Continue**, sau đó bấm **Done**.
3. Bấm vào email của Service Account vừa tạo -> Chuyển sang tab **Keys** -> Bấm **Add Key** > **Create new key** > Chọn loại **JSON** > Bấm **Create** để tải key về máy.
4. Đặt file key vào máy chủ và khai báo trong `.env`:
   ```env
   GDRIVE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
   ```
5. ⚠️ **Cấp Quyền Folder Trên Drive Cá Nhân**: Do Service Account có không gian lưu trữ riêng độc lập, bạn cần vào Google Drive cá nhân, tạo một thư mục (ví dụ: `Agent Uploads`), bấm **Chia sẻ (Share)** và thêm email của Service Account (`xxx@xxx.iam.gserviceaccount.com`) với quyền **Người chỉnh sửa (Editor)**.
6. Lấy ID của thư mục từ URL trên trình duyệt (`https://drive.google.com/drive/folders/<FOLDER_ID>`) và điền vào `.env`:
   ```env
   GDRIVE_FOLDER_ID=<FOLDER_ID>
   ```

---

### ⚙️ Bảng Tham Chiếu Biến Môi Trường (`.env`)

| Biến môi trường | Mặc định | Ý nghĩa |
| :--- | :--- | :--- |
| `GDRIVE_THRESHOLD_MB` | `10` | Ngưỡng dung lượng (MB). File vượt quá kích thước này sẽ được upload qua Google Drive. |
| `GDRIVE_CLIENT_SECRETS_FILE` | `./client_secrets.json` | Đường dẫn tới file thông tin xác thực OAuth client ID. |
| `GDRIVE_TOKEN_FILE` | `./.gdrive_token.json` | Đường dẫn file lưu trữ token đã đăng nhập. |
| `GDRIVE_SERVICE_ACCOUNT_FILE` | *(để trống)* | Đường dẫn file key Service Account JSON (dành cho VPS không có trình duyệt). |
| `GDRIVE_FOLDER_ID` | *(tự tạo)* | ID của thư mục trên Drive muốn lưu file vào. Mặc định sẽ tự tạo thư mục `Agent Telegram Notifier`. |

---

### 🧪 4. Kiểm Tra & Chạy Thử Hoạt Động

Kiểm tra trạng thái cấu hình hiện tại:
```bash
./install.sh --status
# Hoặc: python3 install.py --status
```
Kết quả hiển thị:
```text
☁️ 4. GOOGLE DRIVE UPLOAD (Hỗ trợ file dung lượng > 10MB)
=================================================================
  Google Drive   : ✅ ĐÃ CẤU HÌNH (OAuth 2.0 Token: .gdrive_token.json)
```

Chạy bộ kiểm thử tự động (Unit Test):
```bash
python3 test_gdrive_upload.py
```

Kiểm tra gửi file thực tế qua CLI:
```bash
# Kiểm tra 1: Test upload file trực tiếp qua module gdrive
python3 gdrive.py --upload "/đường/dẫn/file_test.zip"

# Kiểm tra 2: Test trọn vẹn quy trình (Upload Drive và thông báo Telegram)
/bin/sh notify.sh --send-file "/đường/dẫn/file_lon.zip" --caption "📦 Bản sao lưu dữ liệu thử nghiệm"

# Kiểm tra 3: Ép buộc upload Drive ngay cả khi file nhỏ hơn 10MB
/bin/sh notify.sh --send-file "/đường/dẫn/file_nho.txt" --force-gdrive

# Kiểm tra 4: Thay đổi ngưỡng dung lượng kích hoạt Drive (ví dụ: 5MB)
/bin/sh notify.sh --send-file "/đường/dẫn/video.mp4" --gdrive-threshold 5
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
5. Kiểm tra trạng thái Google Drive bằng lệnh `python3 install.py --status`. Nếu đã có file client_secrets.json, hãy hướng dẫn tôi chạy `./install.sh --setup-gdrive`.
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
