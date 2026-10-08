import requests
import json
import os
import time
import random
import threading
import websocket
from datetime import datetime, timedelta
import pytz


OWNER_ID = "1521409217011908608" 

BOT_TOKENS = [
    "MTU1MDc1ODAzMjcyMjQ5MzUxNw.GPjra9.bZnFOeK8Q7jgOTQKBOMYzbnNDx3PH7IlxMQezs",
]

BOT_SETTINGS = {}


SAVED_PIC_PATH = "turbo_pfp.jpg"
MENU_VIDEO_PATH = "help.mp4"
SUDO_FILE = "sudo_users.json"
PREFIX = "~"

TURBO_EMOJIS = ["🔥", "💀", "👑", "⚡", "🌀", "🩸", "💎", "🌌", "☠️", "🖤", "👹", "🔱"]
LUNDSAKI_EMOJIS = ["❄️", "🌪️", "⚡", "🌨️", "🕸️", "🌋", "🌀", "🎀", "🧸"]

class BotState:
    def __init__(self):
        self.ACTIVE_NC_CHANNELS = {}
        self.ACTIVE_SPAM_CHANNELS = {}
        self.ACTIVE_PIC_CHANNELS = {}
        self.ACTIVE_RAID_CHANNELS = {}
        self.ACTIVE_TIMESPAM_CHANNELS = {}
        self.ACTIVE_CUSTOM_SPAM_CHANNELS = {}
        self.ACTIVE_TRYHARD_CHANNELS = {}
        self.ACTIVE_PIN_CHANNELS = {}
        self.ACTIVE_DELETE_CHANNELS = {}
        self.ACTIVE_TURBO_SPAM_CHANNELS = {}  
        self.ACTIVE_LUNDSAKI_CHANNELS = {}
        self.AUTOREACT_EMOJI = {}
        self.TARGET_USER_ID = None
        self.START_TIME = time.time()
        self.GLOBAL_DELAY = 0.1
        self.PIC_DELAY = 1.0
        self.NC_DELAY = 1.5
        self.SUDO_USERS = []
        self.OWNER_ID = OWNER_ID

BOT_STATES = {}


NC_POOLS = {
    "base": ["💤", "🎀", "💋", "💗"], "lightning": ["⚡", "💫", "✨", "🌟"],
    "heart": ["🩵", "💙", "🤍", "💜"], "keng": ["👑", "🔱", "⚜️", "〽️"],
    "time": ["🕐", "🕑", "🕒", "🕓", "⏱️"], "animal": ["🦁", "🦅", "🐺", "🦂", "🐍", "🐆", "🦈"],
    "gothic": ["⛓️‍💥", "🖤", "☠️", "⚔️", "🥀", "🕯️", "🎭"], "cosmic": ["🌌", "🪐", "🌟", "☄️", "🛸", "🔮", "🌀"],
    "viper": ["🧪", "☣️", "💚", "🔋", "🩻", "🦠", "🧬"], "demon": ["👹", "🔥", "🏮", "👁️‍🗨️", "🩸", "🏛️", "🔱"],
    "ocean": ["🌊", "🦈", "🐙", "⚓", "🐬", "🐳", "💧"], "frost": ["❄️", "🥶", "🧊", "🏔️", "💎", "🌨️", "🔮"],
    "cyber": ["🤖", "💻", "💾", "📡", "👾", "⚙️", "🔋"], "toxic": ["🤢", "☣️", "☢️", "⚠️", "🛑", "🗑️", "🤮"],
    "royal": ["👑", "🏰", "⚜️", "💎", "💰", "🧝", "🦁"], "voodoo": ["🔮", "🧿", "🪄", "🧙", "🕯️", "🎴", "🃏"],
    "undead": ["💀", "👻", "🧟", "⚰️", "🥀", "🖤", "🪦"], "ninja": ["🥷", "🗡️", "⚔️", "🏮", "⛩️", "🉐", "💨"],
    "samurai": ["👺", "⚔️", "🛡️", "💮", "🗻", "🏯", "🩸"], "arcade": ["🕹️", "🎰", "👾", "🎲", "🎟️", "💥", "🏁"],
    "shadow": ["🥷", "🌑", "🕷️", "🕸️"], "hazard": ["☣️", "⚠️", "🛑", "⚡"],
    "matrix": ["🟢", "📟", "🔋", "💻"], "phantom": ["👻", "🌫️", "🔮", "⛓️"],
    "galaxy": ["🌌", "🚀", "🪐", "🌠"], "valiant": ["🛡️", "⚔️", "🦅", "🎖️"],
    "glitch": ["🎛️", "🎚️", "🔌", "📡"], "inferno": ["🔥", "🌋", "💥", "☄️"],
    "dynasty": ["🏮", "⛩️", "🉐", "👑"], "rebel": ["🏴‍☠️", "💣", "⚔️", "💥"]
}

CUSTOM_NC_PHRASES = ["𝘎𝘈𝘠", "𝙉𝙄𝙂𝙂𝘼", "𝙁𝘼𝙏𝙃𝙀𝙍𝙇𝙀𝙎𝙎", "Bɪᴛᴄʜ", "᭙ꫀꪖ𝘬", "𝘴ꪶàꪜꫀ", "𝑫𝑰𝑪𝑲 𝑬𝑨𝑻𝑬𝑹", "𝖲𝖫𝖴𝖳"]
RAID_PHRASES = ['𓂃˖˳·˖ ִֶָ ⋆❤️͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚❤️ ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆🧡͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚🧡 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆💛͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚💛 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆💚͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚💚 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆💙͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚💙 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆💜͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚💜 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆🖤͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚🖤 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆🤍͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚🤍 ݁˖⭑.',
    '𓂃˖˳·˖ ִֶָ ⋆🤎͙⋆ ִֶָ˖·˳˖𓂃 ִֶָ⁀➴༯ sꪶꪖꪜꫀ ִֶָ. ..𓂃 ࣪ ִֶָ🌈་༘࿐ 𝗟𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 -/- ⋆˚🤎 ݁˖⭑.',]
CHANNEL_PHRASES = ["˙✧˖°📷༘ ⋆｡° 𝐓ᴇʀʏ 𝐌ᴀ  𝐊ᴀ 𝐂ʜɪʟᴅ 𝐏ᴏʀɴ 𝐑ᴇᴄᴏʀᴅ 𝐇ᴏɢʏᴀ 𝐀ʙ 𝐓ᴏ 𝐒ɪᴅʜᴀ 𝐕ɪʀᴀʟ 𝐇ᴏɢᴀ 𝐘ᴇ ˙✧˖°📷༘ ⋆｡°", "तेरे मां के दूदू के बीच मेरा lund fas gaya oops 🤪（ ͜.🍆 ͜.）", "𓂃✍︎ 𝑵ʏ 𝑵ʏ 𝑨ʙ 𝑲ᴜᴄʜ 𝑵ʏ 𝑯ᴏ 𝑺ᴋᴛᴀ 𝑻ᴇʀɪ  𝑪ᴜᴅᴀɪ 𝑲ɪ 𝑺ᴄʀɪᴘᴛ 𝑨ʙ 𝑳ᴇᴀᴋ 𝐇ᴏᴋᴇ 𝐇ʏ 𝐌ᴀɴᴇɢɪ 𓂃✍︎", "𓂃☁︎ 𓂃𝐒ɪᴅᴇ 𝐇ᴀᴛ 𝐆ᴜʟᴀᴍ 𝐓ᴇʀʏ 𝐌ᴀᴀ 𝐊ᴏ 𝐂ʜᴏᴅɴᴇ  मेरी रेलगाड़ी आ रही .-‘🚂-‘.ᯓᡣ𐭩__ 𓂃☁︎ 𓂃"]

SPAM_PRESETS = {
    "1": "🔥☄️🧨", "2": "👑🔱🛡️", "3": "☠️⛓️⚙️", "4": "🌌🔮🌀",
    "5": "☣️⚠️🚨", "6": "🩸👹🃏", "7": "💎💵💸", "8": "🌊🧊❄️"
}

TRYHARD_FONTS = [
     "चुदाई Kha 😂❤️", "उठक बैठक लगा 😏🔥", "तेरी माँ चोदू 😍😍", 
    "ओय कमजोर 🤢🤢", "लंड चूस 🥱🤍➿", "पिल्लै 🐕‍", "😱 arey 😉 ye 🤡 kaise 😋 kiya 😏 re 😁 teri 😊 maa 😍 randy 😭100% 😂",
    "कमजोर टट्टा","👈🏻👆🏻🖖🏻👇🏻🤲🏻👉🏻🤏🏻 Idr Udr Jidr Bhi Dekhega Teri Randi Maa Dikhegi",
    " 𝘽𝙀𝙏𝘼 🤢᭄᭄᭄᭄ 🌟 𝙇𝙐𝙉𝘿 𝘾𝙃𝙐𝙎 🤪᭄᭄","मदरचोद 🤮🤮", "ro 🤣🤣", "रंडी", "चुप tmr 😒😂",
    "Acha Beta ? Koi Na Mai Teri Maa Coduga 😹💥💯", "चुदकड़", "कमजोर पिल्ले 🤮👞", "Chup  Rndyce ⁉", "Tmkc Mein Mist Breathing ☁",
    " Teri माँ Dead 😂😂😂", "Teri Maa Chodu If Yes Then Reply To My Message 😂😂💯💯",
]


def load_sudo(bot_state):
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r") as f: 
                return json.load(f)
        except: 
            return []
    return []

def save_sudo(users):
    with open(SUDO_FILE, "w") as f: 
        json.dump(users, f)

def get_bot_id_from_token(token):
    try:
        r = requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token})
        if r.status_code == 200:
            return r.json().get('id')
        return None
    except: 
        return None

def get_discord_menu_1():
    p = PREFIX
    return (
        "```\n"
        " 𓆩💢𓆪━━━━━❄️ 𝐓ᴜʀʙᴏ 𝐕13 ❄️━━━━━ 𓆩💢𓆪\n"
        " 🧸❄️  <ᴅʀᥴꪶɀ> 𝘔𝘌𝘕𝘜❄️🧸 \n" 
        "━━━━━━━━━𝙭𝙏𝙪𝙧𝙗𝙤 𝘾𝙪𝙩𝙞𝙚 ›⟩ ❄️━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        " ❄️SYSTEM CONFIG:\n"
        "   » {p}PING\n"
        "   » {p}STATUS\n"
        "   » {p}DELAY (S)      • 𝖣𝖤𝖫𝖠𝖸 ( 𝖲𝖯𝖠𝖬/𝖱𝖠𝖨𝖣/𝖳𝖠𝖱𝖦𝖤𝖳)\n"
        "   » {p}COKENG @user\n"
        "   » {p}REMOVECOKENG\n"
        "   » {p}TARGET @user\n"
        "   » {p}STOPTARGET\n\n"
        " ❄️ALL 30 NC MODES:\n"
        "   » {p}NC (TXT)          {p}LIGHTNINGNC (TXT)  {p}HEARTNC (TXT)     {p}KENGNC (TXT)\n"
        "   » {p}TIMENC (TXT)      {p}ANIMALNC (TXT)     {p}GOTHICNC (TXT)    {p}COSMICNC (TXT)\n"
        "   » {p}VIPERNC (TXT)     {p}DEMONNC (TXT)      {p}OCEANNC (TXT)     {p}FROSTNC (TXT)\n"
        "   » {p}CYBERNC (TXT)     {p}TOXICNC (TXT)      {p}ROYALNC (TXT)     {p}VOODOONC (TXT)\n"
        "   » {p}UNDEADNC (TXT)    {p}NINJANC (TXT)      {p}SAMURAINC (TXT)   {p}ARCADENC (TXT)\n"
        "   » {p}SHADOWNC (TXT)    {p}HAZARDNC (TXT)     {p}MATRIXNC (TXT)    {p}PHANTOMNC (TXT)\n"
        "   » {p}GALAXYNC (TXT)    {p}VALIANTNC (TXT)    {p}GLITCHNC (TXT)    {p}INFERNONC (TXT)\n"
        "   » {p}DYNASTYNC (TXT)   {p}REBELNC (TXT)\n"
        "   » {p}BIGNC (TXT) \n"
        "   » {p}CUSTOMNC (TXT)\n"
        "   » {p}SLOWNC (TXT)\n"
        "   » {p}DELAYNC (S)    • NC DELAY 0.0 TO 5 SECONDS\n"
        "   » {p}STOPNC\n"
        "🧸❄️━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❄️🧸\n"
        "```"
    ).format(p=p)

def get_discord_menu_2():
    p = PREFIX
    return (
        "```\n"
        "🎀🕸️━━━━━🕸️TURBO V10 🕸️━━━━━🎀🕸️\n"
        "🧸❄️━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❄️🧸\n"
        " ❄️SPAM MODES:\n"
        "   » {p}SPAM (TXT)\n"
        "   » {p}CUSTOMSPAM (TXT)\n"
        "   » {p}TIMESPAM (TXT)\n"
        "   » {p}RAID\n"
        "   » {p}STOPRAID\n"
        "   » {p}SPAM1 (TXT) TO {p}SPAM8 (TXT)\n"
        "   » {p}LEGITSPAM (TXT)\n"
        "   » {p}STOPLEGITSPAM\n"
        "   » {p}LUNDSAKI (TXT)\n"
        "   » {p}STOPLUNDSAKI\n"
        "   » {p}STOPSPAM\n\n"
        " ❄️ TRYHARD <ᴅᴄʀʟᴢ>:\n"
        "   » {p}TRYHARD (TXT)\n"
        "   » {p}STOPTRYHARD\n\n"
        " ❄️ PIC & REACTIONS:\n"
        "   » {p}SPAMPICS\n"
        "   » {p}STOPPIC\n"
        "   » {p}SAVEPIC\n"
        "   » {p}REACT [EMOJI]\n"
        "   » {p}STOPREACT\n\n"
        " ❄️PIC DELAY / STOPALL:\n"
        "   » {p}PINMESSAGE\n"
        "   » {p}DELETEMSG\n"
        "   » {p}DELAYPIC\n"
        "   » {p}STOPALL\n\n"
        " ❄️BOT MANAGEMENT:\n"
        "   » {p}LEFT\n"
        "   » {p}GCLEFT\n"
        "   » {p}CLEFT @bot\n"
        "   » {p}JOIN [CODE]\n"
        "   » {p}XJOIN [CODE] \n"
        "   » {p}ADD @bot [CODE] \n"
        " ❄️ FRIEND MANAGEMENT:\n"
        "   » {p}SENDFR @user [@bot] \n"
        "   » {p}ACCEPTFR @user [@bot] \n"
        "   » {p}DISBAND\n"
        "🧸❄️━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❄️🧸\n"
        "```"
    ).format(p=p)

def send_msg(token, c_id, text, reply_to=None):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    payload = {"content": text}
    if reply_to: 
        payload["message_reference"] = {"channel_id": c_id, "message_id": reply_to}
    return requests.post(f"https://discord.com/api/v9/channels/{c_id}/messages", headers=headers, json=payload)

def change_gc_name(token, g_id, name):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    formatted_name = name.lower().replace(" ", "-") if "-" in name or " " in name else name.upper()
    return requests.patch(f"https://discord.com/api/v9/channels/{g_id}", headers=headers, json={"name": formatted_name})

def add_reaction(token, c_id, m_id, emoji):
    encoded_emoji = requests.utils.quote(emoji)
    url = f"https://discord.com/api/v9/channels/{c_id}/messages/{m_id}/reactions/{encoded_emoji}/@me"
    requests.put(url, headers={"Authorization": token})

def resolve_user_id(token, user_mention):
    """Resolve a user mention or username to a user ID"""
    if user_mention.startswith("<@") and user_mention.endswith(">"):
        user_id = user_mention.replace("<@", "").replace(">", "").replace("!", "")
        return user_id, "User"
    
    if user_mention.isdigit():
        return user_mention, "User"
    
    return None, None


def send_friend_request(token, user_id):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    try:
        user_response = requests.get(f"https://discord.com/api/v9/users/{user_id}", headers={"Authorization": token})
        if user_response.status_code != 200:
            return False, "User not found or bot cannot access this user"
        
        response = requests.put(f"https://discord.com/api/v9/users/@me/relationships/{user_id}", 
                               headers=headers, json={})
        if response.status_code == 204:
            return True, "Friend request sent successfully"
        elif response.status_code == 400:
            return False, "Already friends or request already pending"
        elif response.status_code == 429:
            return False, "Rate limited, please wait"
        else:
            return False, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def accept_friend_request(token, user_id):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    try:
        response = requests.put(f"https://discord.com/api/v9/users/@me/relationships/{user_id}", 
                               headers=headers, json={})
        if response.status_code == 204:
            return True, "Friend request accepted"
        elif response.status_code == 400:
            return False, "No pending request or already friends"
        else:
            return False, f"Error {response.status_code}"
    except Exception as e:
        return False, str(e)

def disband_group_chat(token, channel_id):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    try:
        channel_response = requests.get(f"https://discord.com/api/v9/channels/{channel_id}", headers=headers)
        if channel_response.status_code != 200:
            return False, "Failed to get channel info"
        
        channel_data = channel_response.json()
        
        if channel_data.get("type") != 3:
            return False, "Not a group chat"
        
        recipients = channel_data.get("recipients", [])
        removed_count = 0
        
        for recipient in recipients:
            user_id = recipient.get("id")
            if user_id:
                remove_response = requests.delete(
                    f"https://discord.com/api/v9/channels/{channel_id}/recipients/{user_id}",
                    headers=headers
                )
                if remove_response.status_code in [200, 204]:
                    removed_count += 1
                time.sleep(0.3)
        
        leave_response = requests.delete(
            f"https://discord.com/api/v9/channels/{channel_id}",
            headers=headers
        )
        
        if leave_response.status_code in [200, 204]:
            return True, f"Disbanded group chat, removed {removed_count} members"
        else:
            return False, f"Failed to leave group, removed {removed_count} members"
    except Exception as e:
        return False, str(e)


def leave_guild(token, guild_id):
    headers = {"Authorization": token}
    url = f"https://discord.com/api/v9/users/@me/guilds/{guild_id}"
    try:
        response = requests.delete(url, headers=headers)
        return response.status_code == 204
    except:
        return False

def leave_group_chat(token, channel_id):
    headers = {"Authorization": token}
    url = f"https://discord.com/api/v9/channels/{channel_id}"
    try:
        response = requests.delete(url, headers=headers)
        return response.status_code in [200, 204]
    except:
        return False

def join_guild(token, invite_code):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    invite_code = invite_code.strip()
    if "/" in invite_code:
        invite_code = invite_code.split("/")[-1]
    if "discord.gg/" in invite_code:
        invite_code = invite_code.replace("discord.gg/", "")
    if "discord.com/invite/" in invite_code:
        invite_code = invite_code.replace("discord.com/invite/", "")
    
    url = f"https://discord.com/api/v9/invites/{invite_code}"
    try:
        response = requests.post(url, headers=headers)
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"[-] Join failed with status {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[-] Join exception: {e}")
        return False

def get_bot_info(token):
    try:
        response = requests.get("https://discord.com/api/v9/users/@me", 
                               headers={"Authorization": token})
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def find_bot_token_by_id(bot_id):
    for bot_token in BOT_TOKENS:
        if not bot_token or bot_token in ["YOUR_SECOND_BOT_TOKEN_HERE", "YOUR_THIRD_BOT_TOKEN_HERE"]:
            continue
        try:
            bot_info = get_bot_info(bot_token)
            if bot_info and bot_info.get("id") == bot_id:
                return bot_token
        except:
            continue
    return None

def get_bot_name_from_token(token):
    try:
        bot_info = get_bot_info(token)
        if bot_info:
            return bot_info.get("username", "Unknown Bot")
        return "Unknown Bot"
    except:
        return "Unknown Bot"

# ==================== WORKERS ====================
def nc_worker(token, bot_state, g_id, pool_key, mode="NORMAL", text_content=""):
    tz = pytz.timezone('Asia/Kolkata')
    
    while bot_state.ACTIVE_NC_CHANNELS.get(g_id, False):
        try:
            if pool_key == "CUSTOM":
                phrase = random.choice(CUSTOM_NC_PHRASES)
                text = f"{text_content} {phrase}".strip()
            elif pool_key == "SLOW":
                all_emojis = []
                for p in NC_POOLS.values(): 
                    all_emojis.extend(p)
                text = f"{text_content} {random.choice(all_emojis)}".strip()
            else:
                if pool_key == "ALL":
                    # NEW: big NC with fixed decoration
                    emoji = random.choice([e for pool in NC_POOLS.values() for e in pool])
                    decoration = "𝘾𝙃𝙐𝙋 𝙈𝘼𝙆𝙀𝙇𝙊𝘿𝙀 𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫𒐫🩷𒐫𒐫"
                    text = f"{text_content} {decoration} {emoji}".strip()
                else:
                    emoji_pool = NC_POOLS.get(pool_key, NC_POOLS["base"])
                    emoji = random.choice(emoji_pool)
                    if mode == "TIME": 
                        text = f"{text_content} {datetime.now(tz).strftime('%H:%M:%S')} {emoji}".strip()
                    else: 
                        text = f"{text_content} {emoji}".strip()
                
            response = change_gc_name(token, g_id, text)
            if response.status_code == 429:
                time.sleep(response.json().get("retry_after", 4.0))
            else:
                time.sleep(random.uniform(0.8, 1.0) if pool_key == "SLOW" else bot_state.NC_DELAY)
        except: 
            time.sleep(0.5)

def custom_spam_worker(token, bot_state, c_id, input_text):
    cascading_emojis = ["🚀", "🗻", "🩰", "💤", "☄️", "〽️"]
    while bot_state.ACTIVE_CUSTOM_SPAM_CHANNELS.get(c_id, False):
        try:
            for emoji in cascading_emojis:
                if not bot_state.ACTIVE_CUSTOM_SPAM_CHANNELS.get(c_id, False): 
                    break
                block_lines = []
                for _ in range(44):
                    block_lines.append(f"{input_text} SLAVE {emoji}".upper())
                final_payload_text = "\n".join(block_lines)
                res = requests.post(f"https://discord.com/api/v9/channels/{c_id}/messages", 
                                   headers={"Authorization": token}, 
                                   json={"content": final_payload_text}, timeout=5)
                if res.status_code == 429:
                    time.sleep(res.json().get("retry_after", 2.0))
                else:
                    time.sleep(bot_state.GLOBAL_DELAY)
        except:
            time.sleep(1)

def tryhard_worker(token, bot_state, c_id, input_text):
    msg_counter = 0
    url = f"https://discord.com/api/v9/channels/{c_id}/messages"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    
    while bot_state.ACTIVE_TRYHARD_CHANNELS.get(c_id, False):
        try:
            shuffled_fonts = list(TRYHARD_FONTS)
            random.shuffle(shuffled_fonts)
            
            for font_style in shuffled_fonts:
                if not bot_state.ACTIVE_TRYHARD_CHANNELS.get(c_id, False): 
                    break
                
                if msg_counter >= 300:
                    time.sleep(2.0)
                    msg_counter = 0
                    
                payload_text = f"{font_style} {input_text}".upper()
                res = requests.post(url, headers=headers, json={"content": payload_text}, timeout=2)
                
                if res.status_code == 429:
                    time.sleep(res.json().get("retry_after", 1.0))
                else:
                    msg_counter += 1
                    time.sleep(bot_state.GLOBAL_DELAY)
        except:
            time.sleep(0.2)

def spam_worker(token, bot_state, c_id, spam_type="TEXT", text_content="", reply_target_id=None):
    headers = {"Authorization": token}
    tz = pytz.timezone('Asia/Kolkata')
    msg_counter = 0
    
    while True:
        if spam_type == "TEXT" and not bot_state.ACTIVE_SPAM_CHANNELS.get(c_id, False): 
            break
        if spam_type == "RAID" and not bot_state.ACTIVE_RAID_CHANNELS.get(c_id, False): 
            break
        if spam_type == "TIMESPAM" and not bot_state.ACTIVE_TIMESPAM_CHANNELS.get(c_id, False): 
            break
        if spam_type == "PIC" and not bot_state.ACTIVE_PIC_CHANNELS.get(c_id, False): 
            break
        
        try:
            if msg_counter >= 300:
                time.sleep(2.0)
                msg_counter = 0
                
            url = f"https://discord.com/api/v9/channels/{c_id}/messages"
            
            if spam_type == "PIC":
                if os.path.exists(SAVED_PIC_PATH):
                    with open(SAVED_PIC_PATH, "rb") as f:
                        res = requests.post(url, headers=headers, 
                                          files={"file": (SAVED_PIC_PATH, f, "image/jpeg")}, timeout=5)
                        if res.status_code == 429: 
                            time.sleep(res.json().get("retry_after", 2.0))
                else:
                    time.sleep(1.0)
                    continue
            elif spam_type == "RAID":
                payload = {"content": random.choice(RAID_PHRASES).upper()}
                if reply_target_id: 
                    payload["message_reference"] = {"channel_id": c_id, "message_id": reply_target_id}
                res = requests.post(url, headers=headers, json=payload, timeout=2)
                if res.status_code == 429: 
                    time.sleep(res.json().get("retry_after", 2.0))
            elif spam_type == "TIMESPAM":
                time_str = datetime.now(tz).strftime('%H:%M:%S')
                res = requests.post(url, headers=headers, 
                                  json={"content": f"{text_content} | {time_str}".upper()}, timeout=2)
                if res.status_code == 429: 
                    time.sleep(res.json().get("retry_after", 2.0))
            else:
                res = requests.post(url, headers=headers, 
                                  json={"content": text_content.upper()}, timeout=2)
                if res.status_code == 429: 
                    time.sleep(res.json().get("retry_after", 2.0))
            
            msg_counter += 1
            time.sleep(bot_state.PIC_DELAY if spam_type == "PIC" else bot_state.GLOBAL_DELAY)
        except: 
            time.sleep(1)

def auto_delete_worker(token, bot_state, c_id):
    headers = {"Authorization": token}
    while bot_state.ACTIVE_DELETE_CHANNELS.get(c_id, False):
        try:
            res = requests.get(f"https://discord.com/api/v9/channels/{c_id}/messages?limit=50", headers=headers)
            if res.status_code == 200:
                messages = res.json()
                now = datetime.utcnow()
                for msg in messages:
                    if not bot_state.ACTIVE_DELETE_CHANNELS.get(c_id, False): 
                        break
                    if msg["author"]["id"] == bot_state.OWNER_ID:
                        ts_str = msg["timestamp"].replace("+00:00", "")
                        try:
                            msg_time = datetime.fromisoformat(ts_str)
                        except:
                            msg_time = datetime.strptime(ts_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                        
                        if now - msg_time < timedelta(minutes=10):
                            requests.delete(f"https://discord.com/api/v9/channels/{c_id}/messages/{msg['id']}", 
                                          headers=headers)
                            time.sleep(0.4)
            time.sleep(5.0)
        except:
            time.sleep(5.0)


def turbo_spam_worker(token, bot_state, c_id, name):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    url = f"https://discord.com/api/v9/channels/{c_id}/messages"
    
    while bot_state.ACTIVE_TURBO_SPAM_CHANNELS.get(c_id, False):
        try:
            emoji1 = random.choice(TURBO_EMOJIS)
            emoji2 = random.choice(TURBO_EMOJIS)
            base_text = f"{name} 𝐑ɴᴅʏ 𝐊ᴇ 𝐋ᴀᴅᴄᴇ 𝐓ᴇʀɪ 𝐌ᴀ 𝐊ɪ 𝐂ʜᴜᴛ 𓆩{emoji1}𓆪"
            spacing = "\n" * 40
            final_text = base_text + spacing + base_text
            if len(final_text) > 2000:
                spacing = "\n" * 28
                final_text = base_text + spacing + base_text
            
            res = requests.post(url, headers=headers, json={"content": final_text}, timeout=5)
            if res.status_code == 429:
                retry_after = res.json().get("retry_after", 2.0)
                time.sleep(retry_after)
            elif res.status_code == 400:
                try:
                    error_data = res.json()
                    if "content" in str(error_data) and "too long" in str(error_data):
                        spacing = "\n" * 15
                        final_text = base_text + spacing + base_text
                        res = requests.post(url, headers=headers, json={"content": final_text}, timeout=5)
                except:
                    pass
                time.sleep(1)
            else:
                time.sleep(bot_state.GLOBAL_DELAY)
        except Exception as e:
            print(f"[-] Turbo spam error: {e}")
            time.sleep(1)


def lundsaki_worker(token, bot_state, c_id, name):
    headers = {"Authorization": token, "Content-Type": "application/json"}
    url = f"https://discord.com/api/v9/channels/{c_id}/messages"
    
    while bot_state.ACTIVE_LUNDSAKI_CHANNELS.get(c_id, False):
        try:
            emoji = random.choice(LUNDSAKI_EMOJIS)
            base_text = f"{name}#𝗧𝗨𝗠𝗛𝗔𝗥𝗜#𝗠𝗔𝗔#𝗞𝗘#𝗕𝗛⭕𝗦𝗗𝗘#𝗠𝗘#𝗟𝗢𝗗𝗔𝗔𓆩{emoji}𓆪"
            spacing = "\n" * 50
            final_text = base_text + spacing + base_text
            if len(final_text) > 2000:
                spacing = "\n" * 30
                final_text = base_text + spacing + base_text
            
            res = requests.post(url, headers=headers, json={"content": final_text}, timeout=5)
            if res.status_code == 429:
                time.sleep(res.json().get("retry_after", 2.0))
            else:
                time.sleep(bot_state.GLOBAL_DELAY)
        except Exception as e:
            print(f"[-] Lundsaki spam error: {e}")
            time.sleep(1)


def on_message(ws, message, token, bot_state):
    data = json.loads(message)
    
    if data.get("op") == 10:
        heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
        def heartbeat():
            while True:
                time.sleep(heartbeat_interval)
                try: 
                    ws.send(json.dumps({"op": 1, "d": None}))
                except: 
                    break
        threading.Thread(target=heartbeat, daemon=True).start()
        ws.send(json.dumps({"op": 2, "d": {"token": token, "properties": {"$os": "windows", "$browser": "chrome", "$device": "pc"}}}))

    if data.get("t") == "MESSAGE_CREATE":
        msg = data["d"]
        auth_id = msg["author"]["id"]
        content = msg["content"].strip()
        c_id = msg["channel_id"]
        m_id = msg["id"]

        if c_id in bot_state.AUTOREACT_EMOJI:
            threading.Thread(target=add_reaction, args=(token, c_id, m_id, bot_state.AUTOREACT_EMOJI[c_id]), daemon=True).start()

        if bot_state.TARGET_USER_ID and auth_id == bot_state.TARGET_USER_ID:
            try: 
                send_msg(token, c_id, random.choice(CHANNEL_PHRASES).upper(), reply_to=m_id)
            except: 
                pass

        if bot_state.ACTIVE_PIN_CHANNELS.get(c_id, False) and auth_id == bot_state.OWNER_ID:
            if not content.startswith(PREFIX + "pinmessage") and not content.startswith(PREFIX + "stopall"):
                requests.put(f"https://discord.com/api/v9/channels/{c_id}/pins/{m_id}", 
                           headers={"Authorization": token})

        if not content.startswith(PREFIX):
            return

        IS_AUTHORIZED = (auth_id == bot_state.OWNER_ID or auth_id in bot_state.SUDO_USERS)
        if not IS_AUTHORIZED:
            send_msg(token, c_id, "TURBO BAAP KA BOT USE KAREGA 😂", reply_to=m_id)
            return

        cmd_part = content[len(PREFIX):].strip()
        cmd_lower = cmd_part.lower()

        # ==================== HELP / MENU COMMANDS ====================
        if cmd_lower == "help":
            headers = {"Authorization": token}
            if os.path.exists(MENU_VIDEO_PATH):
                with open(MENU_VIDEO_PATH, "rb") as f:
                    form_data_1 = {"content": (None, get_discord_menu_1())}
                    requests.post(f"https://discord.com/api/v9/channels/{c_id}/messages", 
                                headers=headers, data=form_data_1)
                    
                    f.seek(0)
                    form_data_2 = {
                        "content": (None, get_discord_menu_2()),
                        "file": (os.path.basename(MENU_VIDEO_PATH), f, "video/mp4")
                    }
                    requests.post(f"https://discord.com/api/v9/channels/{c_id}/messages", 
                                headers=headers, files=form_data_2)
            else:
                send_msg(token, c_id, get_discord_menu_1())
                send_msg(token, c_id, get_discord_menu_2() + "\n\n⚠️ [SYSTEM WARNING: VIDEO NOT FOUND]")

        elif cmd_lower == "nc":
            send_msg(token, c_id, get_discord_menu_1())

        elif cmd_lower == "spam":
            send_msg(token, c_id, get_discord_menu_2())

        elif cmd_lower == "menu":
            send_msg(token, c_id, get_discord_menu_1())
            send_msg(token, c_id, get_discord_menu_2())

        # ==================== SYSTEM COMMANDS ====================
        elif cmd_lower == "ping":
            start = time.time()
            requests.get("https://discord.com/api/v9/users/@me", headers={"Authorization": token})
            send_msg(token, c_id, f"💤 **PING:** {round((time.time() - start) * 1000, 2)}MS")

        elif cmd_lower == "status":
            uptime = round(time.time() - bot_state.START_TIME, 1)
            status_text = (
                "```\n"
                f"╔═════════ TURBO SELF BOT STATUS ═════════╗\n"
                f" SYSTEM ACTIVE  : {uptime} SECONDS\n"
                f" GLOBAL DELAY   : {bot_state.GLOBAL_DELAY}s\n"
                f" PIC SPAM DELAY : {bot_state.PIC_DELAY}s\n"
                f" ACTIVE PREFIX  : {PREFIX}\n"
                f" TARGET ID LOCK : {bot_state.TARGET_USER_ID}\n"
                "╚══════════════════════════════════════╝\n"
                "```"
            )
            send_msg(token, c_id, status_text)

        elif cmd_lower.startswith("target "):
            try:
                bot_state.TARGET_USER_ID = cmd_part.split("@")[1].replace(">", "").strip()
                send_msg(token, c_id, f"TARGET IS LOCKED ONTO ID: {bot_state.TARGET_USER_ID}")
            except:
                send_msg(token, c_id, "USE: !target @user")

        elif cmd_lower == "stoptarget":
            bot_state.TARGET_USER_ID = None
            send_msg(token, c_id, "TARGET HAS BEEN STOPPED")

        elif cmd_lower.startswith("cokeng "):
            try:
                sid = cmd_part.split("@")[1].replace(">", "").strip()
                if sid not in bot_state.SUDO_USERS:
                    bot_state.SUDO_USERS.append(sid)
                    save_sudo(bot_state.SUDO_USERS)
                    send_msg(token, c_id, "CO KENG IS ADDED")
            except: 
                pass

        elif cmd_lower.startswith("removecokeng "):
            try:
                sid = cmd_part.split("@")[1].replace(">", "").strip()
                if sid in bot_state.SUDO_USERS:
                    bot_state.SUDO_USERS.remove(sid)
                    save_sudo(bot_state.SUDO_USERS)
                    send_msg(token, c_id, "CO KENG IS REMOVED")
            except: 
                pass

        
        elif cmd_lower.startswith("sendfr "):
            try:
                parts = cmd_part.split()
                if len(parts) < 2:
                    send_msg(token, c_id, "❌ Usage: !sendfr @user [@bot]\nExample: !sendfr @User or !sendfr @User @MyBot", reply_to=m_id)
                    return
                
                target_mention = parts[1]
                target_user_id, username = resolve_user_id(token, target_mention)
                
                if not target_user_id:
                    send_msg(token, c_id, f"❌ User not found: {target_mention}\n💡 Try using the full @mention or user ID", reply_to=m_id)
                    return
                
                target_bot_token = None
                target_bot_name = None
                
                if len(parts) > 2:
                    bot_mention = parts[2]
                    if bot_mention.startswith("<@") and bot_mention.endswith(">"):
                        bot_id = bot_mention.replace("<@", "").replace(">", "").replace("!", "")
                        target_bot_token = find_bot_token_by_id(bot_id)
                        if target_bot_token:
                            target_bot_name = get_bot_name_from_token(target_bot_token)
                        else:
                            send_msg(token, c_id, f"❌ Bot <@{bot_id}> not found in token list!", reply_to=m_id)
                            return
                
                if not target_bot_token:
                    target_bot_token = token
                    target_bot_name = get_bot_name_from_token(token)
                
                send_msg(token, c_id, f"🔄 Sending friend request from **{target_bot_name}** to **{username}**...", reply_to=m_id)
                
                success, message = send_friend_request(target_bot_token, target_user_id)
                if success:
                    send_msg(token, c_id, f"✅ Friend request sent from **{target_bot_name}** to **{username}**!", reply_to=m_id)
                else:
                    send_msg(token, c_id, f"❌ {message}", reply_to=m_id)
            except Exception as e:
                send_msg(token, c_id, f"❌ Error: {str(e)}\nUsage: !sendfr @user [@bot]", reply_to=m_id)

        elif cmd_lower.startswith("acceptfr "):
            try:
                parts = cmd_part.split()
                if len(parts) < 2:
                    send_msg(token, c_id, "❌ Usage: !acceptfr @user [@bot]\nExample: !acceptfr @User or !acceptfr @User @MyBot", reply_to=m_id)
                    return
                
                target_mention = parts[1]
                target_user_id, username = resolve_user_id(token, target_mention)
                
                if not target_user_id:
                    send_msg(token, c_id, f"❌ User not found: {target_mention}\n💡 Try using the full @mention or user ID", reply_to=m_id)
                    return
                
                target_bot_token = None
                target_bot_name = None
                
                if len(parts) > 2:
                    bot_mention = parts[2]
                    if bot_mention.startswith("<@") and bot_mention.endswith(">"):
                        bot_id = bot_mention.replace("<@", "").replace(">", "").replace("!", "")
                        target_bot_token = find_bot_token_by_id(bot_id)
                        if target_bot_token:
                            target_bot_name = get_bot_name_from_token(target_bot_token)
                        else:
                            send_msg(token, c_id, f"❌ Bot <@{bot_id}> not found in token list!", reply_to=m_id)
                            return
                
                if not target_bot_token:
                    target_bot_token = token
                    target_bot_name = get_bot_name_from_token(token)
                
                send_msg(token, c_id, f"🔄 Accepting friend request from **{username}** for **{target_bot_name}**...", reply_to=m_id)
                
                success, message = accept_friend_request(target_bot_token, target_user_id)
                if success:
                    send_msg(token, c_id, f"✅ Friend request from **{username}** accepted for **{target_bot_name}**!", reply_to=m_id)
                else:
                    send_msg(token, c_id, f"❌ {message}", reply_to=m_id)
            except Exception as e:
                send_msg(token, c_id, f"❌ Error: {str(e)}\nUsage: !acceptfr @user [@bot]", reply_to=m_id)

        elif cmd_lower == "disband":
            try:
                channel_response = requests.get(f"https://discord.com/api/v9/channels/{c_id}", 
                                               headers={"Authorization": token})
                if channel_response.status_code != 200:
                    send_msg(token, c_id, "❌ Failed to get channel info!", reply_to=m_id)
                    return
                
                channel_data = channel_response.json()
                
                if channel_data.get("type") != 3:
                    send_msg(token, c_id, "❌ This command can only be used in a group chat!", reply_to=m_id)
                    return
                
                owner_name = get_bot_name_from_token(token)
                
                send_msg(token, c_id, f"💣 DISBANDING GROUP CHAT", reply_to=m_id)
                time.sleep(1)
                
                success, message = disband_group_chat(token, c_id)
                
                if success:
                    send_msg(token, c_id, f"✅ {message}", reply_to=m_id)
                else:
                    send_msg(token, c_id, f"❌ {message}", reply_to=m_id)
            except Exception as e:
                send_msg(token, c_id, f"❌ Error: {str(e)}", reply_to=m_id)

       
        elif cmd_lower == "left":
            guild_id = msg.get("guild_id")
            if not guild_id:
                send_msg(token, c_id, "❌ This command can only be used in a server!", reply_to=m_id)
                return
            
            try:
                guild_response = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}", 
                                             headers={"Authorization": token})
                guild_name = guild_response.json().get("name", "Unknown Server") if guild_response.status_code == 200 else "Unknown Server"
            except:
                guild_name = "Unknown Server"
            
            send_msg(token, c_id, f"🔄 Making all bots leave **{guild_name}**...", reply_to=m_id)
            
            success_count = 0
            fail_count = 0
            
            for bot_token in BOT_TOKENS:
                if not bot_token or bot_token in ["YOUR_SECOND_BOT_TOKEN_HERE", "YOUR_THIRD_BOT_TOKEN_HERE"]:
                    continue
                    
                if leave_guild(bot_token, guild_id):
                    success_count += 1
                    print(f"[+] Bot left guild: {guild_id}")
                else:
                    fail_count += 1
                    print(f"[-] Bot failed to leave guild: {guild_id}")
                time.sleep(0.5)
            
            send_msg(token, c_id, f"✅ **{success_count}** bots left the server!\n❌ **{fail_count}** bots failed.", reply_to=m_id)

        elif cmd_lower == "gcleft":
            guild_id = msg.get("guild_id")
            if guild_id:
                try:
                    guild_response = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}", 
                                                 headers={"Authorization": token})
                    guild_name = guild_response.json().get("name", "Unknown Server") if guild_response.status_code == 200 else "Unknown Server"
                except:
                    guild_name = "Unknown Server"
                
                send_msg(token, c_id, f"🔄 Making all bots leave **{guild_name}**...", reply_to=m_id)
                
                success_count = 0
                fail_count = 0
                
                for bot_token in BOT_TOKENS:
                    if not bot_token or bot_token in ["YOUR_SECOND_BOT_TOKEN_HERE", "YOUR_THIRD_BOT_TOKEN_HERE"]:
                        continue
                        
                    if leave_guild(bot_token, guild_id):
                        success_count += 1
                        print(f"[+] Bot left guild: {guild_id}")
                    else:
                        fail_count += 1
                        print(f"[-] Bot failed to leave guild: {guild_id}")
                    time.sleep(0.5)
                
                send_msg(token, c_id, f"✅ **{success_count}** bots left the server!\n❌ **{fail_count}** bots failed.", reply_to=m_id)
            else:
                try:
                    channel_response = requests.get(f"https://discord.com/api/v9/channels/{c_id}", 
                                                   headers={"Authorization": token})
                    if channel_response.status_code == 200:
                        channel_data = channel_response.json()
                        if channel_data.get("type") == 3:
                            send_msg(token, c_id, f"CHUDAI DONE H LEAVE LERA HU 😂🔥", reply_to=m_id)
                            
                            success_count = 0
                            fail_count = 0
                            
                            for bot_token in BOT_TOKENS:
                                if not bot_token or bot_token in ["YOUR_SECOND_BOT_TOKEN_HERE", "YOUR_THIRD_BOT_TOKEN_HERE"]:
                                    continue
                                    
                                if leave_group_chat(bot_token, c_id):
                                    success_count += 1
                                    print(f"[+] Bot left group chat: {c_id}")
                                else:
                                    fail_count += 1
                                    print(f"[-] Bot failed to leave group chat: {c_id}")
                                time.sleep(0.5)
                            
                            send_msg(token, c_id, f"✅ **{success_count}** CHUDAI DONE H LEAVE LERA HU 😂🔥 \n❌ **{fail_count}** bots failed.", reply_to=m_id)
                        else:
                            send_msg(token, c_id, "❌ This is not a group chat!", reply_to=m_id)
                    else:
                        send_msg(token, c_id, "❌ Failed to get channel info!", reply_to=m_id)
                except Exception as e:
                    send_msg(token, c_id, f"❌ Error: {str(e)}", reply_to=m_id)

        elif cmd_lower.startswith("cleft "):
            try:
                bot_mention = cmd_part.split()[1]
                bot_id = bot_mention.split("@")[1].replace(">", "").strip()
                
                guild_id = msg.get("guild_id")
                if not guild_id:
                    send_msg(token, c_id, "❌ This command can only be used in a server!", reply_to=m_id)
                    return
                
                target_token = find_bot_token_by_id(bot_id)
                if not target_token:
                    send_msg(token, c_id, f"❌ Bot <@{bot_id}> not found in token list!", reply_to=m_id)
                    return
                
                bot_info = get_bot_info(target_token)
                bot_name = bot_info.get("username", "Unknown Bot") if bot_info else "Unknown Bot"
                
                if leave_guild(target_token, guild_id):
                    send_msg(token, c_id, f"✅ **{bot_name}** left the server!", reply_to=m_id)
                else:
                    send_msg(token, c_id, f"❌ **{bot_name}** failed to leave the server.", reply_to=m_id)
            except:
                send_msg(token, c_id, "❌ Usage: !cleft @bot", reply_to=m_id)

        
        elif cmd_lower.startswith("join "):
            try:
                parts = cmd_part.split()
                if len(parts) < 2:
                    send_msg(token, c_id, "❌ Usage: !join [invite_code]\nExample: !join discord.gg/abc123", reply_to=m_id)
                    return
                
                invite_code = parts[1].strip()
                if "/" in invite_code:
                    invite_code = invite_code.split("/")[-1]
                if "discord.gg/" in invite_code:
                    invite_code = invite_code.replace("discord.gg/", "")
                if "discord.com/invite/" in invite_code:
                    invite_code = invite_code.replace("discord.com/invite/", "")
                
                try:
                    invite_response = requests.get(f"https://discord.com/api/v9/invites/{invite_code}")
                    if invite_response.status_code != 200:
                        send_msg(token, c_id, f"❌ Invalid invite code: **{invite_code}**", reply_to=m_id)
                        return
                    invite_data = invite_response.json()
                    guild_name = invite_data.get("guild", {}).get("name", "Unknown Server")
                    member_count = invite_data.get("approximate_member_count", "?")
                except:
                    guild_name = "Unknown Server"
                    member_count = "?"
                
                send_msg(token, c_id, f"🔄 Making all bots join **{guild_name}** ({member_count} members)...", reply_to=m_id)
                
                success_count = 0
                fail_count = 0
                failed_bots = []
                
                for bot_token in BOT_TOKENS:
                    if not bot_token or bot_token in ["YOUR_SECOND_BOT_TOKEN_HERE", "YOUR_THIRD_BOT_TOKEN_HERE"]:
                        continue
                        
                    bot_info = get_bot_info(bot_token)
                    bot_name = bot_info.get("username", "Unknown Bot") if bot_info else "Unknown Bot"
                    
                    if join_guild(bot_token, invite_code):
                        success_count += 1
                        print(f"[+] Bot {bot_name} joined via invite: {invite_code}")
                    else:
                        fail_count += 1
                        failed_bots.append(bot_name)
                        print(f"[-] Bot {bot_name} failed to join via invite: {invite_code}")
                    time.sleep(1)
                
                result_msg = f"✅ **{success_count}** bots joined the server!\n❌ **{fail_count}** bots failed."
                if failed_bots:
                    result_msg += f"\nFailed: {', '.join(failed_bots)}"
                
                send_msg(token, c_id, result_msg, reply_to=m_id)
            except Exception as e:
                send_msg(token, c_id, f"❌ Error: {str(e)}\nUsage: !join [invite_code]", reply_to=m_id)

        
        elif cmd_lower.startswith("xjoin "):
            try:
                parts = cmd_part.split()
                if len(parts) < 2:
                    send_msg(token, c_id, "❌ Usage: !xjoin [invite_code]\nExample: !xjoin discord.gg/abc123", reply_to=m_id)
                    return
                
                invite_code = parts[1].strip()
                if "/" in invite_code:
                    invite_code = invite_code.split("/")[-1]
                if "discord.gg/" in invite_code:
                    invite_code = invite_code.replace("discord.gg/", "")
                if "discord.com/invite/" in invite_code:
                    invite_code = invite_code.replace("discord.com/invite/", "")
                
                try:
                    invite_response = requests.get(f"https://discord.com/api/v9/invites/{invite_code}")
                    if invite_response.status_code != 200:
                        send_msg(token, c_id, f"❌ Invalid invite code: **{invite_code}**", reply_to=m_id)
                        return
                    invite_data = invite_response.json()
                    guild_name = invite_data.get("guild", {}).get("name", "Unknown Server")
                    member_count = invite_data.get("approximate_member_count", "?")
                except:
                    guild_name = "Unknown Server"
                    member_count = "?"
                
                send_msg(token, c_id, f"🔄 Making all bots join **{guild_name}** ({member_count} members)...", reply_to=m_id)
                
                success_count = 0
                fail_count = 0
                failed_bots = []
                
                for bot_token in BOT_TOKENS:
                    if not bot_token or bot_token in ["YOUR_SECOND_BOT_TOKEN_HERE", "YOUR_THIRD_BOT_TOKEN_HERE"]:
                        continue
                        
                    bot_info = get_bot_info(bot_token)
                    bot_name = bot_info.get("username", "Unknown Bot") if bot_info else "Unknown Bot"
                    
                    if join_guild(bot_token, invite_code):
                        success_count += 1
                        print(f"[+] Bot {bot_name} joined via invite: {invite_code}")
                    else:
                        fail_count += 1
                        failed_bots.append(bot_name)
                        print(f"[-] Bot {bot_name} failed to join via invite: {invite_code}")
                    time.sleep(1)
                
                result_msg = f"✅ **{success_count}** bots joined the server!\n❌ **{fail_count}** bots failed."
                if failed_bots:
                    result_msg += f"\nFailed: {', '.join(failed_bots)}"
                
                send_msg(token, c_id, result_msg, reply_to=m_id)
            except Exception as e:
                send_msg(token, c_id, f"❌ Error: {str(e)}\nUsage: !xjoin [invite_code]", reply_to=m_id)

        # ==================== ADD COMMAND ====================
        elif cmd_lower.startswith("add "):
            guild_id = msg.get("guild_id")
            if not guild_id:
                send_msg(token, c_id, "❌ This command can only be used in a server!", reply_to=m_id)
                return
            
            parts = cmd_part.split()
            if len(parts) < 2:
                send_msg(token, c_id, "❌ Usage: !add @bot [invite_code]\nExample: !add @MyBot discord.gg/abc123", reply_to=m_id)
                return
            
            bot_mention = parts[1]
            try:
                bot_id = bot_mention.split("@")[1].replace(">", "").strip()
            except:
                send_msg(token, c_id, "❌ Invalid bot mention! Use: !add @bot", reply_to=m_id)
                return
            
            invite_code = None
            if len(parts) > 2:
                invite_code = parts[2]
                if "/" in invite_code:
                    invite_code = invite_code.split("/")[-1]
                if "discord.gg/" in invite_code:
                    invite_code = invite_code.replace("discord.gg/", "")
                if "discord.com/invite/" in invite_code:
                    invite_code = invite_code.replace("discord.com/invite/", "")
            else:
                try:
                    invite_response = requests.post(f"https://discord.com/api/v9/channels/{c_id}/invites", 
                                                  headers={"Authorization": token}, 
                                                  json={"max_age": 300, "max_uses": 1, "temporary": False})
                    if invite_response.status_code in [200, 201]:
                        invite_code = invite_response.json().get("code")
                        send_msg(token, c_id, f"🔗 Created temporary invite: discord.gg/{invite_code}", reply_to=m_id)
                    else:
                        send_msg(token, c_id, f"⚠️ Failed to create temp invite. Please provide invite code.\nUsage: !add @bot invite_code", reply_to=m_id)
                        return
                except:
                    send_msg(token, c_id, f"⚠️ Failed to create temp invite. Please provide invite code.", reply_to=m_id)
                    return
            
            if not invite_code:
                send_msg(token, c_id, f"❌ No valid invite code provided!", reply_to=m_id)
                return
            
            send_msg(token, c_id, f"🔄 Attempting to add bot <@{bot_id}> to this server...", reply_to=m_id)
            
            try:
                bot_info = requests.get(f"https://discord.com/api/v9/users/{bot_id}", 
                                       headers={"Authorization": token})
                if bot_info.status_code != 200:
                    send_msg(token, c_id, f"❌ Bot with ID {bot_id} not found!", reply_to=m_id)
                    return
                bot_name = bot_info.json().get("username", "Unknown Bot")
            except:
                send_msg(token, c_id, f"❌ Error fetching bot info!", reply_to=m_id)
                return
            
            target_token = find_bot_token_by_id(bot_id)
            
            if target_token:
                if join_guild(target_token, invite_code):
                    send_msg(token, c_id, f"✅ **{bot_name}** DONE HEHE", reply_to=m_id)
                else:
                    send_msg(token, c_id, f"❌ **{bot_name}** failed to join the server.\nMake sure the invite is valid and the bot has permission.", reply_to=m_id)
            else:
                send_msg(token, c_id, f"❌ Bot **{bot_name}** not found in token list.\n💡 Please add its token to BOT_TOKENS list.", reply_to=m_id)

       
        nc_mappings = {
            "nc ": ("base", "NORMAL"), "lightningnc ": ("lightning", "NORMAL"),
            "heartnc ": ("heart", "NORMAL"), "kengnc ": ("keng", "NORMAL"),
            "timenc ": ("time", "TIME"), "animalnc ": ("animal", "NORMAL"),
            "gothicnc ": ("gothic", "NORMAL"), "cosmicnc ": ("cosmic", "NORMAL"),
            "vipernc ": ("viper", "NORMAL"), "demonnc ": ("demon", "NORMAL"),
            "oceannc ": ("ocean", "NORMAL"), "frostnc ": ("frost", "NORMAL"),
            "cybernc ": ("cyber", "NORMAL"), "toxicnc ": ("toxic", "NORMAL"),
            "royalnc ": ("royal", "NORMAL"), "voodoonc ": ("voodoo", "NORMAL"),
            "undeadnc ": ("undead", "NORMAL"), "ninjanc ": ("ninja", "NORMAL"),
            "samurainc ": ("samurai", "NORMAL"), "arcadenc ": ("arcade", "NORMAL"),
            "shadownc ": ("shadow", "NORMAL"), "hazardnc ": ("hazard", "NORMAL"),
            "matrixnc ": ("matrix", "NORMAL"), "phantomnc ": ("phantom", "NORMAL"),
            "galaxync ": ("galaxy", "NORMAL"), "valiantnc ": ("valiant", "NORMAL"),
            "glitchnc ": ("glitch", "NORMAL"), "infernonc ": ("inferno", "NORMAL"),
            "dynastync ": ("dynasty", "NORMAL"), "rebelnc ": ("rebel", "NORMAL"),
            "bignc ": ("ALL", "NORMAL"),   # NEW: replaces allnc
            "customnc ": ("CUSTOM", "NORMAL"),
            "slownc ": ("SLOW", "NORMAL")
        }

        for prefix, (pool_key, mode) in nc_mappings.items():
            if cmd_lower.startswith(prefix):
                bot_state.ACTIVE_NC_CHANNELS[c_id] = True
                text_input = cmd_part[len(prefix):]
                threading.Thread(target=nc_worker, args=(token, bot_state, c_id, pool_key, mode, text_input), daemon=True).start()
                break

        if cmd_lower == "stopnc":
            bot_state.ACTIVE_NC_CHANNELS[c_id] = False
            send_msg(token, c_id, "NC HAS BEEN STOPPED")

        # SPAMMERS / RAIDS / TRYHARD
        if cmd_lower.startswith("spam "): 
            bot_state.ACTIVE_SPAM_CHANNELS[c_id] = True
            threading.Thread(target=spam_worker, args=(token, bot_state, c_id, "TEXT", cmd_part[5:]), daemon=True).start()
            
        elif cmd_lower.startswith("customspam "):
            bot_state.ACTIVE_CUSTOM_SPAM_CHANNELS[c_id] = True
            threading.Thread(target=custom_spam_worker, args=(token, bot_state, c_id, cmd_part[11:]), daemon=True).start()

        elif cmd_lower.startswith("timespam "):
            bot_state.ACTIVE_TIMESPAM_CHANNELS[c_id] = True
            threading.Thread(target=spam_worker, args=(token, bot_state, c_id, "TIMESPAM", cmd_part[9:]), daemon=True).start()

        elif cmd_lower == "raid":
            target_msg_id = msg["message_reference"]["message_id"] if "message_reference" in msg else m_id
            send_msg(token, c_id, f"RAIDING ON {auth_id}")
            bot_state.ACTIVE_RAID_CHANNELS[c_id] = True
            threading.Thread(target=spam_worker, args=(token, bot_state, c_id, "RAID", "", target_msg_id), daemon=True).start()

        elif cmd_lower == "stopraid":
            bot_state.ACTIVE_RAID_CHANNELS[c_id] = False
            send_msg(token, c_id, "RAID HAS BEEN STOPPED")

        elif cmd_lower.startswith("tryhard "):
            send_msg(token, c_id, "TRYHARD ACTIVATED ")
            bot_state.ACTIVE_TRYHARD_CHANNELS[c_id] = True
            threading.Thread(target=tryhard_worker, args=(token, bot_state, c_id, cmd_part[8:]), daemon=True).start()

        elif cmd_lower == "stoptryhard":
            bot_state.ACTIVE_TRYHARD_CHANNELS[c_id] = False
            send_msg(token, c_id, "STOPPED FOR DADDY 😩")

        # ==================== RENAMED TURBO SPAM -> LEGITSPAM ====================
        elif cmd_lower.startswith("legitspam "):
            name = cmd_part[10:].strip()
            if not name:
                send_msg(token, c_id, "❌ Usage: !legitspam [name]\nExample: !legitspam TURBO", reply_to=m_id)
                return
            
            if not hasattr(bot_state, 'ACTIVE_TURBO_SPAM_CHANNELS'):
                bot_state.ACTIVE_TURBO_SPAM_CHANNELS = {}
            
            bot_state.ACTIVE_TURBO_SPAM_CHANNELS[c_id] = True
            send_msg(token, c_id, f"🔥 LEGIT SPAM ACTIVATED FOR: **{name}**")
            threading.Thread(target=turbo_spam_worker, args=(token, bot_state, c_id, name), daemon=True).start()

        elif cmd_lower == "stoplegitspam":
            if hasattr(bot_state, 'ACTIVE_TURBO_SPAM_CHANNELS'):
                bot_state.ACTIVE_TURBO_SPAM_CHANNELS[c_id] = False
            send_msg(token, c_id, "🛑 LEGIT SPAM STOPPED")

        # ==================== LUNDSAKI COMMAND ====================
        elif cmd_lower.startswith("lundsaki "):
            name = cmd_part[9:].strip()
            if not name:
                send_msg(token, c_id, "❌ Usage: !lundsaki [name]\nExample: !lundsaki TURBO", reply_to=m_id)
                return
            
            bot_state.ACTIVE_LUNDSAKI_CHANNELS[c_id] = True
            send_msg(token, c_id, f"💥 LUNDSAKI SPAM ACTIVATED FOR: **{name}**")
            threading.Thread(target=lundsaki_worker, args=(token, bot_state, c_id, name), daemon=True).start()

        elif cmd_lower == "stoplundsaki":
            bot_state.ACTIVE_LUNDSAKI_CHANNELS[c_id] = False
            send_msg(token, c_id, "🛑 LUNDSAKI SPAM STOPPED")

        for p_idx in range(1, 9):
            prefix_str = f"spam{p_idx} "
            if cmd_lower.startswith(prefix_str):
                bot_state.ACTIVE_SPAM_CHANNELS[c_id] = True
                user_string = cmd_part[len(prefix_str):]
                tail_emoji = SPAM_PRESETS[str(p_idx)]
                threading.Thread(target=spam_worker, args=(token, bot_state, c_id, "TEXT", f"{user_string} {tail_emoji}"), daemon=True).start()
                break

        if cmd_lower in ["stopextspam", "stopspam"]:
            bot_state.ACTIVE_SPAM_CHANNELS[c_id] = False
            bot_state.ACTIVE_CUSTOM_SPAM_CHANNELS[c_id] = False
            bot_state.ACTIVE_TIMESPAM_CHANNELS[c_id] = False
            send_msg(token, c_id, "EVERY SPAM HAS BEEN STOPPED")

        
        elif cmd_lower == "pinmessage":
            bot_state.ACTIVE_PIN_CHANNELS[c_id] = True
            send_msg(token, c_id, "📌 AUTO PINNING IS NOW ACTIVE ")

        elif cmd_lower == "deletemsg":
            bot_state.ACTIVE_DELETE_CHANNELS[c_id] = True
            send_msg(token, c_id, "🗑️ AUTO DELETE STARTED")
            threading.Thread(target=auto_delete_worker, args=(token, bot_state, c_id), daemon=True).start()

        
        if cmd_lower == "spampics": 
            bot_state.ACTIVE_PIC_CHANNELS[c_id] = True
            threading.Thread(target=spam_worker, args=(token, bot_state, c_id, "PIC", ""), daemon=True).start()

        elif cmd_lower == "stoppic":
            bot_state.ACTIVE_PIC_CHANNELS[c_id] = False
            send_msg(token, c_id, "PICTURE SPAM HAS BEEN STOPPED")

        elif cmd_lower == "savepic":
            if "message_reference" in msg:
                ref_c_id = msg["message_reference"]["channel_id"]
                ref_m_id = msg["message_reference"]["message_id"]
                res_msg = requests.get(f"https://discord.com/api/v9/channels/{ref_c_id}/messages/{ref_m_id}", 
                                      headers={"Authorization": token})
                if res_msg.status_code == 200:
                    ref_data = res_msg.json()
                    img_url = None
                    
                    if "attachments" in ref_data and ref_data["attachments"]:
                        img_url = ref_data["attachments"][0]["url"]
                    elif "embeds" in ref_data and ref_data["embeds"]:
                        for embed in ref_data["embeds"]:
                            if "image" in embed:
                                img_url = embed["image"]["url"]
                                break
                            elif "url" in embed and embed.get("type") == "image":
                                img_url = embed["url"]
                                break
                    
                    if img_url:
                        try:
                            img_res = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                            if img_res.status_code == 200:
                                with open(SAVED_PIC_PATH, "wb") as f: 
                                    f.write(img_res.content)
                                send_msg(token, c_id, "✅ IMAGE SUCCESSFULLY LINKED AND SAVED FOR SPAMPICS")
                            else:
                                send_msg(token, c_id, f"⚠️ HTTP ERROR {img_res.status_code} DOWNLOADING IMAGE.")
                        except Exception as e:
                            send_msg(token, c_id, f"⚠️ EXCEPTION DURING DOWNLOAD: {str(e)}")
                    else:
                        send_msg(token, c_id, "⚠️ FAILED MEDIA FOR THIS TARGET.")
                else:
                    send_msg(token, c_id, "⚠️ SERVER ERROR GETTING THIS REFRENCE.")
            else:
                send_msg(token, c_id, "⚠️ TARGET FAILURE: REPLY TO A PICTURE MESSAGE TO SAVE IT.")

        elif cmd_lower.startswith("react "):
            try:
                emoji = cmd_part.split()[1].strip()
                bot_state.AUTOREACT_EMOJI[c_id] = emoji
                send_msg(token, c_id, f"AUTOREACT ACTIVATED {emoji}")
            except: 
                pass

        elif cmd_lower == "stopreact":
            if c_id in bot_state.AUTOREACT_EMOJI:
                del bot_state.AUTOREACT_EMOJI[c_id]
            send_msg(token, c_id, "AUTOREACT HAS BEEN STOPPED")

        
        elif cmd_lower.startswith("delaync "): 
            try:
                val = float(cmd_part.split()[1])
                if 0.0 <= val <= 5.0: 
                    bot_state.NC_DELAY = val
            except: 
                pass
        elif cmd_lower.startswith("delay "): 
            try: 
                bot_state.GLOBAL_DELAY = float(cmd_part.split()[1])
                send_msg(token, c_id, f"⚡ GLOBAL AND RAID DELAY SET TO {bot_state.GLOBAL_DELAY} SECONDS")
            except: 
                pass
        elif cmd_lower.startswith("delaypic "):
            try:
                val = float(cmd_part.split()[1])
                if 1.0 <= val <= 10.0: 
                    bot_state.PIC_DELAY = val
                    send_msg(token, c_id, f"📸 PICTURE SPAM DELAY SET TO {bot_state.PIC_DELAY} SECONDS")
                else:
                    send_msg(token, c_id, "⚠️ DELAYPIC MUST BE BETWEEN 1 AND 10 SECONDS")
            except: 
                pass

        elif cmd_lower == "stopall": 
            bot_state.ACTIVE_NC_CHANNELS[c_id] = False
            bot_state.ACTIVE_SPAM_CHANNELS[c_id] = False
            bot_state.ACTIVE_CUSTOM_SPAM_CHANNELS[c_id] = False
            bot_state.ACTIVE_PIC_CHANNELS[c_id] = False
            bot_state.ACTIVE_RAID_CHANNELS[c_id] = False
            bot_state.ACTIVE_TIMESPAM_CHANNELS[c_id] = False
            bot_state.ACTIVE_TRYHARD_CHANNELS[c_id] = False
            bot_state.ACTIVE_PIN_CHANNELS[c_id] = False
            bot_state.ACTIVE_DELETE_CHANNELS[c_id] = False
            if hasattr(bot_state, 'ACTIVE_TURBO_SPAM_CHANNELS'):
                bot_state.ACTIVE_TURBO_SPAM_CHANNELS[c_id] = False
            if hasattr(bot_state, 'ACTIVE_LUNDSAKI_CHANNELS'):
                bot_state.ACTIVE_LUNDSAKI_CHANNELS[c_id] = False
            bot_state.TARGET_USER_ID = None
            if c_id in bot_state.AUTOREACT_EMOJI: 
                del bot_state.AUTOREACT_EMOJI[c_id]
            
            send_msg(token, c_id, "ALL COMMANDS HAVE BEEN STOPPED")

def run_bot(token):
    bot_state = BotState()
    bot_state.SUDO_USERS = load_sudo(bot_state)
    bot_id = get_bot_id_from_token(token)
    
    if not bot_id:
        print(f"\033[91m[ERROR] Failed to get bot ID for token: {token[:20]}...\033[0m")
        return
    
    BOT_STATES[token] = bot_state
    
    print(f"\033[92m[+] Bot started with ID: {bot_id} | Owner ID: {bot_state.OWNER_ID}\033[0m")
    
    def on_message_wrapper(ws, message):
        on_message(ws, message, token, bot_state)
    
    while True:
        try:
            ws = websocket.WebSocketApp("wss://gateway.discord.gg/?v=9&encoding=json", 
                                        on_message=on_message_wrapper)
            ws.run_forever()
        except Exception as e:
            print(f"\033[91m[!] Bot {token[:20]}... disconnected: {e}. Reconnecting...\033[0m")
            time.sleep(5)


if __name__ == "__main__":
    print("\033[91m" + "==================================================")
    print("      TURBO MULTI-BOT SYSTEM LOG INITIALIZED  ")
    print("==================================================" + "\033[0m")
    print(f"\033[93m[+] Owner ID configured: {OWNER_ID}\033[0m")
    print(f"\033[93m[+] Total bots to start: {len(BOT_TOKENS)}\033[0m")
    
    for idx, f_val in enumerate(TRYHARD_FONTS):
        TRYHARD_FONTS[idx] = f_val.replace("𘘗𘘙𘘎𘘈𝘈𘘙𘘎", "𝖳𝖱𝖸𝖧𝖠𝖱𝖣").replace("𘘮𘘴𘘭", "𝖡𝖮𝖴𝖳")
    
    threads = []
    for i, token in enumerate(BOT_TOKENS):
        if token and token.strip():
            thread = threading.Thread(target=run_bot, args=(token,), name=f"Bot-{i+1}")
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(2)
    
    print(f"\033[92m[+] All {len(threads)} bots are running!\033[0m")
    
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n\033[91m[!] Shutting down all bots...\033[0m")
