import discord
import json
import os
import asyncio
import requests
from discord.ext import commands
from config import ADMIN_UIDS, WEBHOOK_URL, TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DB_FILE = "database.json"

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def send_webhook(event, data):
    embed = {
        "title": f"{event} Event",
        "description": f"```json\n{json.dumps(data, indent=2)}\n```",
        "color": 3066993 if event == "REDEEM" else 15158332
    }
    requests.post(WEBHOOK_URL, json={"embeds": [embed]})

@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập thành {bot.user}")

@bot.command()
async def taokey(ctx, key: str):
    if str(ctx.author.id) not in ADMIN_UIDS:
        return await ctx.send("❌ Bạn không có quyền.")

    db = load_db()
    if any(k["key"] == key for k in db["keys"]):
        return await ctx.send("⚠️ Key đã tồn tại.")
    
    db["keys"].append({
        "key": key,
        "used": False,
        "discord_id": None,
        "hwid": None
    })
    save_db(db)
    await ctx.send(f"✅ Key `{key}` đã được tạo.")

@bot.command()
async def redeem(ctx, key: str, hwid: str):
    db = load_db()
    for k in db["keys"]:
        if k["key"] == key:
            if k["used"]:
                return await ctx.send("❌ Key đã được sử dụng.")
            k["used"] = True
            k["discord_id"] = str(ctx.author.id)
            k["hwid"] = hwid
            save_db(db)
            send_webhook("REDEEM", k)
            return await ctx.send("✅ Redeem thành công.")
    await ctx.send("❌ Key không tồn tại.")

@bot.command()
async def resethwid(ctx, new_hwid: str):
    db = load_db()
    for k in db["keys"]:
        if k["discord_id"] == str(ctx.author.id):
            old_hwid = k["hwid"]
            k["hwid"] = new_hwid
            save_db(db)
            send_webhook("RESET_HWID", {
                "discord_id": k["discord_id"],
                "key": k["key"],
                "old_hwid": old_hwid,
                "new_hwid": new_hwid
            })
            return await ctx.send("✅ Đã reset HWID.")
    await ctx.send("❌ Bạn chưa redeem key nào.")

@bot.command()
async def getscript(ctx):
    db = load_db()
    for k in db["keys"]:
        if k["discord_id"] == str(ctx.author.id):
            script = f'''
```lua
getgenv().Key = "{k['key']}"
getgenv().ID = "{k['discord_id']}"
loadstring(game:HttpGet("https://raw.githubusercontent.com/chaudzvn123/VnpKing/refs/heads/main/Protected_8040132681226395.txt"))()
