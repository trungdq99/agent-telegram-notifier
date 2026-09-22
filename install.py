#!/usr/bin/env python3
"""
Installer script for Agent Telegram Notifier.
Supports:
1. Native Agent Hooks (Persistent across Orca restarts and works for standalone CLIs):
   - Antigravity (~/.gemini/config/hooks.json)
   - Claude Code (~/.claude/settings.json)
   - Grok (~/.grok/hooks/agent-telegram-notifier.json)
2. Orca Relay Hooks (~/.orca/agent-hooks/*.sh) with backups (.bak)
"""

import os
import sys
import json
import shutil
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOTIFY_SH = os.path.join(SCRIPT_DIR, "notify.sh")
HOOKS_DIR = os.path.expanduser("~/.orca/agent-hooks")

ORCA_TARGET_HOOKS = {
    "antigravity": os.path.join(HOOKS_DIR, "antigravity-hook.sh"),
    "claude": os.path.join(HOOKS_DIR, "claude-hook.sh"),
    "grok": os.path.join(HOOKS_DIR, "grok-hook.sh"),
    "cursor": os.path.join(HOOKS_DIR, "cursor-hook.sh"),
    "codex": os.path.join(HOOKS_DIR, "codex-hook.sh"),
    "gemini": os.path.join(HOOKS_DIR, "gemini-hook.sh"),
}

START_MARKER = "# === AGENT TELEGRAM NOTIFIER HOOK START ==="
END_MARKER = "# === AGENT TELEGRAM NOTIFIER HOOK END ==="

# -------------------------------------------------------------
# 1. Antigravity Native Hook (~/.gemini/config/hooks.json)
# -------------------------------------------------------------
GEMINI_HOOKS_PATH = os.path.expanduser("~/.gemini/config/hooks.json")
ANTIGRAVITY_NAMESPACE = "agent-telegram-notifier"

def get_antigravity_hook_def():
    stop_cmd = f'if [ -f "{NOTIFY_SH}" ]; then /bin/sh "{NOTIFY_SH}" --agent "antigravity" --event "Stop"; else printf \'%s\\n\' \'{{"decision":""}}\'; {{ command -p cat 2>/dev/null || cat; }} >/dev/null 2>&1 || :; fi'
    tool_cmd = f'if [ -f "{NOTIFY_SH}" ]; then /bin/sh "{NOTIFY_SH}" --agent "antigravity" --event "PreToolUse"; else printf \'%s\\n\' \'{{"decision":"allow"}}\'; {{ command -p cat 2>/dev/null || cat; }} >/dev/null 2>&1 || :; fi'
    return {
        "Stop": [
            {
                "type": "command",
                "command": stop_cmd,
                "timeout": 15
            }
        ],
        "PreToolUse": [
            {
                "matcher": "ask_question",
                "hooks": [
                    {
                        "type": "command",
                        "command": tool_cmd,
                        "timeout": 15
                    }
                ]
            }
        ]
    }

def is_antigravity_native_installed():
    if not os.path.exists(GEMINI_HOOKS_PATH):
        return False
    try:
        with open(GEMINI_HOOKS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ANTIGRAVITY_NAMESPACE in data
    except Exception:
        return False

def install_antigravity_native():
    try:
        os.makedirs(os.path.dirname(GEMINI_HOOKS_PATH), exist_ok=True)
        data = {}
        if os.path.exists(GEMINI_HOOKS_PATH):
            with open(GEMINI_HOOKS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[ANTIGRAVITY_NAMESPACE] = get_antigravity_hook_def()
        with open(GEMINI_HOOKS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Đã cài đặt Native Hook cho Antigravity vào: {GEMINI_HOOKS_PATH}")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi cài đặt Native Hook Antigravity: {e}")
        return False

def uninstall_antigravity_native():
    if not os.path.exists(GEMINI_HOOKS_PATH):
        return True
    try:
        with open(GEMINI_HOOKS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if ANTIGRAVITY_NAMESPACE in data:
            del data[ANTIGRAVITY_NAMESPACE]
            with open(GEMINI_HOOKS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  🗑️  Đã gỡ bỏ Native Hook Antigravity khỏi: {GEMINI_HOOKS_PATH}")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi gỡ bỏ Native Hook Antigravity: {e}")
        return False

# -------------------------------------------------------------
# 2. Claude Native Hook (~/.claude/settings.json)
# -------------------------------------------------------------
CLAUDE_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
CLAUDE_EVENTS = ["Stop", "SessionEnd", "PermissionRequest"]

def is_claude_native_installed():
    if not os.path.exists(CLAUDE_SETTINGS_PATH):
        return False
    try:
        with open(CLAUDE_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        hooks = data.get("hooks", {})
        for event in CLAUDE_EVENTS:
            event_hooks = hooks.get(event, [])
            for group in event_hooks:
                for h in group.get("hooks", []):
                    if NOTIFY_SH in h.get("command", ""):
                        return True
        return False
    except Exception:
        return False

def install_claude_native():
    if not os.path.exists(CLAUDE_SETTINGS_PATH):
        print(f"  ⚠️  Bỏ qua Claude Native: Không tìm thấy {CLAUDE_SETTINGS_PATH}")
        return False
    try:
        with open(CLAUDE_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "hooks" not in data or not isinstance(data["hooks"], dict):
            data["hooks"] = {}

        for event in CLAUDE_EVENTS:
            if event not in data["hooks"] or not isinstance(data["hooks"][event], list):
                data["hooks"][event] = []
            
            # Check if already registered
            already = False
            for group in data["hooks"][event]:
                for h in group.get("hooks", []):
                    if NOTIFY_SH in h.get("command", ""):
                        already = True
                        break
                if already:
                    break

            if not already:
                cmd = f'if [ -f "{NOTIFY_SH}" ]; then /bin/sh "{NOTIFY_SH}" --agent "claude" --event "{event}"; else {{ command -p cat 2>/dev/null || cat; }} >/dev/null 2>&1 || :; printf \'{{\\n}}\'; fi'
                data["hooks"][event].append({
                    "hooks": [
                        {
                            "type": "command",
                            "command": cmd,
                            "timeout": 15
                        }
                    ]
                })

        with open(CLAUDE_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Đã cài đặt Native Hook cho Claude vào: {CLAUDE_SETTINGS_PATH}")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi cài đặt Native Hook Claude: {e}")
        return False

def uninstall_claude_native():
    if not os.path.exists(CLAUDE_SETTINGS_PATH):
        return True
    try:
        with open(CLAUDE_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        hooks = data.get("hooks", {})
        changed = False
        for event in CLAUDE_EVENTS:
            if event in hooks and isinstance(hooks[event], list):
                new_groups = []
                for group in hooks[event]:
                    inner = group.get("hooks", [])
                    filtered = [h for h in inner if NOTIFY_SH not in h.get("command", "")]
                    if filtered:
                        new_groups.append({"hooks": filtered})
                    else:
                        changed = True
                hooks[event] = new_groups

        if changed:
            with open(CLAUDE_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  🗑️  Đã gỡ bỏ Native Hook Claude khỏi: {CLAUDE_SETTINGS_PATH}")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi gỡ bỏ Native Hook Claude: {e}")
        return False

# -------------------------------------------------------------
# 3. Grok Native Hook (~/.grok/hooks/agent-telegram-notifier.json)
# -------------------------------------------------------------
GROK_DIR = os.path.expanduser("~/.grok")
GROK_HOOK_FILE = os.path.join(GROK_DIR, "hooks", "agent-telegram-notifier.json")

def is_grok_native_installed():
    return os.path.exists(GROK_HOOK_FILE)

def install_grok_native():
    if not os.path.exists(GROK_DIR):
        return False
    try:
        os.makedirs(os.path.dirname(GROK_HOOK_FILE), exist_ok=True)
        grok_def = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": f'if [ -f "{NOTIFY_SH}" ]; then /bin/sh "{NOTIFY_SH}" --agent "grok" --event "Stop"; else {{ command -p cat 2>/dev/null || cat; }} >/dev/null 2>&1 || :; fi',
                                "timeout": 15
                            }
                        ]
                    }
                ],
                "SessionEnd": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": f'if [ -f "{NOTIFY_SH}" ]; then /bin/sh "{NOTIFY_SH}" --agent "grok" --event "SessionEnd"; else {{ command -p cat 2>/dev/null || cat; }} >/dev/null 2>&1 || :; fi',
                                "timeout": 15
                            }
                        ]
                    }
                ]
            }
        }
        with open(GROK_HOOK_FILE, "w", encoding="utf-8") as f:
            json.dump(grok_def, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Đã cài đặt Native Hook cho Grok vào: {GROK_HOOK_FILE}")
        return True
    except Exception as e:
        print(f"  ❌ Lỗi cài đặt Native Hook Grok: {e}")
        return False

def uninstall_grok_native():
    if os.path.exists(GROK_HOOK_FILE):
        try:
            os.remove(GROK_HOOK_FILE)
            print(f"  🗑️  Đã gỡ bỏ Native Hook Grok: {GROK_HOOK_FILE}")
        except Exception as e:
            print(f"  ❌ Lỗi gỡ bỏ Native Hook Grok: {e}")
    return True

# -------------------------------------------------------------
# 4. Orca Relay Hooks (~/.orca/agent-hooks/*.sh)
# -------------------------------------------------------------
def generate_orca_hook_code(agent_name):
    lines = [START_MARKER]
    if agent_name == "antigravity":
        lines.extend([
            f'if [ -f "{NOTIFY_SH}" ]; then',
            f'  printf \'%s\' "$payload" | /bin/sh "{NOTIFY_SH}" --agent "antigravity" --event "${{ORCA_ANTIGRAVITY_EVENT:-Stop}}" >/dev/null 2>&1 &',
            f'fi',
        ])
    elif agent_name == "grok":
        lines.extend([
            f'if [ -f "{NOTIFY_SH}" ]; then',
            f'  printf \'%s\' "$payload" | /bin/sh "{NOTIFY_SH}" --agent "grok" --event "${{GROK_HOOK_EVENT:-Stop}}" >/dev/null 2>&1 &',
            f'fi',
        ])
    else:
        lines.extend([
            f'if [ -f "{NOTIFY_SH}" ]; then',
            f'  printf \'%s\' "$payload" | /bin/sh "{NOTIFY_SH}" --agent "{agent_name}" >/dev/null 2>&1 &',
            f'fi',
        ])

    # Subagent filter to prevent Orca from receiving subagent completion events
    if agent_name == "claude":
        lines.extend([
            'case "$payload" in',
            '  *\'"SubagentStart"\'*|*\'"SubagentStop"\'*|*\'"SubagentEnd"\'*|*\'"isSidechain":true\'*|*\'"isSidechain": true\'*)',
            '    exit 0',
            '    ;;',
            'esac',
        ])
    elif agent_name == "grok":
        lines.extend([
            'case "$payload" in',
            '  *\'"SubagentStart"\'*|*\'"SubagentStop"\'*|*\'"SubagentEnd"\'*)',
            '    exit 0',
            '    ;;',
            'esac',
        ])
    elif agent_name == "antigravity":
        lines.extend([
            'case "$payload" in',
            '  *\'"fullyIdle":false\'*|*\'"fullyIdle": false\'*)',
            '    exit 0',
            '    ;;',
            'esac',
            '_cid=$(printf \'%s\' "$payload" | sed -n \'s/.*"conversationId":[ ]*"\\([^"]*\\)".*/\\1/p\')',
            'if [ -n "$_cid" ]; then',
            '  if ls "$HOME/.gemini/antigravity-cli/brain/"*/.system_generated/subagents/"$_cid.json" >/dev/null 2>&1; then',
            '    exit 0',
            '  fi',
            'fi',
        ])

    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"

def is_orca_hook_installed(filepath):
    if not os.path.exists(filepath):
        return False
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return START_MARKER in content

def install_orca_hook(agent_name, filepath):
    if not os.path.exists(filepath):
        print(f"  ⚠️  Bỏ qua {agent_name}: không tìm thấy file {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARKER in content:
        uninstall_orca_hook(agent_name, filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

    backup_file = filepath + ".bak"
    if not os.path.exists(backup_file):
        shutil.copy2(filepath, backup_file)
        print(f"  💾 Đã sao lưu bản gốc sang {backup_file}")

    hook_code = generate_orca_hook_code(agent_name)

    lines = content.splitlines(keepends=True)
    insert_idx = -1

    for i, line in enumerate(lines):
        if 'if [ -z "$payload" ]' in line or 'if [ -z "$payload" ];' in line:
            for j in range(i, min(i + 15, len(lines))):
                if lines[j].strip() == "fi":
                    insert_idx = j + 1
                    break
            if insert_idx != -1:
                break

    if insert_idx == -1:
        for i, line in enumerate(lines):
            if "payload=" in line:
                insert_idx = i + 1
                break

    if insert_idx == -1:
        insert_idx = 1 if len(lines) > 0 and lines[0].startswith("#!") else 0

    lines.insert(insert_idx, hook_code)
    
    new_content = "".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    os.chmod(filepath, 0o755)
    print(f"  ✅ Đã cài đặt Orca relay hook vào: {filepath}")
    return True

def uninstall_orca_hook(agent_name, filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content:
        return True

    lines = content.splitlines(keepends=True)
    new_lines = []
    in_block = False
    for line in lines:
        if START_MARKER in line:
            in_block = True
            continue
        if END_MARKER in line:
            in_block = False
            continue
        if not in_block:
            new_lines.append(line)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("".join(new_lines))

    print(f"  🗑️  Đã gỡ bỏ Orca relay hook khỏi: {filepath}")
    return True

# -------------------------------------------------------------
# Summary & CLI
# -------------------------------------------------------------
def show_status():
    print("\n" + "=" * 65)
    print("🌟 1. AGENT NATIVE HOOKS (Bền vững - Không bị Orca ghi đè khi restart)")
    print("=" * 65)
    ag_stat = "✅ ĐÃ CÀI ĐẶT" if is_antigravity_native_installed() else "❌ CHƯA CÀI ĐẶT"
    print(f"  Antigravity    : {ag_stat} (~/.gemini/config/hooks.json)")
    
    cl_stat = "✅ ĐÃ CÀI ĐẶT" if is_claude_native_installed() else "❌ CHƯA CÀI ĐẶT"
    print(f"  Claude         : {cl_stat} (~/.claude/settings.json)")
    
    if os.path.exists(GROK_DIR):
        gr_stat = "✅ ĐÃ CÀI ĐẶT" if is_grok_native_installed() else "❌ CHƯA CÀI ĐẶT"
        print(f"  Grok           : {gr_stat} (~/.grok/hooks/agent-telegram-notifier.json)")

    print("\n" + "=" * 65)
    print("🔄 2. ORCA RELAY HOOKS (Bổ trợ - Tự động bị Orca reset nếu Orca khởi động lại)")
    print("=" * 65)
    for agent, path in ORCA_TARGET_HOOKS.items():
        exists = os.path.exists(path)
        installed = is_orca_hook_installed(path) if exists else False
        if agent in ("antigravity", "claude", "grok") and not installed:
            status_str = "⏭️  BỎ QUA (Đã dùng Native Hook)"
        elif installed:
            status_str = "✅ ĐÃ CÀI ĐẶT"
        elif exists:
            status_str = "❌ CHƯA CÀI ĐẶT"
        else:
            status_str = "⚠️ KHÔNG TÌM THẤY FILE"
        print(f"  {agent.title():<15}: {status_str} ({os.path.basename(path)})")
    print("=" * 65 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Install/Uninstall Telegram Notifier hooks for AI agents.")
    parser.add_argument("--install", action="store_true", help="Install hooks into both native agents and Orca")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall all hooks")
    parser.add_argument("--status", action="store_true", help="Show current installation status")
    args = parser.parse_args()

    if args.uninstall:
        print("\n⏳ Đang gỡ bỏ Telegram Notifier hooks...")
        uninstall_antigravity_native()
        uninstall_claude_native()
        uninstall_grok_native()
        for agent, path in ORCA_TARGET_HOOKS.items():
            uninstall_orca_hook(agent, path)
        print("\n✅ Đã hoàn tất gỡ bỏ hooks.")
        show_status()
    elif args.install:
        print("\n⏳ Đang cài đặt Native Hooks cho các Agent (Bền vững across restarts)...")
        install_antigravity_native()
        install_claude_native()
        install_grok_native()

        print("\n⏳ Cấu hình Orca Relay hooks (~/.orca/agent-hooks/)...")
        # Các agent đã có Native Hooks (Antigravity, Claude, Grok) đã gọi notify.sh trực tiếp
        # từ cấu hình gốc của chúng. Ta gỡ bỏ đoạn hook trong ~/.orca/agent-hooks/*.sh của chúng
        # để tránh bị gọi 2 lần (duplicate notifications).
        for agent in ("antigravity", "claude", "grok"):
            path = ORCA_TARGET_HOOKS.get(agent)
            if path and os.path.exists(path):
                uninstall_orca_hook(agent, path)

        # Cài đặt Orca relay hook cho các agent còn lại chưa có Native Hook (cursor, codex, gemini)
        for agent in ("cursor", "codex", "gemini"):
            path = ORCA_TARGET_HOOKS.get(agent)
            if path:
                install_orca_hook(agent, path)

        print("\n✅ Đã hoàn tất cài đặt hooks.")
        show_status()
    else:
        show_status()
        print("💡 Cách sử dụng:")
        print("   python3 install.py --install     : Cài đặt hook vào tất cả các agent (Native + Orca)")
        print("   python3 install.py --uninstall   : Gỡ bỏ hook khỏi tất cả các agent")
        print("   python3 install.py --status      : Xem trạng thái hiện tại\n")

if __name__ == "__main__":
    main()
