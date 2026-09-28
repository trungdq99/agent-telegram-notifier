#!/usr/bin/env python3
"""
Telegram Notification Tool for AI Agents (Claude, Antigravity, Grok, Codex, Cursor, etc.)
Triggers notifications via Telegram Bot when:
  1. Main agent completes a task/turn.
  2. Agent asks a question or requires user confirmation / option selection (e.g. ask_question).
Filters out subagent completions to prevent false / premature notifications.
Supports git worktree detection, project identification, and task summary.
"""

import os
import sys
import json
import time
import html
import glob
import logging
import urllib.request
import urllib.parse
import subprocess
import re
import uuid
import mimetypes
from datetime import datetime
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

# Setup logging
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "agent_notifier.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def load_env(env_path=None):
    """Load configuration from .env file."""
    if env_path is None:
        env_path = os.path.join(SCRIPT_DIR, ".env")
    
    config = {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.environ.get("TELEGRAM_CHAT_ID", ""),
        "TELEGRAM_THREAD_ID": os.environ.get("TELEGRAM_THREAD_ID", ""),
        "DEBOUNCE_SECONDS": os.environ.get("DEBOUNCE_SECONDS", "3"),
        "GDRIVE_THRESHOLD_MB": os.environ.get("GDRIVE_THRESHOLD_MB", "10"),
        "GDRIVE_CLIENT_SECRETS_FILE": os.environ.get("GDRIVE_CLIENT_SECRETS_FILE", ""),
        "GDRIVE_TOKEN_FILE": os.environ.get("GDRIVE_TOKEN_FILE", ""),
        "GDRIVE_SERVICE_ACCOUNT_FILE": os.environ.get("GDRIVE_SERVICE_ACCOUNT_FILE", ""),
        "GDRIVE_FOLDER_ID": os.environ.get("GDRIVE_FOLDER_ID", ""),
    }
    
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    config[key] = val
        except Exception as e:
            logging.error(f"Error reading .env at {env_path}: {e}")
            
    return config

def get_git_info(cwd):
    """
    Detect git project details and whether the cwd is inside a git worktree.
    Returns:
      {
        "is_git": bool,
        "is_worktree": bool,
        "project": str,
        "worktree": str or None,
        "branch": str or None
      }
    """
    def run_git(args):
        try:
            res = subprocess.check_output(
                ["git"] + args,
                cwd=cwd,
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            return res
        except Exception:
            return None

    is_work_tree = run_git(["rev-parse", "--is-inside-work-tree"])
    if is_work_tree != "true":
        return {
            "is_git": False,
            "is_worktree": False,
            "project": os.path.basename(os.path.abspath(cwd)),
            "worktree": None,
            "branch": None
        }

    git_dir = run_git(["rev-parse", "--git-dir"])
    git_common_dir = run_git(["rev-parse", "--git-common-dir"])
    toplevel = run_git(["rev-parse", "--show-toplevel"])
    branch = run_git(["branch", "--show-current"])
    if not branch:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])

    if not git_dir or not git_common_dir or not toplevel:
        return {
            "is_git": True,
            "is_worktree": False,
            "project": os.path.basename(os.path.abspath(cwd)),
            "worktree": None,
            "branch": branch
        }

    abs_git_dir = os.path.realpath(os.path.abspath(os.path.join(cwd, git_dir)))
    abs_common_dir = os.path.realpath(os.path.abspath(os.path.join(cwd, git_common_dir)))
    abs_toplevel = os.path.realpath(os.path.abspath(toplevel))

    # A worktree has its git_dir pointing to .git/worktrees/<name> rather than .git
    is_worktree = (abs_git_dir != abs_common_dir) or ("/worktrees/" in abs_git_dir)

    if is_worktree:
        main_repo_root = os.path.dirname(abs_common_dir)
        project_name = os.path.basename(main_repo_root)
        worktree_name = os.path.basename(abs_toplevel)
    else:
        project_name = os.path.basename(abs_toplevel)
        worktree_name = None

    return {
        "is_git": True,
        "is_worktree": is_worktree,
        "project": project_name,
        "worktree": worktree_name,
        "branch": branch
    }

def is_subagent(agent, payload):
    """
    Check if the event is originating from a subagent rather than the main agent.
    Returns True if this is a subagent.
    """
    raw_agent = (agent or "").strip().lower()
    event = (payload.get("hook_event_name") or payload.get("hookEventName") or payload.get("hookEvent") or "")
    
    # 1. Claude subagent check
    if event in ("SubagentStart", "SubagentStop", "SubagentEnd"):
        return True
    if payload.get("isSidechain") is True or payload.get("is_sidechain") is True:
        return True
    if payload.get("parent_session_id") or payload.get("parentUuid"):
        # If there's an explicit parentUuid or parent_session_id marking a subagent
        if event in ("Stop", "SubagentStop") or payload.get("isSidechain") or "subagent" in str(payload.get("userType", "")).lower():
            return True

    # 2. Antigravity subagent check
    if "antigravity" in raw_agent:
        # If fullyIdle is explicitly false, background tasks/subagents are still actively running!
        if payload.get("fullyIdle") is False or payload.get("fully_idle") is False:
            return True
        cid = payload.get("conversationId", "")
        if cid:
            # Check if this cid is recorded as a child subagent of any conversation
            pattern = os.path.expanduser(f"~/.gemini/antigravity-cli/brain/*/.system_generated/subagents/{cid}.json")
            if glob.glob(pattern):
                return True

    # 3. Grok subagent check
    if "grok" in raw_agent:
        if event in ("SubagentStart", "SubagentStop", "SubagentEnd"):
            return True
        if payload.get("isSidechain") is True or payload.get("is_sidechain") is True:
            return True

    return False

def check_ask_question_or_permission(payload):
    """
    Detect if the agent is calling ask_question or waiting for user confirmation.
    Returns:
      (type, data) where type is 'ask_question' or 'permission_request' or None
    """
    tool_call = payload.get("toolCall") or payload.get("tool_call") or {}
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            pass

    # Tool ask_question
    if tool_name in ("ask_question", "AskFollowupQuestion", "ask_user"):
        questions = args.get("questions", [])
        if isinstance(questions, list) and questions:
            q_items = []
            for q in questions:
                if isinstance(q, dict):
                    q_text = q.get("question", "")
                    opts = q.get("options", [])
                    q_items.append((q_text, opts))
            return "ask_question", q_items
        elif "question" in args:
            return "ask_question", [(args.get("question"), args.get("options", []))]

    # Permission / confirmation requests
    event = (payload.get("hook_event_name") or payload.get("hookEventName") or payload.get("hookEvent") or "")
    if event.lower() == "permissionrequest" or payload.get("permission_prompt"):
        reason = payload.get("reason") or tool_name or payload.get("command") or "Yêu cầu quyền thực thi"
        return "permission_request", reason

    return None, None

def extract_task_from_transcript(transcript_path):
    """Extract the last user prompt from a JSONL transcript file."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    
    import re
    last_query = ""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                # Claude format
                if data.get("type") == "user":
                    msg = data.get("message", {})
                    content = msg.get("content")
                    if isinstance(content, str) and content.strip():
                        text = content.strip()
                        if not text.startswith("<local-command-") and not text.startswith("<command_output>"):
                            last_query = text
                    elif isinstance(content, list):
                        texts = [
                            item.get("text", "") for item in content 
                            if isinstance(item, dict) and item.get("type") == "text"
                        ]
                        combined = " ".join(t.strip() for t in texts if t.strip())
                        if combined and not combined.startswith("<local-command-"):
                            last_query = combined

                # Antigravity format
                elif data.get("type") == "USER_INPUT" or data.get("source") == "USER_EXPLICIT":
                    content = data.get("content", "")
                    if isinstance(content, str) and content.strip():
                        # Extract inside <USER_REQUEST> if present
                        m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                        if m:
                            content = m.group(1).strip()
                        else:
                            content = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", content, flags=re.DOTALL)
                            content = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", content, flags=re.DOTALL)
                            content = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", content, flags=re.DOTALL)
                            content = content.strip()
                        if content:
                            last_query = content
                        
    except Exception as e:
        logging.warning(f"Error parsing transcript {transcript_path}: {e}")
        
    # Truncate clean summary
    if last_query:
        lines = [l.strip() for l in last_query.splitlines() if l.strip()]
        if lines:
            summary = lines[0]
            if len(summary) > 160:
                summary = summary[:157] + "..."
            return summary
    return ""

def check_and_set_debounce(cache_dir, key, min_seconds=3):
    """Prevent spamming multiple notifications for the same event in quick succession with atomic file locking."""
    cache_file = os.path.join(cache_dir, "last_notify.json")
    lock_file = os.path.join(cache_dir, "notify.lock")
    now = time.time()
    try:
        os.makedirs(cache_dir, exist_ok=True)
        lock_fd = None
        if fcntl:
            lock_fd = open(lock_file, "w")
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

        try:
            data = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}

            last_time = data.get(key, 0)
            if (now - last_time) < min_seconds:
                return False  # Debounced

            data[key] = now
            # Evict old entries (> 24h)
            data = {k: v for k, v in data.items() if (now - v) < 86400}
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return True
        finally:
            if fcntl and lock_fd:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    lock_fd.close()
                except Exception:
                    pass
    except Exception as e:
        logging.warning(f"Debounce error: {e}")
        return True

def send_telegram(bot_token, chat_id, message_html, thread_id=None, timeout=6.0):
    """Send HTML message via Telegram Bot API using urllib (zero dependencies)."""
    if not bot_token or not chat_id:
        return False, "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env"
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if thread_id:
        try:
            payload["message_thread_id"] = int(thread_id)
        except ValueError:
            pass
            
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "AgentTelegramNotifier/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            if res_json.get("ok"):
                return True, "Success"
            return False, res_json.get("description", "Unknown Telegram API error")
    except Exception as e:
        return False, str(e)

def build_multipart(fields, files):
    """
    Build multipart/form-data payload in pure Python standard library.
    fields: dict {name: str_value}
    files: list of tuples (field_name, file_path)
    Returns: (content_type_header, body_bytes)
    """
    boundary = f"----TelegramBoundary{uuid.uuid4().hex}"
    parts = []
    for k, v in fields.items():
        if v is not None and v != "":
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
    for field_name, file_path in files:
        filename = os.path.basename(file_path)
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n".encode("utf-8")
        )
        parts.append(data)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return f"multipart/form-data; boundary={boundary}", b"".join(parts)

def build_gdrive_file_message(filename, size_formatted, drive_link, caption=""):
    """Build clean, formatted HTML notification message when a large file is uploaded to Google Drive."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    lines = [
        "☁️ <b>File Dung Lượng Lớn Đã Tải Lên Google Drive!</b>",
        "",
        f"📁 <b>Tên file:</b> <code>{html.escape(filename)}</code>",
        f"📊 <b>Kích thước:</b> <code>{html.escape(size_formatted)}</code> <i>(Vượt ngưỡng 10MB)</i>",
        f"🔗 <b>Link Google Drive:</b> <a href=\"{drive_link}\">Xem và tải file tại đây</a>",
    ]
    if caption:
        lines.append(f"📝 <b>Mô tả:</b> {caption}")
    lines.append(f"⏰ <b>Thời gian:</b> {now_str}")
    return "\n".join(lines)

def send_telegram_file(bot_token, chat_id, file_path, file_type="document", caption="", thread_id=None, timeout=15.0, config=None, force_gdrive=False, gdrive_threshold=None):
    """
    Send photo or document via Telegram Bot API or Google Drive for large files (> 10MB).
    - If file_size > threshold (default 10MB) or force_gdrive is True:
        Uploads file to Google Drive and sends formatted Telegram message with shareable link.
    - Else:
        Dispatches file directly via Telegram Bot API (sendPhoto or sendDocument).
    """
    if not bot_token or not chat_id:
        return False, "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID trong .env"
    if not os.path.exists(file_path):
        return False, f"File không tồn tại: {file_path}"

    file_size = os.path.getsize(file_path)

    # Determine threshold (default 10 MB)
    if gdrive_threshold is not None:
        threshold_mb = float(gdrive_threshold)
    elif config and config.get("GDRIVE_THRESHOLD_MB"):
        try:
            threshold_mb = float(config.get("GDRIVE_THRESHOLD_MB"))
        except (ValueError, TypeError):
            threshold_mb = 10.0
    else:
        threshold_mb = 10.0

    threshold_bytes = int(threshold_mb * 1024 * 1024)

    # Route to Google Drive if size exceeds threshold or forced
    if force_gdrive or file_size > threshold_bytes:
        logging.info(
            f"File '{file_path}' ({file_size} bytes) exceeds threshold ({threshold_bytes} bytes). "
            f"Uploading to Google Drive..."
        )
        try:
            from gdrive import upload_file_to_drive, format_size
            dest_folder = config.get("GDRIVE_FOLDER_ID") if config else None
            res = upload_file_to_drive(file_path, config=config, folder_id=dest_folder)
            if not res.get("ok"):
                err_msg = res.get("error", "Unknown Google Drive error")
                logging.error(f"Google Drive upload failed: {err_msg}")
                return False, f"Upload Google Drive thất bại: {err_msg}"

            drive_link = res.get("share_link") or res.get("web_view_link")
            size_formatted = res.get("size_formatted", format_size(file_size))
            filename = res.get("filename", os.path.basename(file_path))

            msg_html = build_gdrive_file_message(filename, size_formatted, drive_link, caption)
            return send_telegram(bot_token, chat_id, msg_html, thread_id=thread_id, timeout=timeout)
        except Exception as e:
            logging.exception(f"Error handling Google Drive upload: {e}")
            return False, f"Lỗi Google Drive: {e}"

    lower_path = file_path.lower()
    # Telegram photo constraints: must be photo format and <= 10MB
    if file_type == "photo":
        if lower_path.endswith(".svg") or file_size > 10 * 1024 * 1024:
            file_type = "document"

    endpoint = "sendPhoto" if file_type == "photo" else "sendDocument"
    field_file = "photo" if file_type == "photo" else "document"
    url = f"https://api.telegram.org/bot{bot_token}/{endpoint}"

    fields = {
        "chat_id": str(chat_id),
        "parse_mode": "HTML"
    }
    if thread_id:
        try:
            fields["message_thread_id"] = str(int(thread_id))
        except ValueError:
            pass

    if caption:
        if len(caption) > 1020:
            caption = caption[:1017] + "..."
        fields["caption"] = caption

    try:
        content_type, body = build_multipart(fields, [(field_file, file_path)])
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": content_type, "User-Agent": "AgentTelegramNotifier/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            res_json = json.loads(body)
            if res_json.get("ok"):
                return True, "Success"
            return False, res_json.get("description", "Unknown Telegram API error")
    except Exception as e:
        return False, str(e)

def format_agent_name(name):
    """Normalize agent names with readable titles and emojis."""
    raw = (name or "Unknown").strip().lower()
    mapping = {
        "claude": ("Claude", "🟣"),
        "antigravity": ("Antigravity", "🟢"),
        "grok": ("Grok", "⚡"),
        "cursor": ("Cursor", "🔵"),
        "codex": ("Codex", "🟠"),
        "gemini": ("Gemini", "✨")
    }
    for key, (display, emoji) in mapping.items():
        if key in raw:
            return f"{emoji} {display}"
    return f"🤖 {name.title()}"

def build_task_completed_message(agent_display, project_name, is_worktree, worktree_name, branch_name, task_text):
    """Build clean, formatted HTML notification message for task completion."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    lines = [
        "🎯 <b>Agent Đã Triển Khai Xong Task!</b>",
        "",
        f"<b>Agent:</b> {html.escape(agent_display)}",
        f"📁 <b>Dự án:</b> <b>{html.escape(project_name)}</b>",
    ]
    
    if is_worktree and worktree_name:
        branch_desc = f" (nhánh <code>{html.escape(branch_name)}</code>)" if branch_name else ""
        lines.append(f"🌿 <b>Worktree:</b> <code>{html.escape(worktree_name)}</code>{branch_desc}")
    else:
        branch_desc = f"<code>{html.escape(branch_name)}</code>" if branch_name else "main"
        lines.append(f"🌿 <b>Nhánh:</b> {branch_desc} <i>(nhánh chính)</i>")
        
    if task_text:
        lines.append(f"📝 <b>Task:</b> <i>{html.escape(task_text)}</i>")
        
    lines.append(f"⏰ <b>Thời gian:</b> {now_str}")
    
    return "\n".join(lines)

def build_ask_question_message(agent_display, project_name, is_worktree, worktree_name, branch_name, q_items):
    """Build clean, formatted HTML notification message when an agent asks a question / choices."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    lines = [
        "❓ <b>Agent Cần Bạn Trả Lời / Chọn Phương Án!</b>",
        "",
        f"<b>Agent:</b> {html.escape(agent_display)}",
        f"📁 <b>Dự án:</b> <b>{html.escape(project_name)}</b>",
    ]
    
    if is_worktree and worktree_name:
        branch_desc = f" (nhánh <code>{html.escape(branch_name)}</code>)" if branch_name else ""
        lines.append(f"🌿 <b>Worktree:</b> <code>{html.escape(worktree_name)}</code>{branch_desc}")
    else:
        branch_desc = f"<code>{html.escape(branch_name)}</code>" if branch_name else "main"
        lines.append(f"🌿 <b>Nhánh:</b> {branch_desc} <i>(nhánh chính)</i>")
        
    lines.append("")
    for q_text, opts in q_items:
        lines.append(f"<b>Câu hỏi:</b> <i>{html.escape(q_text)}</i>")
        if opts:
            lines.append("<b>Các phương án lựa chọn:</b>")
            for idx, opt in enumerate(opts, 1):
                lines.append(f"  {idx}. {html.escape(str(opt))}")
        lines.append("")

    lines.append(f"⏰ <b>Thời gian:</b> {now_str}")
    return "\n".join(lines)

def build_permission_message(agent_display, project_name, is_worktree, worktree_name, branch_name, operation_text):
    """Build notification message when an agent requires user permission."""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    lines = [
        "⚠️ <b>Agent Cần Xác Nhận Quyền Thực Thi!</b>",
        "",
        f"<b>Agent:</b> {html.escape(agent_display)}",
        f"📁 <b>Dự án:</b> <b>{html.escape(project_name)}</b>",
    ]
    
    if is_worktree and worktree_name:
        branch_desc = f" (nhánh <code>{html.escape(branch_name)}</code>)" if branch_name else ""
        lines.append(f"🌿 <b>Worktree:</b> <code>{html.escape(worktree_name)}</code>{branch_desc}")
    else:
        branch_desc = f"<code>{html.escape(branch_name)}</code>" if branch_name else "main"
        lines.append(f"🌿 <b>Nhánh:</b> {branch_desc} <i>(nhánh chính)</i>")
        
    lines.append(f"⚙️ <b>Thao tác:</b> <code>{html.escape(operation_text)}</code>")
    lines.append(f"⏰ <b>Thời gian:</b> {now_str}")
    return "\n".join(lines)

CURRENT_IS_TOOL = any("tool" in arg.lower() for arg in sys.argv)

def finish(code=0):
    """Output valid JSON response for agent hooks and exit."""
    if CURRENT_IS_TOOL:
        print('{"decision": "allow"}')
    else:
        print('{}')
    sys.exit(code)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Send Telegram notification when an agent finishes a task or asks questions.")
    parser.add_argument("--agent", help="Agent name (claude, grok, antigravity, codex, cursor, etc.)")
    parser.add_argument("--event", help="Hook event name (Stop, SessionEnd, PreToolUse, etc.)")
    parser.add_argument("--cwd", help="Working directory of the project")
    parser.add_argument("--task", help="Explicit task description")
    parser.add_argument("--test", action="store_true", help="Send a test notification immediately")
    parser.add_argument("--dry-run", action="store_true", help="Print message without sending")
    parser.add_argument("--env-file", help="Path to custom .env file")
    parser.add_argument("--send-photo", help="Send a photo directly via Telegram")
    parser.add_argument("--send-file", "--send-doc", dest="send_file", help="Send a document or file directly via Telegram")
    parser.add_argument("--caption", default="", help="Caption for photo or file")
    parser.add_argument("--setup-gdrive", action="store_true", help="Interactive OAuth 2.0 setup for Google Drive")
    parser.add_argument("--force-gdrive", action="store_true", help="Force upload to Google Drive regardless of file size")
    parser.add_argument("--gdrive-threshold", type=float, help="File size threshold in MB for Google Drive upload (default: 10)")
    args = parser.parse_args()

    config = load_env(args.env_file)
    bot_token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")
    thread_id = config.get("TELEGRAM_THREAD_ID")
    min_interval = float(config.get("DEBOUNCE_SECONDS", "3"))

    # Interactive Google Drive OAuth setup
    if args.setup_gdrive:
        try:
            from gdrive import setup_gdrive_oauth
            setup_gdrive_oauth(config)
            sys.exit(0)
        except Exception as e:
            print(f"❌ Lỗi cấu hình Google Drive: {e}")
            sys.exit(1)

    # Direct photo sending mode
    if args.send_photo:
        caption = args.caption
        if not caption:
            caption = f"🖼️ <b>{html.escape(os.path.basename(args.send_photo))}</b>"
        ok, res = send_telegram_file(
            bot_token, chat_id, args.send_photo,
            file_type="photo", caption=caption, thread_id=thread_id,
            config=config, force_gdrive=args.force_gdrive, gdrive_threshold=args.gdrive_threshold
        )
        if ok:
            print(f"✅ Gửi ảnh thành công: {args.send_photo}")
            sys.exit(0)
        else:
            print(f"❌ Gửi ảnh thất bại: {res}")
            sys.exit(1)

    # Direct document sending mode
    if args.send_file:
        caption = args.caption
        if not caption:
            caption = f"📄 <b>{html.escape(os.path.basename(args.send_file))}</b>"
        ok, res = send_telegram_file(
            bot_token, chat_id, args.send_file,
            file_type="document", caption=caption, thread_id=thread_id,
            config=config, force_gdrive=args.force_gdrive, gdrive_threshold=args.gdrive_threshold
        )
        if ok:
            print(f"✅ Gửi file thành công: {args.send_file}")
            sys.exit(0)
        else:
            print(f"❌ Gửi file thất bại: {res}")
            sys.exit(1)

    # Test mode
    if args.test:
        print("Đang kiểm tra kết nối Telegram...")
        test_msg = (
            "🔔 <b>Test Thông Báo Telegram Bot Thành Công!</b>\n\n"
            "Công cụ <b>Agent Telegram Notifier</b> đã được cấu hình chính xác và sẵn sàng nhận thông báo từ các agent (Claude, Grok, Antigravity, Orca)."
        )
        ok, res = send_telegram(bot_token, chat_id, test_msg, thread_id)
        if ok:
            print("✅ Gửi tin nhắn thử nghiệm thành công! Vui lòng kiểm tra Telegram của bạn.")
            sys.exit(0)
        else:
            print(f"❌ Gửi tin nhắn thất bại: {res}")
            sys.exit(1)

    # Read stdin payload if provided
    raw_stdin = ""
    payload = {}
    if not sys.stdin.isatty():
        try:
            raw_stdin = sys.stdin.read()
            if raw_stdin.strip():
                payload = json.loads(raw_stdin)
        except Exception as e:
            logging.debug(f"Could not parse stdin as JSON: {e}")

    # Determine agent
    agent = args.agent
    if not agent:
        if os.environ.get("ORCA_ANTIGRAVITY_EVENT"):
            agent = "antigravity"
        elif os.environ.get("GROK_HOME") or os.environ.get("GROK_HOOK_EVENT"):
            agent = "grok"
        elif payload.get("source") in ("claude", "grok", "antigravity", "codex", "cursor", "gemini"):
            agent = payload.get("source")
        elif payload.get("agentType"):
            agent = payload.get("agentType")
        elif payload.get("agent"):
            agent = payload.get("agent")
        else:
            agent = "AI Agent"

    # Determine event
    event = args.event
    if not event:
        if os.environ.get("ORCA_ANTIGRAVITY_EVENT"):
            event = os.environ.get("ORCA_ANTIGRAVITY_EVENT")
        elif payload.get("hook_event_name"):
            event = payload.get("hook_event_name")
        elif payload.get("hookEventName"):
            event = payload.get("hookEventName")
        elif payload.get("hookEvent"):
            event = payload.get("hookEvent")
        elif payload.get("type"):
            event = payload.get("type")
        elif payload.get("event"):
            event = payload.get("event")

    cid = payload.get("conversationId", "")
    global CURRENT_IS_TOOL
    if "tool" in (event or "").lower():
        CURRENT_IS_TOOL = True
    logging.info(f"Received hook: agent='{agent}', event='{event}', cid='{cid}'")

    # 1. Check if this is a subagent completion -> IGNORE if subagent!
    if is_subagent(agent, payload):
        logging.info(f"Ignored subagent event: {event} for agent: {agent} (cid={cid})")
        finish(0)

    # 2. Check if agent is asking a question or requesting user confirmation
    ask_type, ask_data = check_ask_question_or_permission(payload)

    completion_events = ("stop", "sessionend", "done", "completed")
    normalized_event = (event or "").strip().lower()

    # Determine if we should notify:
    # Option A: Ask question / permission
    # Option B: Main agent completion
    is_completion = any(comp in normalized_event for comp in completion_events)
    is_interactive = (ask_type is not None)

    if not is_completion and not is_interactive:
        logging.info(f"Ignoring non-actionable event: '{event}' for agent: '{agent}'")
        finish(0)

    # Determine cwd
    cwd = args.cwd or payload.get("cwd")
    if not cwd and os.environ.get("ORCA_WORKTREE_ID"):
        worktree_id = os.environ.get("ORCA_WORKTREE_ID")
        if "::" in worktree_id:
            cwd = worktree_id.split("::", 1)[1]
    if not cwd and payload.get("workspacePaths") and len(payload["workspacePaths"]) > 0:
        cwd = payload["workspacePaths"][0]
    if not cwd:
        cwd = os.getcwd()

    # Get git information
    git_info = get_git_info(cwd)
    project_name = git_info["project"]
    is_worktree = git_info["is_worktree"]
    worktree_name = git_info["worktree"]
    branch_name = git_info["branch"]

    agent_display = format_agent_name(agent)
    cache_dir = os.path.join(SCRIPT_DIR, ".cache")

    # Handle Interactive Question / Permission
    if is_interactive:
        if ask_type == "ask_question":
            debounce_key = f"ask:{agent}:{project_name}:{worktree_name or branch_name}"
            if not check_and_set_debounce(cache_dir, debounce_key, min_seconds=min_interval):
                finish(0)
            msg_html = build_ask_question_message(
                agent_display, project_name, is_worktree, worktree_name, branch_name, ask_data
            )
        else: # permission_request
            debounce_key = f"perm:{agent}:{project_name}:{worktree_name or branch_name}"
            if not check_and_set_debounce(cache_dir, debounce_key, min_seconds=min_interval):
                finish(0)
            msg_html = build_permission_message(
                agent_display, project_name, is_worktree, worktree_name, branch_name, ask_data
            )

    # Handle Task Completed
    else:
        debounce_key = f"done:{agent}:{project_name}:{worktree_name or branch_name or 'main'}"
        if not check_and_set_debounce(cache_dir, debounce_key, min_seconds=min_interval):
            logging.info(f"Skipping debounced notification for key: {debounce_key}")
            finish(0)

        # Resolve transcript path
        transcript_path = payload.get("transcript_path") or payload.get("transcriptPath")
        if not transcript_path and payload.get("providerSession"):
            transcript_path = payload.get("providerSession", {}).get("transcriptPath")
        if not transcript_path and "antigravity" in str(agent).lower():
            if cid:
                auto_path = os.path.expanduser(f"~/.gemini/antigravity-cli/brain/{cid}/.system_generated/logs/transcript.jsonl")
                if os.path.exists(auto_path):
                    transcript_path = auto_path

        # Extract task
        task_text = args.task
        if not task_text:
            task_text = payload.get("task") or payload.get("prompt") or payload.get("query") or payload.get("description")
        if not task_text and transcript_path:
            task_text = extract_task_from_transcript(transcript_path)

        msg_html = build_task_completed_message(
            agent_display=agent_display,
            project_name=project_name,
            is_worktree=is_worktree,
            worktree_name=worktree_name,
            branch_name=branch_name,
            task_text=task_text
        )

    if args.dry_run:
        print("--- [DRY RUN MESSAGE] ---")
        print(msg_html)
        print("-------------------------")
        sys.exit(0)

    # Send message
    ok, res = send_telegram(bot_token, chat_id, msg_html, thread_id)
    if ok:
        logging.info(f"Notification sent successfully: {debounce_key}")
    else:
        logging.error(f"Failed to send notification: {res}")

    finish(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        logging.exception(f"Unhandled fatal error in notify.py: {err}")
        if CURRENT_IS_TOOL or any("tool" in arg.lower() for arg in sys.argv):
            print('{"decision": "allow"}')
        else:
            print('{}')
        sys.exit(0)
