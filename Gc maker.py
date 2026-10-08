import json
import time
import threading
import requests
import websocket

OWNER_IDS = ["1202293462620459108", "1502282491921174750"]

TOKENS = [
    ""
]
TOKENS = [t.strip() for t in TOKENS if t and not t.startswith('.')]

PREFIX = "~"
GC_TARGET_NAME = "zєиιт нαᴛєʀ ¢υ∂αι кєи∂яα"


STREAM_TITLE = "ZENIT  GC MAKER"
TWITCH_URL = "https://www.twitch.tv/twitch "

ACTIVE_JOBS = {}
START_TIME = time.time()


def get_headers(token: str) -> dict:
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }


def send_message(channel_id: str, content: str, token: str):
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        requests.post(url, headers=get_headers(token), json={"content": content}, timeout=5)
    except Exception:
        pass


def send_friend_request(user_id: str, token: str):
    try:
        url = "https://discord.com/api/v9/users/@me/relationships"
        requests.post(url, headers=get_headers(token), json={"user_id": user_id}, timeout=5)
    except Exception:
        pass


def update_gc_name(channel_id: str, new_name: str, token: str) -> bool:
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        res = requests.patch(url, headers=get_headers(token), json={"name": new_name}, timeout=3)
        return res.status_code == 200
    except Exception:
        return False


def create_group_chat(token: str, recipients: list) -> str | None:
    try:
        url = "https://discord.com/api/v9/users/@me/channels"
        payload = {"access_tokens": [], "nicks": {}, "recipients": recipients}
        res = requests.post(url, headers=get_headers(token), json=payload, timeout=4)
        if res.status_code in (200, 201):
            data = res.json()
            return data.get("id")
    except Exception:
        pass
    return None


def fetch_gcs(token: str) -> list:
    try:
        url = "https://discord.com/api/v9/users/@me/channels"
        res = requests.get(url, headers=get_headers(token), timeout=5)
        if res.status_code == 200:
            return [(ch.get("id"), ch.get("name") or "Unnamed GC") for ch in res.json() if ch.get("type") == 3]
    except Exception:
        pass
    return []


def leave_gc(channel_id: str, token: str):
    try:
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        requests.delete(url, headers=get_headers(token), timeout=5)
    except Exception:
        pass


def verify_token(token: str) -> tuple[bool, str | None]:
    try:
        url = "https://discord.com/api/v9/users/@me"
        res = requests.get(url, headers=get_headers(token), timeout=5)
        if res.status_code == 200:
            return True, res.json().get("username")
    except Exception:
        pass
    return False, None


def background_gc_worker(channel_id: str, token: str, bot_id: int, limit: int, target_recipients: list):
    
    for uid in target_recipients:
        send_friend_request(uid, token)
        time.sleep(0.2)

    created_count = 0
    while ACTIVE_JOBS.get(channel_id, False) and created_count < limit:
        try:
            gc_id = create_group_chat(token, target_recipients)
            if gc_id:
                update_gc_name(gc_id, GC_TARGET_NAME, token)
                created_count += 1
            time.sleep(0.2)
        except Exception:
            time.sleep(0.5)

    ACTIVE_JOBS[channel_id] = False
    send_message(channel_id, f"✅ Bot #{bot_id} successfully created {created_count} Group Chats with the mentioned user(s)!", token)


class DiscordBotInstance:
    def __init__(self, token: str, bot_index: int):
        self.token = token
        self.bot_index = bot_index + 1
        self.running = True
        self.ws = None

    def handle_message(self, data: dict):
        if data.get("t") != "MESSAGE_CREATE":
            return
            
        msg = data.get("d", {})
        author_id = msg.get("author", {}).get("id")
        channel_id = msg.get("channel_id")
        content = msg.get("content", "")
        mentions = msg.get("mentions", [])

        if author_id not in OWNER_IDS or not content.startswith(PREFIX):
            return

        parts = content[len(PREFIX):].strip().split()
        if not parts:
            return
            
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "ping":
            uptime = round(time.time() - START_TIME, 2)
            send_message(channel_id, f"🏓 Pong #{self.bot_index} active. Uptime: {uptime}s", self.token)

        elif cmd in ("help", "menu"):
            help_msg = (
                f"```markdown\n"
                f"# ZENIT GC maker-  #\n"
                f"• {PREFIX}gcmake [count] @user - Make GCs with tagged user(s) (Max: 20)\n"
                f"• {PREFIX}stopgc              - stop GC creation loop\n"
                f"• {PREFIX}showgcs             - Fetch active joined GCs\n"
                f"• {PREFIX}leaveallgc          - Leave all GCs\n"
                f"• {PREFIX}tokens              - shows tokens\n"
                f"```"
            )
            send_message(channel_id, help_msg, self.token)

        elif cmd == "gcmake":
            if ACTIVE_JOBS.get(channel_id, False):
                send_message(channel_id, "⚠️  already running in this channel.", self.token)
                return
            
            limit = 5
            if args and args[0].isdigit():
                limit = int(args[0])
            
            if limit > 20:
                limit = 20

            
            target_recipients = [m.get("id") for m in mentions]
            
            if not target_recipients:
                send_message(channel_id, "⚠️ Please ping at least one user Example: `~gcmake 10 @user`", self.token)
                return

            ACTIVE_JOBS[channel_id] = True
            threading.Thread(target=background_gc_worker, args=(channel_id, self.token, self.bot_index, limit, target_recipients), daemon=True).start()
            send_message(channel_id, f"🚀 launching **{limit}** GCs with the tagged user(s)!", self.token)

        elif cmd == "stopgc":
            ACTIVE_JOBS[channel_id] = False
            send_message(channel_id, "🛑 Stopping active GC loops...", self.token)

        elif cmd == "showgcs":
            gcs = fetch_gcs(self.token)
            if not gcs:
                send_message(channel_id, "📁 No active group DMs found.", self.token)
                return
            formatted_list = "\n".join([f"• [{gid}] {name}" for gid, name in gcs[:12]])
            send_message(channel_id, f"📂 **Active GCs (Bot #{self.bot_index}):**\n{formatted_list}", self.token)

        elif cmd == "leaveallgc":
            gcs = fetch_gcs(self.token)
            if not gcs:
                send_message(channel_id, "📁 No GCs available to prune.", self.token)
                return
            send_message(channel_id, f"🧹 Leaving {len(gcs)} GCs...", self.token)
            for gid, _ in gcs:
                leave_gc(gid, self.token)
                time.sleep(0.2)
            send_message(channel_id, "✅ Pruning complete.", self.token)

        elif cmd == "tokens":
            valid, username = verify_token(self.token)
            status = f"Valid (User: `{username}`)" if valid else "Invalid / Expired"
            send_message(channel_id, f"🔍 Token Status: {status}", self.token)

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            op = data.get("op")

            if op == 10:
                interval = data["d"]["heartbeat_interval"] / 1000.0
                def heartbeat():
                    while self.running:
                        try:
                            ws.send(json.dumps({"op": 1, "d": None}))
                        except Exception:
                            break
                        time.sleep(interval)
                threading.Thread(target=heartbeat, daemon=True).start()

                payload = {
                    "op": 2,
                    "d": {
                        "token": self.token,
                        "properties": {"os": "windows", "browser": "chrome", "device": "pc"},
                        "presence": {
                            "status": "online",
                            "since": 0,
                            "activities": [{
                                "name": STREAM_TITLE,
                                "type": 1,
                                "url": TWITCH_URL
                            }],
                            "afk": False
                        }
                    }
                }
                ws.send(json.dumps(payload))

            self.handle_message(data)
        except Exception:
            pass

    def start(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    "wss://gateway.discord.gg/?v=9&encoding=json",
                    on_message=self.on_message
                )
                self.ws.run_forever()
            except Exception:
                pass
            time.sleep(5)


def main():
    if not TOKENS:
        print("[!] No valid tokens found.")
        return

    print(f"[*] Starting bot ...")
    for idx, token in enumerate(TOKENS):
        bot = DiscordBotInstance(token, idx)
        threading.Thread(target=bot.start, daemon=True).start()
        time.sleep(0.3)

    print(f"\n[+] Bot is ready! Use `~gcmake <n> @user @user2` in Discord.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down .")


if __name__ == "__main__":
    main()
