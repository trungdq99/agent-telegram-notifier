#!/usr/bin/env python3
"""
Google Drive Integration Module for Agent Telegram Notifier.
Handles:
1. Authentication:
   - OAuth 2.0 User Credentials (Desktop app flow with persistent token refresh)
   - Service Account JSON (Headless/server environment)
2. Resumable File Upload:
   - Uploads files of any size (especially > 10MB)
   - Supports specific destination folder (GDRIVE_FOLDER_ID)
3. Shareable Permissions:
   - Automatically sets public read access ("anyone with link can view/download")
   - Returns webViewLink and webContentLink
"""

import os
import sys
import glob
import json
import logging
import mimetypes
from pathlib import Path

# Setup logging
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "agent_notifier.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Required Drive scopes: drive.file grants access to files created/opened by the app
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def format_size(size_bytes):
    """Format bytes into human-readable string (KB, MB, GB)."""
    if size_bytes is None:
        return "N/A"
    try:
        size_bytes = float(size_bytes)
    except (ValueError, TypeError):
        return "N/A"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def find_client_secrets_file(config=None):
    """Locate client_secrets.json or credentials.json file."""
    if config and config.get("GDRIVE_CLIENT_SECRETS_FILE"):
        custom_path = os.path.expanduser(config["GDRIVE_CLIENT_SECRETS_FILE"])
        if os.path.exists(custom_path):
            return custom_path

    # Search strictly in current script directory or user app config directory
    patterns = [
        os.path.join(SCRIPT_DIR, "client_secrets.json"),
        os.path.join(SCRIPT_DIR, "credentials.json"),
        os.path.join(SCRIPT_DIR, "client_secret*.json"),
        os.path.expanduser("~/.config/agent-telegram-notifier/client_secrets.json"),
        os.path.expanduser("~/.config/agent-telegram-notifier/credentials.json")
    ]
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            return matches[0]

    return None

def get_token_file_path(config=None):
    """Get path to store or read OAuth token JSON."""
    if config and config.get("GDRIVE_TOKEN_FILE"):
        return os.path.expanduser(config["GDRIVE_TOKEN_FILE"])
    return os.path.join(SCRIPT_DIR, ".gdrive_token.json")

def get_service_account_path(config=None):
    """Get path to Service Account JSON key if configured."""
    if config and config.get("GDRIVE_SERVICE_ACCOUNT_FILE"):
        p = os.path.expanduser(config["GDRIVE_SERVICE_ACCOUNT_FILE"])
        if os.path.exists(p):
            return p
    default_sa = os.path.join(SCRIPT_DIR, "service_account.json")
    if os.path.exists(default_sa):
        return default_sa
    return None

def get_drive_service(config=None, interactive=False):
    """
    Authenticate and return Google Drive v3 Resource service.
    Supports Service Account and OAuth 2.0.
    """
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google.oauth2 import service_account
    except ImportError as e:
        raise ImportError(
            f"Thiếu thư viện Google Drive API ({e}). Vui lòng đảm bảo môi trường 'mcp_servers' có google-api-python-client và google-auth-oauthlib."
        )

    # 1. Check Service Account first if configured
    sa_path = get_service_account_path(config)
    if sa_path:
        logging.info(f"Using Google Drive Service Account: {sa_path}")
        creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
        return build("drive", "v3", credentials=creds)

    # 2. Check OAuth 2.0 User Credentials
    token_file = get_token_file_path(config)
    creds = None
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        except Exception as e:
            logging.warning(f"Could not load token from {token_file}: {e}")
            creds = None

    # Refresh expired token if possible
    if creds and creds.expired and creds.refresh_token:
        try:
            logging.info("Refreshing expired Google Drive OAuth token...")
            creds.refresh(Request())
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        except Exception as e:
            logging.warning(f"Failed to refresh Google Drive token: {e}")
            creds = None

    if creds and creds.valid:
        return build("drive", "v3", credentials=creds)

    # If creds are invalid/missing:
    if interactive:
        return setup_gdrive_oauth(config)
    else:
        client_secrets = find_client_secrets_file(config)
        hints = [
            "Chưa cấu hình hoặc token Google Drive đã hết hạn.",
            "👉 Để đăng nhập và cấp quyền Google Drive, vui lòng chạy lệnh:",
            "   /bin/sh notify.sh --setup-gdrive",
        ]
        if not client_secrets:
            hints.append("⚠️ Không tìm thấy file client_secrets.json. Hãy tải từ Google Cloud Console (OAuth Client ID) và đặt vào thư mục dự án.")
        raise PermissionError("\n".join(hints))

def setup_gdrive_oauth(config=None):
    """
    Interactive OAuth 2.0 setup for Google Drive.
    Opens browser for user authentication and stores token.
    """
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_secrets = find_client_secrets_file(config)
    if not client_secrets:
        print("\n❌ Không tìm thấy file client_secrets.json hoặc credentials.json!")
        print("👉 Hướng dẫn tạo và tải file:")
        print("   1. Truy cập: https://console.cloud.google.com/apis/credentials")
        print("   2. Chọn hoặc tạo project, bật Google Drive API (APIs & Services > Enable APIs)")
        print("   3. Tạo 'OAuth client ID' (Application type: Desktop App hoặc Web Application)")
        print("   4. Tải file JSON về và lưu tên là 'client_secrets.json' tại thư mục này:")
        print(f"      {SCRIPT_DIR}/client_secrets.json\n")
        sys.exit(1)

    print(f"\n📂 Sử dụng client secrets: {client_secrets}")
    print("⏳ Đang mở trình duyệt để xác thực tài khoản Google...")

    # Determine redirect URI port if web client
    port = 0
    try:
        with open(client_secrets, "r", encoding="utf-8") as f:
            data = json.load(f)
            web_info = data.get("web", {})
            redirect_uris = web_info.get("redirect_uris", [])
            for uri in redirect_uris:
                if "localhost:" in uri:
                    import urllib.parse
                    p = urllib.parse.urlparse(uri).port
                    if p:
                        port = p
                        break
    except Exception:
        pass

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
    if port != 0:
        creds = flow.run_local_server(port=port, prompt="consent")
    else:
        creds = flow.run_local_server(port=0, prompt="consent")

    token_file = get_token_file_path(config)
    os.makedirs(os.path.dirname(os.path.abspath(token_file)), exist_ok=True)
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    service = build("drive", "v3", credentials=creds)
    try:
        about = service.about().get(fields="user").execute()
        user_info = about.get("user", {})
        display_name = user_info.get("displayName", "N/A")
        email = user_info.get("emailAddress", "N/A")
        print("\n" + "=" * 65)
        print("✅ ĐĂNG NHẬP GOOGLE DRIVE THÀNH CÔNG!")
        print(f"👤 Người dùng : {display_name} ({email})")
        print(f"💾 Token lưu tại: {token_file}")
        print("=" * 65 + "\n")
    except Exception as e:
        print(f"✅ Đã lưu token thành công tại: {token_file} (Lưu ý: {e})")

def get_or_create_default_folder(service, folder_name="Agent Telegram Notifier"):
    """Find or create a dedicated folder in Google Drive for agent uploads."""
    try:
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]

        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        folder = service.files().create(body=metadata, fields="id").execute()
        logging.info(f"Created dedicated Google Drive folder '{folder_name}' with ID: {folder.get('id')}")
        return folder.get("id")
    except Exception as e:
        logging.warning(f"Could not get or create default folder '{folder_name}': {e}")
        return None

def upload_file_to_drive(file_path, config=None, folder_id=None, make_public=True):
    """
    Upload a local file to Google Drive using resumable upload.
    Returns:
      {
        "ok": bool,
        "file_id": str,
        "filename": str,
        "size_bytes": int,
        "size_formatted": str,
        "web_view_link": str,
        "web_content_link": str,
        "share_link": str,
        "error": str (if ok is False)
      }
    """
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File không tồn tại: {file_path}"}

    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as e:
        return {"ok": False, "error": f"Thiếu googleapiclient ({e})"}

    try:
        service = get_drive_service(config)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    file_metadata = {"name": filename}
    dest_folder = folder_id or (config.get("GDRIVE_FOLDER_ID") if config else None)
    if not dest_folder:
        dest_folder = get_or_create_default_folder(service)
    if dest_folder:
        file_metadata["parents"] = [dest_folder]

    logging.info(f"Uploading file '{filename}' ({file_size} bytes) to Google Drive...")

    try:
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        drive_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name, size, webViewLink, webContentLink"
        ).execute()

        file_id = drive_file.get("id")
        logging.info(f"File uploaded successfully to Google Drive. File ID: {file_id}")

        web_view_link = drive_file.get("webViewLink")
        web_content_link = drive_file.get("webContentLink")

        if make_public and file_id:
            try:
                service.permissions().create(
                    fileId=file_id,
                    body={"role": "reader", "type": "anyone"}
                ).execute()
                logging.info(f"Set public read permission for Drive file: {file_id}")
            except Exception as perm_err:
                logging.warning(f"Could not set public permission on Drive file {file_id}: {perm_err}")

        # Construct safe shareable link fallback
        share_link = web_view_link or f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

        return {
            "ok": True,
            "file_id": file_id,
            "filename": filename,
            "size_bytes": file_size,
            "size_formatted": format_size(file_size),
            "web_view_link": web_view_link,
            "web_content_link": web_content_link,
            "share_link": share_link
        }

    except Exception as e:
        logging.error(f"Error during Google Drive file upload: {e}")
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Google Drive CLI Helper for Agent Telegram Notifier")
    parser.add_argument("--setup", action="store_true", help="Authenticate with Google Drive via OAuth 2.0")
    parser.add_argument("--upload", help="Upload a file to Google Drive")
    parser.add_argument("--folder-id", help="Destination Google Drive folder ID")
    parser.add_argument("--env-file", help="Path to custom .env file")
    args = parser.parse_args()

    # Load config if notify.py is present
    config = {}
    try:
        from notify import load_env
        config = load_env(args.env_file)
    except Exception:
        pass

    if args.setup:
        setup_gdrive_oauth(config)
    elif args.upload:
        print(f"Đang tải lên: {args.upload}...")
        res = upload_file_to_drive(args.upload, config=config, folder_id=args.folder_id)
        if res.get("ok"):
            print("✅ Tải lên Google Drive thành công!")
            print(f"📁 Tên file: {res['filename']}")
            print(f"📊 Dung lượng: {res['size_formatted']}")
            print(f"🔗 Link: {res['share_link']}")
        else:
            print(f"❌ Tải lên thất bại: {res.get('error')}")
            sys.exit(1)
    else:
        parser.print_help()
