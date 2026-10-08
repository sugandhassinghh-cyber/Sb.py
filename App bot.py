import asyncio
import json
import os
import random
import sys
from collections import deque
from typing import Optional, Set, Dict, List, Deque
import time

import discord
from discord.ext import commands, tasks

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURATION & PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

BOT_TOKENS = [
"token",
"token"
]

DEFAULT_OWNER_IDS = {535325409580023818}
DATA_FILE = "bot_data.json"
PARALLEL_LIMIT = 15

SPAM_DELAY_MIN = 0.05
SPAM_DELAY_MAX = 0.15
BATCH_SIZE = 10
BATCH_SLEEP = 0.3
RANDOM_ROTATION = True

C = {
    "reset":  "\033[0m",
    "red":    "\033[1;31m",
    "green":  "\033[1;32m",
    "yellow": "\033[1;33m",
    "blue":   "\033[1;34m",
    "cyan":   "\033[1;36m",
    "purple": "\033[1;35m",
    "white":  "\033[1;37m",
    "gray":   "\033[2;37m",
    "bg":     "\033[1;40m",
}

# ═══════════════════════════════════════════════════════════════════
#  DATA PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        initial = {
            "owner_ids": list(DEFAULT_OWNER_IDS),
            "roasts": [""],
            "spam_phrases": [""],
            "dm_phrases": [""],
            "channel_phrases": [""],
            "server_prefixes": [""],
            "channel_prefixes": [""],
            "member_nc_prefixes": [""],
            "copied_user": None,
            "copied_messages": [],
        }
        with open(DATA_FILE, "w") as f:
            json.dump(initial, f, indent=4)
        return initial
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        defaults = {
            "dm_phrases": [""],
            "channel_phrases": [""],
            "member_nc_prefixes": [""],
            "copied_user": None,
            "copied_messages": [],
        }
        for key, default in defaults.items():
            if key not in data:
                data[key] = default
        return data
    except Exception:
        return {
            "owner_ids": list(DEFAULT_OWNER_IDS),
            "roasts": [],
            "spam_phrases": [],
            "dm_phrases": [],
            "channel_phrases": [],
            "server_prefixes": [],
            "channel_prefixes": [],
            "member_nc_prefixes": [],
            "copied_user": None,
            "copied_messages": [],
        }

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

GLOBAL_DATA = load_data()
GLOBAL_OWNERS: Set[int] = set(GLOBAL_DATA.get("owner_ids", DEFAULT_OWNER_IDS))

def pick_dm_phrase() -> str:
    pool = GLOBAL_DATA.get("dm_phrases") or GLOBAL_DATA.get("spam_phrases") or ["."]
    return random.choice(pool)

def pick_channel_phrase() -> str:
    pool = GLOBAL_DATA.get("channel_phrases") or GLOBAL_DATA.get("spam_phrases") or ["."]
    return random.choice(pool)

# ═══════════════════════════════════════════════════════════════════
#  FAST PARALLEL SENDER
# ═══════════════════════════════════════════════════════════════════

async def batch_send(targets: List[discord.abc.Messageable], content: str):
    for i in range(0, len(targets), PARALLEL_LIMIT):
        batch = targets[i : i + PARALLEL_LIMIT]
        await asyncio.gather(*[t.send(content) for t in batch], return_exceptions=True)


# ═══════════════════════════════════════════════════════════════════
#  UNIFIED BOT CLASS
# ═══════════════════════════════════════════════════════════════════

class UnifiedBot(commands.Bot):
    def __init__(self, index: int):
        intents = discord.Intents.all()
        super().__init__(command_prefix=["$", "!"], intents=intents, help_command=None)
        self.index = index

        self.auto_react_enabled: bool = False
        self.auto_react_emoji: str = "🥵"

        self.tracked_dms: Set[int] = set()
        self.tracked_channels: Set[int] = set()
        self.custom_dms: Dict[int, str] = {}
        self.auto_replies: Dict[int, str] = {}

        self.target_name: Optional[str] = None

        self.server_nc_name: Optional[str] = None
        self.server_nc_active: bool = False

        self.channel_nc_active: bool = False

        self.member_nc_active: bool = False
        self.member_nc_target: Optional[int] = None

        self.dm_spam_all_active: bool = False
        self.custom_dm_spam_all_active: bool = False
        self.custom_dm_spam_all_msg: Optional[str] = None

        self.nuke_active: bool = False
        self.nuke_channel_name: str = "nuked"
        self.nuke_message: str = "@everyone GET NUKED ☢️"

        self.raid_active: bool = False
        self.raid_channel_name: str = "raided"
        self.raid_message: str = "@everyone RAIDED 🚨"

        self.custom_channel_msgs: Dict[int, str] = {}

        self.custom_message_all_active: bool = False
        self.custom_message_all_msg: Optional[str] = None

        self.copied_target: Optional[int] = GLOBAL_DATA.get("copied_user")

        # ── Longspam Features (multi-channel now) ──
        self.longspam_channels: Dict[int, str] = {}    # { channel_id: text }
        self.longspam_all_active: bool = False
        self.longspam_all_text: Optional[str] = None

        # ── Spam Command Features (multi-channel now) ──
        self.spam_cmd_channels: Dict[int, str] = {}    # { channel_id: target }

        # ── Anti-Rate-Limit state per channel ──
        self._spam_message_count: int = 0
        self._spam_last_send: Dict[int, float] = {}
        self._spam_variants: List[str] = []

        # ── Roast Spam Features (multi-channel now) ──
        self.roast_spam_channels: Dict[int, Dict] = {}  # { channel_id: {target, delay, task} }

        # ── ALL Roast Spam (server-wide) ──
        self.all_roast_spam_active: bool = False
        self.all_roast_spam_target: Optional[str] = None
        self.all_roast_spam_guild_id: Optional[int] = None
        self.all_roast_spam_delay: float = 0.0

        # ── Bypass Spam Features ──
        self.byp_spam_active: bool = False
        self.byp_spam_target: Optional[str] = None
        self.byp_spam_channel_id: Optional[int] = None

        # ── Bypass Channel Add Features ──
        self.byp_channel_add_active: bool = False
        self.byp_channel_add_name: Optional[str] = None
        self.byp_channel_add_guild_id: Optional[int] = None
        self.byp_channel_add_created: int = 0
        self.byp_channel_add_max: int = 50

        self._all_text_channels_cache: List[discord.TextChannel] = []
        self._all_members_cache: List[discord.Member] = []
        self._cache_refresh_counter: int = 0

        self._generate_spam_variants()

        self.roast_emojis = ["❤️️", "💛", "💚", "💙", "💜", "🧡", "🤎", "🖤", "🤍", "💓", "💗", "💖", "💘", "💝"]

        self.roast_messages = [
            "𝐑ɴᴅʏ", "𝐑ɴᴅʏ",
            "𝐋ᴏᴅᴇ", "𝐋ᴏᴅᴇ",
            "𝐂ʜᴜᴅ", "𝐂ʜᴜᴅ",
            "𝐁sᴅᴋ", "𝐁sᴅᴋ",
            "𝐓ᴍᴋᴄ", "𝐓ᴍᴋᴄ",
            "𝐓ᴍᴋʟ", "𝐓ᴍᴋʟ",
            "𝐓ᴍᴋʙ", "𝐓ᴍᴋʙ",
        ]

    def _generate_spam_variants(self):
        heart_emojis = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💘", "💝", "💖", "💗", "💓", "💕", "💞", "💟", "♥️"]
        decorations = ["𓍼", "✦", "✧", "🌸", "🌺", "✨", "⭐", "🌈", "🦋", "🌊", "🔥", "⚡", "💫"]

        templates = [
            """{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart1}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart2}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart3}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart1}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart1}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart2}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart3}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart1}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart1}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart2}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart3}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart1}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart1}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart2}
{deco} {deco2}🌈{deco2}

< {target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{heart3}
│   {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{heart1}""",

            """═══ {deco} ═══
【 {target} 】  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
┌─{heart1}─┐
│ {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 │
└─{heart2}─┘
═══ {deco2} ═══
═══ {deco} ═══
【 {target} 】  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
┌─{heart1}─┐
│ {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 │
└─{heart2}─┘
═══ {deco2} ═══
═══ {deco} ═══
【 {target} 】  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
┌─{heart1}─┐
│ {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 │
└─{heart2}─┘
═══ {deco2} ═══
═══ {deco} ═══
【 {target} 】  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
┌─{heart1}─┐
│ {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 │
└─{heart2}─┘
═══ {deco2} ═══
═══ {deco} ═══
【 {target} 】  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
┌─{heart1}─┐
│ {target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 │
└─{heart2}─┘
═══ {deco2} ═══""",

            """✦ {target} ✦  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
{target}  𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✦ {heart1} ✦
✦ {target} ✦  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
{target}  𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✦ {heart1} ✦
✦ {target} ✦  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
{target}  𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✦ {heart1} ✦
✦ {target} ✦  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
{target}  𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✦ {heart1} ✦
✦ {target} ✦  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
{target}  𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✦ {heart1} ✦
✦ {target} ✦  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
{target}  𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
✦ {heart1} ✦""",

            """╔═══════════════════╗
║ {target} ║
║  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ ║
║  𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ║
╠═══════════════════╣
║ {target}  𝐓ʀ𝐈  मा ║
║ 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 ║
╚═══════════════════╝
{heart1} {heart2} {heart3}
╔═══════════════════╗
║ {target} ║
║  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ ║
║  𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ║
╠═══════════════════╣
║ {target}  𝐓ʀ𝐈  मा ║
║ 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 ║
╚═══════════════════╝
{heart1} {heart2} {heart3}
╔═══════════════════╗
║ {target} ║
║  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ ║
║  𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ║
╠═══════════════════╣
║ {target}  𝐓ʀ𝐈  मा ║
║ 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 ║
╚═══════════════════╝
{heart1} {heart2} {heart3}
╔═══════════════════╗
║ {target} ║
║  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ ║
║  𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ║
╠═══════════════════╣
║ {target}  𝐓ʀ𝐈  मा ║
║ 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓 ║
╚═══════════════════╝
{heart1} {heart2} {heart3}""",
        ]

        self._spam_variants = templates

    def _bold_text(self, text: str) -> str:
        bold_map = {
            'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛',
            'I': '𝗜', 'J': '𝗝', 'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣',
            'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧', 'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫',
            'Y': '𝗬', 'Z': '𝗭', 'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳',
            'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷', 'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻',
            'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁', 'u': '𝘂', 'v': '𝘃',
            'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇'
        }
        return ''.join(bold_map.get(c, c) for c in text)

    def _get_roast_emoji(self) -> str:
        return random.choice(self.roast_emojis)

    def _build_roast_message(self, target: str, text: str) -> str:
        e = self._get_roast_emoji()
        msg = f"🎯 {target} 🎯\n\n"
        for i in range(50):
            msg += f"{target} {self._bold_text(text)} {e}\n"
        msg += f"\n🔥 {self._bold_text('The ZENIT Daddy')} 🔥"
        return msg

    def _get_random_roast_msg(self, target: str) -> str:
        selected_text = random.choice(self.roast_messages)
        return self._build_roast_message(target, selected_text)

    # ── LONGSPAM message builder (50 lines, same emoji per message) ──
    def _build_longspam_message(self, text: str) -> str:
        """Build a 50-line longspam message. All 50 lines use the SAME emoji.
        The emoji changes per message (via random.choice in the loop)."""
        heart_emojis = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍",
                        "💘", "💝", "💖", "💗", "💓", "💕", "💞", "💟", "♥️"]
        chosen = random.choice(heart_emojis)
        line = f"# {text} {chosen}\n"
        return line * 50

    def _refresh_caches(self):
        self._all_text_channels_cache = [
            ch for g in self.guilds
            for ch in g.channels if isinstance(ch, discord.TextChannel)
        ]
        self._all_members_cache = [
            m for g in self.guilds for m in g.members if not m.bot
        ]

    def _get_guild_text_channels(self, guild_id: int) -> List[discord.TextChannel]:
        guild = self.get_guild(guild_id)
        if not guild:
            return []
        return [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]

    # ═══════════════════════════════════════════════════
    #  SETUP
    # ═══════════════════════════════════════════════════

    async def setup_hook(self):
        self.spam_loop.start()
        self.nc_loop.start()
        self.nuke_raid_loop.start()
        self.longspam_loop.start()
        self.spam_cmd_loop.start()
        self.byp_spam_loop.start()
        self.byp_channel_add_loop.start()
        self.all_roast_spam_loop.start()

    # ═══════════════════════════════════════════════════
    #  ALL ROAST SPAM LOOP  (server-wide)
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.05)
    async def all_roast_spam_loop(self):
        if not self.all_roast_spam_active or not self.all_roast_spam_target or not self.all_roast_spam_guild_id:
            return

        try:
            channels = self._get_guild_text_channels(self.all_roast_spam_guild_id)
            if not channels:
                self.all_roast_spam_active = False
                self.all_roast_spam_target = None
                self.all_roast_spam_guild_id = None
                return

            roast_msg = self._get_random_roast_msg(self.all_roast_spam_target)

            for i in range(0, len(channels), PARALLEL_LIMIT):
                batch = channels[i:i + PARALLEL_LIMIT]
                try:
                    await asyncio.gather(*[ch.send(roast_msg) for ch in batch], return_exceptions=True)
                except Exception:
                    pass
                await asyncio.sleep(0.05 + random.uniform(0.01, 0.05))

            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            print(f"[Bot #{self.index}] All Roast Spam error: {e}")
            self.all_roast_spam_active = False
            self.all_roast_spam_target = None
            self.all_roast_spam_guild_id = None

    @all_roast_spam_loop.before_loop
    async def before_all_roast_spam_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  SPAM CMD LOOP (multi-channel now)
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.1)
    async def spam_cmd_loop(self):
        """Multi-channel spam with anti-RL & anti-ban protection."""
        if not self.spam_cmd_channels:
            return

        for channel_id, target in list(self.spam_cmd_channels.items()):
            try:
                channel = self.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.fetch_channel(channel_id)
                    except Exception:
                        self.spam_cmd_channels.pop(channel_id, None)
                        continue

                last = self._spam_last_send.get(channel_id, 0)
                now = time.time()
                time_since = now - last
                if time_since < SPAM_DELAY_MIN:
                    await asyncio.sleep(SPAM_DELAY_MIN - time_since + random.uniform(0.01, 0.05))

                heart_emojis = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💘", "💝", "💖", "💗", "💓", "💕", "💞", "💟", "♥️️"]
                decorations = ["𓍼", "✦", "✧", "🌸", "🌺", "✨", "⭐", "🌈", "🦋", "🌊", "🔥", "⚡", "💫"]

                heart1 = random.choice(heart_emojis)
                heart2 = random.choice(heart_emojis)
                heart3 = random.choice(heart_emojis)
                deco = random.choice(decorations)
                deco2 = random.choice(decorations)

                template = random.choice(self._spam_variants)
                spam_message = template.format(
                    target=target, heart1=heart1, heart2=heart2, heart3=heart3,
                    deco=deco, deco2=deco2
                )

                try:
                    await channel.send(spam_message)
                    self._spam_message_count += 1
                    self._spam_last_send[channel_id] = time.time()
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = float(e.response.headers.get('Retry-After', 1))
                        await asyncio.sleep(retry_after + random.uniform(0.5, 1.5))
                    else:
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                except Exception:
                    await asyncio.sleep(random.uniform(0.1, 0.5))

                if self._spam_message_count % BATCH_SIZE == 0:
                    await asyncio.sleep(BATCH_SLEEP + random.uniform(0, 0.5))

                if random.random() < 0.1:
                    await asyncio.sleep(random.uniform(0.1, 0.4))

            except Exception as e:
                print(f"[Bot #{self.index}] Spam cmd error in {channel_id}: {e}")

    @spam_cmd_loop.before_loop
    async def before_spam_cmd_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  BYPASS SPAM LOOP  (0.3 s)
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.3)
    async def byp_spam_loop(self):
        if not self.byp_spam_active or not self.byp_spam_target or not self.byp_spam_channel_id:
            return

        heart_emojis = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💘", "💝", "💖", "💗", "💓", "💕", "💞", "💟", "♥️"]

        try:
            channel = self.get_channel(self.byp_spam_channel_id)
            if not channel:
                try:
                    channel = await self.fetch_channel(self.byp_spam_channel_id)
                except Exception as e:
                    print(f"[Bot #{self.index}] Cannot access channel {self.byp_spam_channel_id}: {e}")
                    self.byp_spam_active = False
                    self.byp_spam_target = None
                    self.byp_spam_channel_id = None
                    return

            random_heart1 = random.choice(heart_emojis)
            random_heart2 = random.choice(heart_emojis)
            random_heart3 = random.choice(heart_emojis)

            spam_message = f"""𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart1}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart2}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart3}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart1}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart2}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart3}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart1}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart2}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart3}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart1}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart2}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart3}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart1}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart2}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart3}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart1}
𓍼 𓆩🌈𓆪

< {self.byp_spam_target} >  𝐓ᴇ𝐑ʏ बौनी मा 𝐊ᴀ ₹ᴀ𝐏ᴇ 𝐊ᴀʀ𝐃𝐮  ___/ 🦋 ࿐ཽ༵
╭─────────────────{random_heart2}
│   {self.byp_spam_target}   𝐓ʀ𝐈  मा 𝐂ᴜ𝐃ɪ 𝐁ʏ---𝐙ᴇɴɪ𝐓
╰─────────────────{random_heart3}"""

            await channel.send(spam_message)

        except Exception as e:
            self.byp_spam_active = False
            self.byp_spam_target = None
            self.byp_spam_channel_id = None
            print(f"[Bot #{self.index}] Bypass spam error: {e}")

    @byp_spam_loop.before_loop
    async def before_byp_spam_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  BYPASS CHANNEL ADD LOOP
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.5)
    async def byp_channel_add_loop(self):
        if not self.byp_channel_add_active or not self.byp_channel_add_guild_id:
            return

        try:
            guild = self.get_guild(self.byp_channel_add_guild_id)
            if not guild:
                try:
                    guild = await self.fetch_guild(self.byp_channel_add_guild_id)
                except Exception as e:
                    print(f"[Bot #{self.index}] Cannot access guild {self.byp_channel_add_guild_id}: {e}")
                    self.byp_channel_add_active = False
                    return

            for _ in range(min(3, self.byp_channel_add_max - self.byp_channel_add_created)):
                try:
                    await guild.create_text_channel(self.byp_channel_add_name)
                    self.byp_channel_add_created += 1
                except Exception as e:
                    print(f"[Bot #{self.index}] Channel creation error: {e}")
                    await asyncio.sleep(0.5)
                await asyncio.sleep(0.2)

            if self.byp_channel_add_created >= self.byp_channel_add_max:
                self.byp_channel_add_active = False

        except Exception as e:
            print(f"[Bot #{self.index}] Bypass channel add error: {e}")
            self.byp_channel_add_active = False

    @byp_channel_add_loop.before_loop
    async def before_byp_channel_add_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  LONGSPAM LOOP (multi-channel + 50-line format)
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.05)
    async def longspam_loop(self):
        # ── Multi-channel longspam ──
        for channel_id, text in list(self.longspam_channels.items()):
            if not text:
                continue
            try:
                chan = self.get_channel(channel_id) or await self.fetch_channel(channel_id)

                # Anti-rate-limit: per-channel dynamic delay
                last = self._spam_last_send.get(channel_id, 0)
                now = time.time()
                if now - last < SPAM_DELAY_MIN:
                    await asyncio.sleep(SPAM_DELAY_MIN - (now - last) + random.uniform(0.01, 0.05))

                msg = self._build_longspam_message(text)
                try:
                    await chan.send(msg)
                    self._spam_last_send[channel_id] = time.time()
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = float(e.response.headers.get('Retry-After', 1))
                        await asyncio.sleep(retry_after + random.uniform(0.5, 1.5))
                    else:
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                except Exception:
                    await asyncio.sleep(random.uniform(0.1, 0.5))

                # Anti-ban: random extra delay
                if random.random() < 0.1:
                    await asyncio.sleep(random.uniform(0.05, 0.2))
            except Exception:
                self.longspam_channels.pop(channel_id, None)

        # ── Longspam in all channels ──
        if self.longspam_all_active and self.longspam_all_text and self._all_text_channels_cache:
            try:
                msg = self._build_longspam_message(self.longspam_all_text)
                await batch_send(self._all_text_channels_cache, msg)
                if random.random() < 0.1:
                    await asyncio.sleep(random.uniform(0.05, 0.2))
            except Exception as e:
                print(f"[Bot #{self.index}] Longspam ALL error: {e}")

    @longspam_loop.before_loop
    async def before_longspam_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  SPAM LOOP  (DM/Channel roasts etc.)  (0.05 s)
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.05)
    async def spam_loop(self):
        self._cache_refresh_counter += 1
        if self._cache_refresh_counter % 30 == 0:
            self._refresh_caches()

        if self.dm_spam_all_active and self._all_members_cache:
            msg = pick_dm_phrase()
            await batch_send(self._all_members_cache, msg)

        if self.custom_dm_spam_all_active and self.custom_dm_spam_all_msg and self._all_members_cache:
            await batch_send(self._all_members_cache, self.custom_dm_spam_all_msg)

        for uid in list(self.tracked_dms):
            try:
                user = await self.fetch_user(uid)
                await user.send(pick_dm_phrase())
            except Exception:
                self.tracked_dms.discard(uid)

        for uid, msg in list(self.custom_dms.items()):
            try:
                user = await self.fetch_user(uid)
                await user.send(msg)
            except Exception:
                self.custom_dms.pop(uid, None)

        for cid in list(self.tracked_channels):
            try:
                chan = self.get_channel(cid) or await self.fetch_channel(cid)
                await chan.send(pick_channel_phrase())
            except Exception:
                self.tracked_channels.discard(cid)

        if self.target_name:
            for cid in list(self.tracked_channels):
                try:
                    chan = self.get_channel(cid) or await self.fetch_channel(cid)
                    roast = random.choice(GLOBAL_DATA["roasts"])
                    await chan.send(f"{self.target_name} {roast}")
                except Exception:
                    pass

        for cid, msg in list(self.custom_channel_msgs.items()):
            try:
                chan = self.get_channel(cid) or await self.fetch_channel(cid)
                await chan.send(msg)
            except Exception:
                self.custom_channel_msgs.pop(cid, None)

        if self.custom_message_all_active and self.custom_message_all_msg and self._all_text_channels_cache:
            await batch_send(self._all_text_channels_cache, self.custom_message_all_msg)

        if self.copied_spam_active and GLOBAL_DATA.get("copied_messages") and self._all_text_channels_cache:
            for msg in GLOBAL_DATA["copied_messages"]:
                await batch_send(self._all_text_channels_cache, msg)

    @spam_loop.before_loop
    async def before_spam_loop(self):
        await self.wait_until_ready()
        self._refresh_caches()

    # ═══════════════════════════════════════════════════
    #  NAME-CHANGER LOOP
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=1.0)
    async def nc_loop(self):
        if self.server_nc_active and self.server_nc_name:
            prefix = random.choice(GLOBAL_DATA["server_prefixes"]) if GLOBAL_DATA["server_prefixes"] else ""
            new_name = f"{self.server_nc_name} {prefix}".strip()
            edits = [g.edit(name=new_name) for g in self.guilds]
            await asyncio.gather(*edits, return_exceptions=True)

        if self.channel_nc_active:
            prefix = random.choice(GLOBAL_DATA["channel_prefixes"]) if GLOBAL_DATA["channel_prefixes"] else "rip"
            edits = [
                ch.edit(name=f"{prefix}-{random.randint(1,999)}")
                for g in self.guilds
                for ch in g.channels
            ]
            for i in range(0, len(edits), PARALLEL_LIMIT):
                await asyncio.gather(*edits[i:i+PARALLEL_LIMIT], return_exceptions=True)

        if self.member_nc_active and self.member_nc_target:
            prefixes = GLOBAL_DATA.get("member_nc_prefixes") or ["."]
            for guild in self.guilds:
                member = guild.get_member(self.member_nc_target)
                if member:
                    try:
                        new_nick = f"{random.choice(prefixes)} {random.randint(1,999)}".strip()
                        await member.edit(nick=new_nick)
                    except Exception:
                        pass

    @nc_loop.before_loop
    async def before_nc_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  NUKE / RAID LOOP
    # ═══════════════════════════════════════════════════
    @tasks.loop(seconds=0.5)
    async def nuke_raid_loop(self):
        channels = self._all_text_channels_cache or [
            ch for g in self.guilds
            for ch in g.channels if isinstance(ch, discord.TextChannel)
        ]

        if self.nuke_active:
            if channels:
                await batch_send(channels, self.nuke_message)
            name_edits = [
                g.edit(name=f"{self.nuke_channel_name}-{random.randint(1,9999)}")
                for g in self.guilds
            ]
            await asyncio.gather(*name_edits, return_exceptions=True)

        if self.raid_active:
            if channels:
                await batch_send(channels, self.raid_message)

    @nuke_raid_loop.before_loop
    async def before_nuke_raid_loop(self):
        await self.wait_until_ready()

    # ═══════════════════════════════════════════════════
    #  EVENTS
    # ═══════════════════════════════════════════════════

    async def on_ready(self):
        print(f"[Bot #{self.index}] ✅ Online as {self.user} (ID: {self.user.id})")
        self._refresh_caches()

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.copied_target and message.author.id == self.copied_target:
            GLOBAL_DATA.setdefault("copied_messages", [])
            GLOBAL_DATA["copied_messages"].append(message.content)
            save_data(GLOBAL_DATA)

        if message.author.id in self.auto_replies:
            try:
                await message.reply(self.auto_replies[message.author.id])
            except Exception:
                pass

        if self.auto_react_enabled:
            try:
                await message.add_reaction(self.auto_react_emoji)
            except Exception:
                pass

        await self.process_commands(message)


# ═══════════════════════════════════════════════════════════════════
#  COMMAND REGISTRATION
# ═══════════════════════════════════════════════════════════════════

def is_owner():
    async def predicate(ctx: commands.Context) -> bool:
        return ctx.author.id in GLOBAL_OWNERS
    return commands.check(predicate)

SUCCESS_COLOR = 0x57F287
ERROR_COLOR   = 0xED4245
INFO_COLOR    = 0x5865F2
WARN_COLOR    = 0xFEE75C

def ok_embed(title: str, desc: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=desc, color=SUCCESS_COLOR)

def err_embed(title: str, desc: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=desc, color=ERROR_COLOR)

def info_embed(title: str, desc: str = "") -> discord.Embed:
    return discord.Embed(title=title, description=desc, color=INFO_COLOR)

_copied_spam_active: bool = False

def register_commands(bot: UnifiedBot):

    # ═══════════════════════════════════════════════════
    #  HELP
    # ═══════════════════════════════════════════════════
    @bot.command(name="help")
    async def help_cmd(ctx: commands.Context):
        zenit_art = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  ███████╗███████╗███╗   ██╗██╗████████╗    ██╗  ██╗███████╗    ██████╗██╗  ██╗║
║  ╚══███╔╝██╔════╝████╗  ██║██║╚══██╔══╝    ██║ ██╔╝██╔════╝   ██╔════╝██║  ██║║
║    ███╔╝ █████╗  ██╔██╗ ██║██║   ██║       █████╔╝ █████╗     ██║     ███████║║
║   ███╔╝  ██╔══╝  ██║╚██╗██║██║   ██║       ██╔═██╗ ██╔══╝     ██║     ██╔══██║║
║  ███████╗███████╗██║ ╚████║██║   ██║       ██║  ██╗███████╗██╗╚██████╗██║  ██║║
║  ╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝   ╚═╝       ╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝╚═╝  ╚═╝║
║                                                                              ║
║  ██████╗  ██████╗ ████████╗███████╗    ███████╗██╗  ██╗██████╗ ██╗██████╗     ║
║  ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝    ██╔════╝██║  ██║██╔══██╗██║██╔══██╗    ║
║  ██████╔╝██║   ██║   ██║   ███████╗    ███████╗███████║██████╔╝██║██████╔╝    ║
║  ██╔══██╗██║   ██║   ██║   ╚════██║    ╚════██║██╔══██║██╔═══╝ ██║██╔═══╝     ║
║  ██║  ██║╚██████╔╝   ██║   ███████║    ███████║██║  ██║██║     ██║██║         ║
║  ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝         ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """

        embed = discord.Embed(
            title="⚡ **SYSTEM INTERFACE**",
            description=f"```\n{zenit_art}\n```\n**Bot Instance #{bot.index}**  —  `{bot.user}`",
            color=0xFF6B00,
        )
        embed.set_footer(text="Prefixes: !  or  $  •  All commands require owner role  •  ⚡ ZENIT KE CHELE SCRIPT v2.0")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1015805567988617246.png")

        embed.add_field(
            name="🔑 **Ownership**",
            value="`!addowner <id>` / `!removeowner <id>` / `!listowners`",
            inline=False,
        )
        embed.add_field(
            name="☢️ **Nuke / Raid**",
            value="`!nuke [name] [msg]` / `!nukestop` / `!raid [name] [msg]` / `!raidstop`",
            inline=False,
        )
        embed.add_field(
            name="💬 **Custom Messages**",
            value="`!custommessage <msg>` / `!custommessagestop` / `!custommessageall <msg>` / `!custommessageallstop`",
            inline=False,
        )
        embed.add_field(
            name="📢 **DM Broadcast**",
            value="`!dm <id>` / `!dmcustommessage <id> <msg>` / `!dmspamall` / `!dmspamallstop` / `!customdmspamall <msg>` / `!customdmspamallstop`",
            inline=False,
        )
        embed.add_field(
            name="📺 **Channel Tools**",
            value="`!channel <id>` / `!channeladd <n> <name>` / `!deletechannelall` / `!target <name>`",
            inline=False,
        )
        embed.add_field(
            name="🏷️ **Name Changers**",
            value="`!servernc <name>` / `!serverncstop` / `!channelnc` / `!channelncstop` / `!membernc <id>` / `!memberncstop`",
            inline=False,
        )
        embed.add_field(
            name="⚙️ **Phrases & Prefixes**",
            value=(
                "`!dmphraseadd <text>` / `!dmphraseremove <text>`\n"
                "`!channelphraseadd <text>` / `!channelphraseremove <text>`\n"
                "`!serverprefixadd <p>` / `!serverprefixremove <p>`\n"
                "`!channelprefixadd <p>` / `!channelprefixremove <p>`\n"
                "`!memberncprefixadd <p>` / `!memberncprefixremove <p>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="📋 **Copy Message System**",
            value="`!copymessage <id>` / `!copymessagestop` / `!copiedmessagespam` / `!copiedmessagespamstop` / `!deletecopiedmessage`",
            inline=False,
        )
        embed.add_field(
            name="📝 **Longspam System (Multi-Channel, 50 lines)**",
            value=(
                "`!longspam <text>`  —  Adds current channel to longspam list\n"
                "`!longspamstop`  —  Stops longspam in current channel only\n"
                "`!longspamall <text>`  —  Longspam in ALL channels\n"
                "`!longspamallstop`  —  Stop\n"
                "`!stopall`  —  Stop ALL"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔥 **Bypass Commands**",
            value="`!bypspam <channel_id> <target>` / `!stopbypspam` / `!bypchanneladd <server_id> <name>` / `!stopbypchanneladd`",
            inline=False,
        )
        embed.add_field(
            name="⚡ **Spam Commands (Multi-Channel)**",
            value=(
                "`!spam <target>`  —  Adds current channel to spam list\n"
                "`!stopspam`  —  Stops spam in current channel only"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔥 **Roast Spam (Multi-Channel)**",
            value=(
                "`!roastspam <target> [delay]`  —  Adds current channel to roast list\n"
                "`!roastspamstop`  —  Stops roast in current channel only\n"
                "Start it in as many channels as you want — each runs independently!"
            ),
            inline=False,
        )
        embed.add_field(
            name="🌐 **All Roast Spam (Server-Wide)**",
            value="`!allroastspam <target>` / `!allroastspamstop`",
            inline=False,
        )
        embed.add_field(
            name="🤖 **Automation & Utility**",
            value="`!autoreact <emoji>` / `!autoreactstop` / `!autoreply <id> <msg>` / `!autoreplystop <id>` / `!say <text>` / `!ping` / `!rename <name>` / `!shutdown` / `!stop <id>`",
            inline=False,
        )

        await ctx.send(embed=embed)

    # ═══════════════════════════════════════════════════
    #  ALL ROAST SPAM
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def allroastspam(ctx: commands.Context, *, target: str):
        if not ctx.guild:
            await ctx.send(embed=err_embed("❌ Error", "This command must be used in a server."))
            return

        if bot.all_roast_spam_active and bot.all_roast_spam_guild_id == ctx.guild.id:
            await ctx.send(embed=err_embed("⚠️ Already all-roast spamming this server!", "Use `!stopall` or `!allroastspamstop` first."))
            return

        if ctx.message.mentions:
            target = ctx.message.mentions[0].mention
        else:
            target = target.strip()

        channels = bot._get_guild_text_channels(ctx.guild.id)
        if not channels:
            await ctx.send(embed=err_embed("❌ Error", "No text channels found in this server."))
            return

        bot.all_roast_spam_active = True
        bot.all_roast_spam_target = target
        bot.all_roast_spam_guild_id = ctx.guild.id

        embed = discord.Embed(
            title="🌐 **ALL ROAST SPAM STARTED (INFINITE)**",
            description=f"Roasting **{target}** in **ALL {len(channels)} text channels** of `{ctx.guild.name}`",
            color=WARN_COLOR
        )
        embed.add_field(name="⚡ Speed", value="• **0.05s** loop speed\n• Parallel sending\n• Anti-RL protection", inline=False)
        embed.add_field(name="To Stop", value="Use `!allroastspamstop` or `!stopall`", inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    @is_owner()
    async def allroastspamstop(ctx: commands.Context):
        if not ctx.guild:
            await ctx.send(embed=err_embed("❌ Error", "This command must be used in a server."))
            return

        if bot.all_roast_spam_active and bot.all_roast_spam_guild_id == ctx.guild.id:
            bot.all_roast_spam_active = False
            bot.all_roast_spam_target = None
            bot.all_roast_spam_guild_id = None
            await ctx.send(embed=ok_embed("🛑 All Roast Spam Stopped", f"Stopped in `{ctx.guild.name}`"))
        else:
            await ctx.send(embed=err_embed("❌ Error", "No active all-roast spam in this server."))

    # ═══════════════════════════════════════════════════
    #  SAY
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def say(ctx: commands.Context, *, text: str):
        try:
            await ctx.send(text)
        except Exception as e:
            await ctx.send(embed=err_embed("❌ Error", f"Failed: {str(e)}"))

    # ═══════════════════════════════════════════════════
    #  SPAM COMMAND (multi-channel)
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def spam(ctx: commands.Context, *, target: str):
        """Add current channel to spam list. Use !stopspam to remove."""
        if ctx.channel.id in bot.spam_cmd_channels:
            await ctx.send(embed=err_embed("⚠️ Already spamming here!", "Use `!stopspam` first."))
            return

        bot.spam_cmd_channels[ctx.channel.id] = target
        bot._spam_last_send[ctx.channel.id] = time.time()

        embed = discord.Embed(
            title="⚡ **SPAM ADDED TO CHANNEL**",
            description=f"Spamming **{target}** in {ctx.channel.mention}",
            color=0xFF6B00
        )
        embed.add_field(
            name="📊 Active Channels",
            value=f"Currently spamming in **{len(bot.spam_cmd_channels)}** channel(s)",
            inline=False
        )
        embed.add_field(name="To Stop", value="Use `!stopspam` (this channel) or `!stopall`", inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    @is_owner()
    async def stopspam(ctx: commands.Context):
        """Stop spam in current channel only."""
        if ctx.channel.id in bot.spam_cmd_channels:
            bot.spam_cmd_channels.pop(ctx.channel.id, None)
            bot._spam_last_send.pop(ctx.channel.id, None)
            await ctx.send(embed=ok_embed("🛑 Spam Stopped", f"Stopped in {ctx.channel.mention}\n**Still active in {len(bot.spam_cmd_channels)} channel(s)**"))
        else:
            await ctx.send(embed=err_embed("❌ Error", "No active spam in this channel."))

    # ═══════════════════════════════════════════════════
    #  ROAST SPAM (multi-channel)
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def roastspam(ctx: commands.Context, *, args: str = None):
        """Add current channel to roast spam. Usage: !roastspam <target> [delay]"""
        if ctx.channel.id in bot.roast_spam_channels:
            await ctx.send(embed=err_embed("⚠️ Already roasting here!", "Use `!roastspamstop` first."))
            return

        delay = 0.0
        target = "@everyone"

        if args:
            parts = args.split()
            try:
                delay = float(parts[0])
                if len(parts) > 1:
                    target = ' '.join(parts[1:])
            except ValueError:
                target = args

        if ctx.message.mentions:
            target = ctx.message.mentions[0].mention
        else:
            target = target.strip()

        channel_id = ctx.channel.id
        delay_text = f"{delay}s" if delay > 0 else "MAX SPEED (0.0s)"

        bot.roast_spam_channels[channel_id] = {
            "target": target,
            "delay": delay,
        }

        embed = discord.Embed(
            title="🔥 **ROAST SPAM ADDED**",
            description=f"Roasting **{target}** at {delay_text} in {ctx.channel.mention}",
            color=WARN_COLOR
        )
        embed.add_field(
            name="📊 Active Channels",
            value=f"Currently roasting in **{len(bot.roast_spam_channels)}** channel(s)",
            inline=False
        )
        embed.add_field(
            name="💡 Multi-Channel",
            value="Run `!roastspam` in other channels to add them too — each runs independently!",
            inline=False
        )
        embed.add_field(name="To Stop", value="Use `!roastspamstop` (this channel) or `!stopall`", inline=False)
        await ctx.send(embed=embed)

        async def roast_loop_for_channel(cid, tgt, dly):
            consecutive_errors = 0
            while cid in bot.roast_spam_channels:
                try:
                    channel = bot.get_channel(cid)
                    if not channel:
                        try:
                            channel = await bot.fetch_channel(cid)
                        except Exception:
                            break

                    await channel.send(bot._get_random_roast_msg(tgt))

                    if dly > 0:
                        await asyncio.sleep(dly)
                    else:
                        await asyncio.sleep(0.02)

                    consecutive_errors = 0

                except discord.Forbidden:
                    await asyncio.sleep(5)
                    consecutive_errors += 1
                    if consecutive_errors >= 5:
                        break
                except discord.HTTPException as e:
                    if e.status == 429:
                        retry_after = float(e.response.headers.get('Retry-After', 5))
                        await asyncio.sleep(retry_after)
                    else:
                        await asyncio.sleep(0.5)
                        consecutive_errors += 1
                        if consecutive_errors >= 10:
                            break
                except Exception as e:
                    print(f"[Bot #{bot.index}] Roast spam error in {cid}: {e}")
                    await asyncio.sleep(1)
                    consecutive_errors += 1
                    if consecutive_errors >= 10:
                        break

            bot.roast_spam_channels.pop(cid, None)

        task_obj = asyncio.create_task(roast_loop_for_channel(channel_id, target, delay))
        bot.roast_spam_channels[channel_id]["task"] = task_obj

    @bot.command()
    @is_owner()
    async def roastspamstop(ctx: commands.Context):
        """Stop roast spam in current channel only."""
        channel_id = ctx.channel.id
        if channel_id in bot.roast_spam_channels:
            cfg = bot.roast_spam_channels.pop(channel_id, None)
            if cfg and cfg.get("task") and not cfg["task"].done():
                cfg["task"].cancel()
            await ctx.send(embed=ok_embed(
                "🛑 Roast Spam Stopped",
                f"Stopped in {ctx.channel.mention}\n**Still active in {len(bot.roast_spam_channels)} channel(s)**"
            ))
        else:
            await ctx.send(embed=err_embed("❌ Error", "No active roast spam in this channel."))

    # ═══════════════════════════════════════════════════
    #  BYPASS SPAM
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def bypspam(ctx: commands.Context, channel_id: int, *, target: str):
        channel = bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await bot.fetch_channel(channel_id)
                if not channel:
                    await ctx.send(embed=err_embed("❌ Error", "Channel not found."))
                    return
            except Exception as e:
                await ctx.send(embed=err_embed("❌ Error", f"Cannot access channel.\nError: {str(e)}"))
                return

        if not isinstance(channel, discord.TextChannel):
            await ctx.send(embed=err_embed("❌ Error", "That's not a text channel."))
            return

        bot.byp_spam_active = True
        bot.byp_spam_target = target
        bot.byp_spam_channel_id = channel_id

        embed = discord.Embed(
            title="🔥 **BYPASS SPAM STARTED**",
            description=f"Spamming **{target}** in <#{channel_id}>",
            color=WARN_COLOR
        )
        embed.add_field(name="To Stop", value="Use `!stopbypspam` or `!stopall`", inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    @is_owner()
    async def stopbypspam(ctx: commands.Context):
        if bot.byp_spam_active:
            bot.byp_spam_active = False
            bot.byp_spam_target = None
            bot.byp_spam_channel_id = None
            await ctx.send(embed=ok_embed("🛑 Bypass Spam Stopped"))
        else:
            await ctx.send(embed=err_embed("❌ Error", "No active bypass spam."))

    # ═══════════════════════════════════════════════════
    #  BYPASS CHANNEL ADD
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def bypchanneladd(ctx: commands.Context, guild_id: int, *, name: str):
        guild = bot.get_guild(guild_id)
        if not guild:
            try:
                guild = await bot.fetch_guild(guild_id)
                if not guild:
                    await ctx.send(embed=err_embed("❌ Error", "Bot is not in that server."))
                    return
            except Exception as e:
                await ctx.send(embed=err_embed("❌ Error", f"Cannot access guild.\nError: {str(e)}"))
                return

        bot.byp_channel_add_active = True
        bot.byp_channel_add_name = name
        bot.byp_channel_add_guild_id = guild_id
        bot.byp_channel_add_created = 0
        bot.byp_channel_add_max = 50

        embed = discord.Embed(
            title="🚀 **BYPASS CHANNEL ADD STARTED**",
            description=f"Creating **50** channels named `{name}` in `{guild.name}`",
            color=WARN_COLOR
        )
        embed.add_field(name="To Stop", value="Use `!stopbypchanneladd` or `!stopall`", inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    @is_owner()
    async def stopbypchanneladd(ctx: commands.Context):
        if bot.byp_channel_add_active:
            bot.byp_channel_add_active = False
            created = bot.byp_channel_add_created
            bot.byp_channel_add_name = None
            bot.byp_channel_add_guild_id = None
            bot.byp_channel_add_created = 0
            await ctx.send(embed=ok_embed("🛑 Bypass Channel Add Stopped", f"Created {created} channels."))
        else:
            await ctx.send(embed=err_embed("❌ Error", "No active bypass channel add."))

    # ═══════════════════════════════════════════════════
    #  OWNER MANAGEMENT
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def addowner(ctx: commands.Context, user_id: int):
        GLOBAL_OWNERS.add(user_id)
        GLOBAL_DATA["owner_ids"] = list(GLOBAL_OWNERS)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ Owner Added", f"`{user_id}` is now an owner."))

    @bot.command()
    @is_owner()
    async def removeowner(ctx: commands.Context, user_id: int):
        if len(GLOBAL_OWNERS) <= 1:
            return await ctx.send(embed=err_embed("❌ Error", "Cannot remove the last owner."))
        GLOBAL_OWNERS.discard(user_id)
        GLOBAL_DATA["owner_ids"] = list(GLOBAL_OWNERS)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ Owner Removed", f"`{user_id}` removed."))

    @bot.command()
    @is_owner()
    async def listowners(ctx: commands.Context):
        owners = "\n".join(f"• `{o}`" for o in GLOBAL_OWNERS)
        await ctx.send(embed=info_embed("👑 Authorized Owners", owners))

    # ═══════════════════════════════════════════════════
    #  AUTOMATION
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def autoreact(ctx: commands.Context, emoji: str):
        bot.auto_react_emoji = emoji
        bot.auto_react_enabled = True
        await ctx.send(embed=ok_embed("✅ Auto-React Enabled", f"Reacting with {emoji}"))

    @bot.command()
    @is_owner()
    async def autoreactstop(ctx: commands.Context):
        bot.auto_react_enabled = False
        await ctx.send(embed=ok_embed("🛑 Auto-React Disabled"))

    @bot.command()
    @is_owner()
    async def autoreply(ctx: commands.Context, user_id: int, *, msg: str):
        bot.auto_replies[user_id] = msg
        await ctx.send(embed=ok_embed("✅ Auto-Reply Set", f"User: `{user_id}`\nMessage: {msg}"))

    @bot.command()
    @is_owner()
    async def autoreplystop(ctx: commands.Context, user_id: int):
        bot.auto_replies.pop(user_id, None)
        await ctx.send(embed=ok_embed("🛑 Auto-Reply Stopped", f"For `{user_id}`"))

    # ═══════════════════════════════════════════════════
    #  TARGETING
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def dmcustommessage(ctx: commands.Context, user_id: int, *, msg: str):
        bot.custom_dms[user_id] = msg
        await ctx.send(embed=ok_embed("✅ Custom DM Spam Started", f"User: `{user_id}`\nMsg: {msg}"))

    @bot.command()
    @is_owner()
    async def dm(ctx: commands.Context, user_id: int):
        bot.tracked_dms.add(user_id)
        await ctx.send(embed=ok_embed("✅ DM Spam Started", f"User: `{user_id}`"))

    @bot.command()
    @is_owner()
    async def channel(ctx: commands.Context, channel_id: int):
        bot.tracked_channels.add(channel_id)
        await ctx.send(embed=ok_embed("✅ Channel Spam Started", f"Channel: <#{channel_id}>"))

    @bot.command()
    @is_owner()
    async def stop(ctx: commands.Context, target_id: int):
        bot.tracked_dms.discard(target_id)
        bot.tracked_channels.discard(target_id)
        bot.custom_dms.pop(target_id, None)
        bot.auto_replies.pop(target_id, None)
        if bot.copied_target == target_id:
            bot.copied_target = None
            GLOBAL_DATA["copied_user"] = None
            save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("🛑 Targeting Stopped", f"All spam stopped for `{target_id}`"))

    @bot.command()
    @is_owner()
    async def target(ctx: commands.Context, *, name: str):
        bot.target_name = name
        bot.tracked_channels.add(ctx.channel.id)
        await ctx.send(embed=ok_embed("🎯 Target Set", f"Roasting **{name}** in this channel."))

    # ═══════════════════════════════════════════════════
    #  DM BROADCAST
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def dmspamall(ctx: commands.Context):
        bot.dm_spam_all_active = True
        await ctx.send(embed=ok_embed("✅ DM Spam All Started", "Using dm_phrases"))

    @bot.command()
    @is_owner()
    async def dmspamallstop(ctx: commands.Context):
        bot.dm_spam_all_active = False
        await ctx.send(embed=ok_embed("🛑 DM Spam All Stopped"))

    @bot.command()
    @is_owner()
    async def customdmspamall(ctx: commands.Context, *, msg: str):
        bot.custom_dm_spam_all_active = True
        bot.custom_dm_spam_all_msg = msg
        await ctx.send(embed=ok_embed("✅ Custom DM Spam All Started", msg))

    @bot.command()
    @is_owner()
    async def customdmspamallstop(ctx: commands.Context):
        bot.custom_dm_spam_all_active = False
        bot.custom_dm_spam_all_msg = None
        await ctx.send(embed=ok_embed("🛑 Custom DM Spam All Stopped"))

    # ═══════════════════════════════════════════════════
    #  CHANNEL TOOLS
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def deletechannelall(ctx: commands.Context):
        if not ctx.guild:
            return await ctx.send(embed=err_embed("❌ Error", "Server-only command."))
        tasks_list = [ch.delete() for ch in ctx.guild.channels]
        await asyncio.gather(*tasks_list, return_exceptions=True)
        await ctx.send(embed=ok_embed("✅ All Channels Deleted"))

    @bot.command()
    @is_owner()
    async def channeladd(ctx: commands.Context, count: int, *, name: str):
        if not ctx.guild:
            return await ctx.send(embed=err_embed("❌ Error", "Server-only command."))
        count = min(count, 50)
        created = 0
        for _ in range(count):
            try:
                await ctx.guild.create_text_channel(name)
                created += 1
            except Exception:
                break
        await ctx.send(embed=ok_embed("✅ Channels Created", f"`{created}` channel(s) named `{name}`"))

    # ═══════════════════════════════════════════════════
    #  NAME CHANGERS
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def servernc(ctx: commands.Context, *, name: str):
        bot.server_nc_name = name
        bot.server_nc_active = True
        await ctx.send(embed=ok_embed("✅ Server NC Active", f"Name: **{name}**"))

    @bot.command()
    @is_owner()
    async def serverncstop(ctx: commands.Context):
        bot.server_nc_active = False
        await ctx.send(embed=ok_embed("🛑 Server NC Stopped"))

    @bot.command()
    @is_owner()
    async def channelnc(ctx: commands.Context):
        bot.channel_nc_active = True
        await ctx.send(embed=ok_embed("✅ Channel NC Active"))

    @bot.command()
    @is_owner()
    async def channelncstop(ctx: commands.Context):
        bot.channel_nc_active = False
        await ctx.send(embed=ok_embed("🛑 Channel NC Stopped"))

    @bot.command()
    @is_owner()
    async def membernc(ctx: commands.Context, user_id: int):
        bot.member_nc_target = user_id
        bot.member_nc_active = True
        await ctx.send(embed=ok_embed("✅ Member NC Active", f"Target: <@{user_id}>"))

    @bot.command()
    @is_owner()
    async def memberncstop(ctx: commands.Context):
        bot.member_nc_active = False
        bot.member_nc_target = None
        await ctx.send(embed=ok_embed("🛑 Member NC Stopped"))

    # ═══════════════════════════════════════════════════
    #  PHRASES & PREFIXES
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def dmphraseadd(ctx: commands.Context, *, text: str):
        GLOBAL_DATA.setdefault("dm_phrases", [])
        GLOBAL_DATA["dm_phrases"].append(text)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ DM Phrase Added", f"`{text}`"))

    @bot.command()
    @is_owner()
    async def dmphraseremove(ctx: commands.Context, *, text: str):
        phrases = GLOBAL_DATA.get("dm_phrases", [])
        if text in phrases:
            phrases.remove(text)
            save_data(GLOBAL_DATA)
            await ctx.send(embed=ok_embed("✅ DM Phrase Removed", f"`{text}`"))
        else:
            await ctx.send(embed=err_embed("❌ Not Found", f"`{text}`"))

    @bot.command()
    @is_owner()
    async def channelphraseadd(ctx: commands.Context, *, text: str):
        GLOBAL_DATA.setdefault("channel_phrases", [])
        GLOBAL_DATA["channel_phrases"].append(text)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ Channel Phrase Added", f"`{text}`"))

    @bot.command()
    @is_owner()
    async def channelphraseremove(ctx: commands.Context, *, text: str):
        phrases = GLOBAL_DATA.get("channel_phrases", [])
        if text in phrases:
            phrases.remove(text)
            save_data(GLOBAL_DATA)
            await ctx.send(embed=ok_embed("✅ Channel Phrase Removed", f"`{text}`"))
        else:
            await ctx.send(embed=err_embed("❌ Not Found", f"`{text}`"))

    @bot.command()
    @is_owner()
    async def serverprefixadd(ctx: commands.Context, *, prefix: str):
        GLOBAL_DATA.setdefault("server_prefixes", [])
        GLOBAL_DATA["server_prefixes"].append(prefix)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ Server Prefix Added", f"`{prefix}`"))

    @bot.command()
    @is_owner()
    async def serverprefixremove(ctx: commands.Context, *, prefix: str):
        prefixes = GLOBAL_DATA.get("server_prefixes", [])
        if prefix in prefixes:
            prefixes.remove(prefix)
            save_data(GLOBAL_DATA)
            await ctx.send(embed=ok_embed("✅ Server Prefix Removed", f"`{prefix}`"))
        else:
            await ctx.send(embed=err_embed("❌ Not Found", f"`{prefix}`"))

    @bot.command()
    @is_owner()
    async def channelprefixadd(ctx: commands.Context, *, prefix: str):
        GLOBAL_DATA.setdefault("channel_prefixes", [])
        GLOBAL_DATA["channel_prefixes"].append(prefix)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ Channel Prefix Added", f"`{prefix}`"))

    @bot.command()
    @is_owner()
    async def channelprefixremove(ctx: commands.Context, *, prefix: str):
        prefixes = GLOBAL_DATA.get("channel_prefixes", [])
        if prefix in prefixes:
            prefixes.remove(prefix)
            save_data(GLOBAL_DATA)
            await ctx.send(embed=ok_embed("✅ Channel Prefix Removed", f"`{prefix}`"))
        else:
            await ctx.send(embed=err_embed("❌ Not Found", f"`{prefix}`"))

    @bot.command()
    @is_owner()
    async def memberncprefixadd(ctx: commands.Context, *, prefix: str):
        GLOBAL_DATA.setdefault("member_nc_prefixes", [])
        GLOBAL_DATA["member_nc_prefixes"].append(prefix)
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("✅ Member NC Prefix Added", f"`{prefix}`"))

    @bot.command()
    @is_owner()
    async def memberncprefixremove(ctx: commands.Context, *, prefix: str):
        prefixes = GLOBAL_DATA.get("member_nc_prefixes", [])
        if prefix in prefixes:
            prefixes.remove(prefix)
            save_data(GLOBAL_DATA)
            await ctx.send(embed=ok_embed("✅ Member NC Prefix Removed", f"`{prefix}`"))
        else:
            await ctx.send(embed=err_embed("❌ Not Found", f"`{prefix}`"))

    # ═══════════════════════════════════════════════════
    #  CUSTOM MESSAGES
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def custommessage(ctx: commands.Context, *, msg: str):
        bot.custom_channel_msgs[ctx.channel.id] = msg
        await ctx.send(embed=ok_embed("✅ Custom Message Started", f"Channel: {ctx.channel.mention}\nMsg: {msg}"))

    @bot.command()
    @is_owner()
    async def custommessagestop(ctx: commands.Context):
        bot.custom_channel_msgs.pop(ctx.channel.id, None)
        await ctx.send(embed=ok_embed("🛑 Custom Message Stopped", f"Channel: {ctx.channel.mention}"))

    @bot.command()
    @is_owner()
    async def custommessageall(ctx: commands.Context, *, msg: str):
        bot.custom_message_all_active = True
        bot.custom_message_all_msg = msg
        await ctx.send(embed=ok_embed("✅ Custom Message ALL Started", msg))

    @bot.command()
    @is_owner()
    async def custommessageallstop(ctx: commands.Context):
        bot.custom_message_all_active = False
        bot.custom_message_all_msg = None
        await ctx.send(embed=ok_embed("🛑 Custom Message ALL Stopped"))

    # ═══════════════════════════════════════════════════
    #  COPY MESSAGE
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def copymessage(ctx: commands.Context, user_id: int):
        GLOBAL_DATA["copied_user"] = user_id
        bot.copied_target = user_id
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("📋 Copy Message Active", f"Copying from <@{user_id}>"))

    @bot.command()
    @is_owner()
    async def copymessagestop(ctx: commands.Context):
        GLOBAL_DATA["copied_user"] = None
        bot.copied_target = None
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("🛑 Copy Message Stopped"))

    @bot.command()
    @is_owner()
    async def copiedmessagespam(ctx: commands.Context):
        global _copied_spam_active
        msgs = GLOBAL_DATA.get("copied_messages", [])
        if not msgs:
            return await ctx.send(embed=err_embed("❌ No Copied Messages", "Use `!copymessage <id>` first."))
        _copied_spam_active = True
        bot.copied_spam_active = True
        await ctx.send(embed=ok_embed("📋 Copied Messages Spam Started", f"Spamming `{len(msgs)}` message(s)."))

    @bot.command()
    @is_owner()
    async def copiedmessagespamstop(ctx: commands.Context):
        global _copied_spam_active
        _copied_spam_active = False
        bot.copied_spam_active = False
        await ctx.send(embed=ok_embed("🛑 Copied Messages Spam Stopped"))

    @bot.command()
    @is_owner()
    async def deletecopiedmessage(ctx: commands.Context):
        GLOBAL_DATA["copied_messages"] = []
        GLOBAL_DATA["copied_user"] = None
        bot.copied_target = None
        global _copied_spam_active
        _copied_spam_active = False
        bot.copied_spam_active = False
        save_data(GLOBAL_DATA)
        await ctx.send(embed=ok_embed("🗑️ Copied Messages Deleted"))

    # ═══════════════════════════════════════════════════
    #  NUKE / RAID
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def nuke(ctx: commands.Context, channel_name: str = "nuked", *, message: str = "@everyone GET NUKED ☢️"):
        if not ctx.guild:
            return await ctx.send(embed=err_embed("❌ Error", "Server-only command."))
        await ctx.send(embed=warn_embed("☢️ NUKE INITIATED", f"Channel: `{channel_name}`\nMsg: {message}"))
        deletes = [ch.delete() for ch in ctx.guild.channels]
        await asyncio.gather(*deletes, return_exceptions=True)
        created = 0
        for _ in range(50):
            try:
                await ctx.guild.create_text_channel(channel_name)
                created += 1
            except Exception:
                break
        bot.nuke_channel_name = channel_name
        bot.nuke_message = message
        bot.nuke_active = True
        bot._refresh_caches()
        await ctx.send(embed=ok_embed("☢️ Nuke Active", f"{created} channels created."))

    @bot.command()
    @is_owner()
    async def nukestop(ctx: commands.Context):
        bot.nuke_active = False
        await ctx.send(embed=ok_embed("🛑 Nuke Stopped"))

    @bot.command()
    @is_owner()
    async def raid(ctx: commands.Context, channel_name: str = "raided", *, message: str = "@everyone RAIDED 🚨"):
        if not ctx.guild:
            return await ctx.send(embed=err_embed("❌ Error", "Server-only command."))
        await ctx.send(embed=warn_embed("🚨 RAID INITIATED", f"Channel: `{channel_name}`\nMsg: {message}"))
        created = 0
        for _ in range(50):
            try:
                await ctx.guild.create_text_channel(channel_name)
                created += 1
            except Exception:
                break
        bot.raid_channel_name = channel_name
        bot.raid_message = message
        bot.raid_active = True
        bot._refresh_caches()
        await ctx.send(embed=ok_embed("🚨 Raid Active", f"{created} channels created."))

    @bot.command()
    @is_owner()
    async def raidstop(ctx: commands.Context):
        bot.raid_active = False
        await ctx.send(embed=ok_embed("🛑 Raid Stopped"))

    # ═══════════════════════════════════════════════════
    #  LONGSPAM (multi-channel + 50 lines)
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def longspam(ctx: commands.Context, *, text: str):
        """Add current channel to longspam list."""
        if ctx.channel.id in bot.longspam_channels:
            await ctx.send(embed=err_embed("⚠️ Already longspamming here!", "Use `!longspamstop` first."))
            return

        bot.longspam_channels[ctx.channel.id] = text

        embed = discord.Embed(
            title="📝 **LONGSPAM ADDED (50 LINES PER MSG)**",
            description=f"Longspamming `{text}` in {ctx.channel.mention}",
            color=WARN_COLOR
        )
        embed.add_field(
            name="📊 Active Channels",
            value=f"Currently longspamming in **{len(bot.longspam_channels)}** channel(s)",
            inline=False
        )
        embed.add_field(
            name="💡 Format",
            value="Each message = 50 lines of `{text} {emoji}`. The emoji changes every message.",
            inline=False
        )
        embed.add_field(name="To Stop", value="Use `!longspamstop` (this channel) or `!stopall`", inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    @is_owner()
    async def longspamstop(ctx: commands.Context):
        """Stop longspam in current channel only."""
        if ctx.channel.id in bot.longspam_channels:
            bot.longspam_channels.pop(ctx.channel.id, None)
            await ctx.send(embed=ok_embed(
                "🛑 Longspam Stopped",
                f"Stopped in {ctx.channel.mention}\n**Still active in {len(bot.longspam_channels)} channel(s)**"
            ))
        else:
            await ctx.send(embed=err_embed("❌ Error", "No active longspam in this channel."))

    @bot.command()
    @is_owner()
    async def longspamall(ctx: commands.Context, *, text: str):
        if not ctx.guild:
            return await ctx.send(embed=err_embed("❌ Error", "Server-only command."))
        bot.longspam_all_active = True
        bot.longspam_all_text = text
        bot._refresh_caches()
        await ctx.send(embed=ok_embed("📝 Longspam ALL Started", f"Text: `{text}` (50 lines per message)"))

    @bot.command()
    @is_owner()
    async def longspamallstop(ctx: commands.Context):
        bot.longspam_all_active = False
        bot.longspam_all_text = None
        await ctx.send(embed=ok_embed("🛑 Longspam ALL Stopped"))

    # ═══════════════════════════════════════════════════
    #  STOP ALL
    # ═══════════════════════════════════════════════════
    @bot.command()
    @is_owner()
    async def stopall(ctx: commands.Context):
        bot.tracked_dms.clear()
        bot.tracked_channels.clear()
        bot.custom_dms.clear()
        bot.auto_replies.clear()

        bot.dm_spam_all_active = False
        bot.custom_dm_spam_all_active = False
        bot.custom_dm_spam_all_msg = None

        bot.custom_channel_msgs.clear()
        bot.custom_message_all_active = False
        bot.custom_message_all_msg = None

        bot.nuke_active = False
        bot.raid_active = False

        bot.server_nc_active = False
        bot.channel_nc_active = False
        bot.member_nc_active = False
        bot.member_nc_target = None

        bot.target_name = None

        bot.copied_target = None
        GLOBAL_DATA["copied_user"] = None
        global _copied_spam_active
        _copied_spam_active = False
        bot.copied_spam_active = False
        save_data(GLOBAL_DATA)

        # Stop Longspam (all channels)
        bot.longspam_channels.clear()
        bot.longspam_all_active = False
        bot.longspam_all_text = None

        # Stop Spam cmd (all channels)
        bot.spam_cmd_channels.clear()
        bot._spam_last_send.clear()

        # Stop Roast Spam (all channels)
        for cid, cfg in list(bot.roast_spam_channels.items()):
            if cfg.get("task") and not cfg["task"].done():
                cfg["task"].cancel()
        bot.roast_spam_channels.clear()

        # Stop All Roast Spam (server-wide)
        bot.all_roast_spam_active = False
        bot.all_roast_spam_target = None
        bot.all_roast_spam_guild_id = None

        # Stop Bypass Spam
        bot.byp_spam_active = False
        bot.byp_spam_target = None
        bot.byp_spam_channel_id = None

        # Stop Bypass Channel Add
        bot.byp_channel_add_active = False
        bot.byp_channel_add_name = None
        bot.byp_channel_add_guild_id = None
        bot.byp_channel_add_created = 0

        # Stop Auto React
        bot.auto_react_enabled = False

        await ctx.send(embed=ok_embed("🛑 STOP ALL", "All active features have been stopped successfully!"))

    # ═══════════════════════════════════════════════════
    #  UTILITY
    # ═══════════════════════════════════════════════════
    @bot.command()
    async def ping(ctx: commands.Context):
        await ctx.send(embed=info_embed("🏓 Pong", f"Latency: `{round(bot.latency * 1000)}ms`"))

    @bot.command()
    @is_owner()
    async def rename(ctx: commands.Context, *, name: str):
        try:
            await bot.user.edit(username=name)
            await ctx.send(embed=ok_embed("✅ Renamed", f"Now: `{name}`"))
        except Exception as e:
            await ctx.send(embed=err_embed("❌ Rename Failed", str(e)))

    @bot.command()
    @is_owner()
    async def shutdown(ctx: commands.Context):
        await ctx.send(embed=err_embed("🛑 SHUTDOWN", "All bots terminating now..."))
        os._exit(0)

    def warn_embed(title: str, desc: str = "") -> discord.Embed:
        return discord.Embed(title=title, description=desc, color=WARN_COLOR)

    globals()["warn_embed"] = warn_embed


# Add copied_spam_active attribute to UnifiedBot
UnifiedBot.copied_spam_active = False


# ═══════════════════════════════════════════════════════════════════
#  MULTI-TOKEN RUNNER
# ═══════════════════════════════════════════════════════════════════

async def start_instance(token: str, index: int):
    bot = UnifiedBot(index)
    register_commands(bot)
    try:
        await bot.start(token)
    except Exception as e:
        print(f"[Bot #{index}] ❌ Failed: {e}")

async def main():
    await asyncio.gather(*[start_instance(t, i + 1) for i, t in enumerate(BOT_TOKENS)])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutdown by user.")
        os._exit(0)
