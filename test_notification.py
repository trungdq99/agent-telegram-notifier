#!/usr/bin/env python3
"""
Test Telegram Notification Script
Kiểm tra cấu hình Telegram Bot Token và Chat ID trong file .env.
"""

import sys
import os

# Import từ notify.py
from notify import load_env, send_telegram

def main():
    print("=" * 60)
    print("🤖 KIỂM TRA CẤU HÌNH TELEGRAM BOT CHO AGENT NOTIFIER")
    print("=" * 60)

    config = load_env()
    token = config.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = config.get("TELEGRAM_CHAT_ID", "").strip()
    thread_id = config.get("TELEGRAM_THREAD_ID", "").strip()

    if not token or token == "your_bot_token_here":
        print("\n❌ LỖI: Chưa cấu hình TELEGRAM_BOT_TOKEN trong file .env!")
        print("👉 Hướng dẫn lấy Token:")
        print("   1. Mở Telegram, tìm kiếm bot '@BotFather'")
        print("   2. Gửi lệnh: /newbot và làm theo hướng dẫn")
        print("   3. Sao chép chuỗi HTTP API Token và dán vào file .env:")
        print("      TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ\n")
        sys.exit(1)

    if not chat_id or chat_id == "your_chat_id_here":
        print("\n❌ LỖI: Chưa cấu hình TELEGRAM_CHAT_ID trong file .env!")
        print("👉 Hướng dẫn lấy Chat ID:")
        print("   1. Mở Telegram, tìm kiếm bot '@userinfobot' (hoặc '@RawDataBot')")
        print("   2. Bấm 'Start' hoặc gửi bất kỳ tin nhắn nào")
        print("   3. Bot sẽ trả về 'Id' của bạn (ví dụ: 987654321)")
        print("   4. Quan trọng: Mở bot của BẠN (vừa tạo ở bước BotFather) và bấm START (/start)")
        print("   5. Dán Chat ID vào file .env:")
        print("      TELEGRAM_CHAT_ID=987654321\n")
        sys.exit(1)

    print(f"\n[+] Token: {token[:8]}...{token[-5:]}")
    print(f"[+] Chat ID: {chat_id}")
    if thread_id:
        print(f"[+] Thread ID: {thread_id}")

    print("\n⏳ Đang gửi tin nhắn thử nghiệm tới Telegram...")

    test_message = (
        "🎉 <b>Test Thông Báo Telegram Thành Công!</b>\n\n"
        "🤖 <b>Hệ thống:</b> <code>Agent Telegram Notifier</code>\n"
        "📱 <b>Trạng thái:</b> Sẵn sàng nhận thông báo khi Claude, Grok, Antigravity hoàn thành task trên Orca!\n"
        "🚀 Chúc bạn làm việc hiệu quả cùng các Agent."
    )

    ok, res = send_telegram(token, chat_id, test_message, thread_id)

    if ok:
        print("\n" + "=" * 60)
        print("✅ THÀNH CÔNG! Đã gửi tin nhắn test tới Telegram.")
        print("Vui lòng mở ứng dụng Telegram trên điện thoại để kiểm tra thông báo!")
        print("=" * 60 + "\n")
    else:
        print("\n" + "=" * 60)
        print(f"❌ THẤT BẠI: {res}")
        print("=" * 60)
        print("\n👉 Các nguyên nhân phổ biến:")
        if "Unauthorized" in str(res):
            print(" - Token bot không hợp lệ hoặc đã bị revoke. Hãy kiểm tra lại với @BotFather.")
        elif "chat not found" in str(res) or "Forbidden" in str(res):
            print(" - Bạn CHƯA bấm 'START' (/start) với bot mới tạo của bạn trên Telegram.")
            print("   => Hãy mở bot của bạn trên Telegram và bấm START, sau đó chạy lại script này.")
        elif "wrong persistent file" in str(res) or "bad request" in str(res).lower():
            print(" - Chat ID không đúng định dạng. Hãy kiểm tra lại ID lấy từ @userinfobot.")
        else:
            print(" - Kiểm tra kết nối Internet hoặc cấu hình proxy/VPN.")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
