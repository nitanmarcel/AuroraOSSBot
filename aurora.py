import logging
import os
import re

import telethon
import aiohttp
from telethon.tl.custom import Button

logging.basicConfig(level=logging.INFO)

try:
    API_ID = os.environ["APP_ID"]
    API_HASH = os.environ["APP_HASH"]
    TOKEN = os.environ["TOKEN"]
except KeyError as e:
    quit(e.args[0] + ' missing from environment variables')


DISPENSER_HOOK = os.environ.get("DISPENSER_HOOK")

bot = telethon.TelegramClient("aurorabot", API_ID, API_HASH)

bot.start(bot_token=TOKEN)


CHANNEL_ID = -1001398868273
BOT_ID = 589434197
OFFICIAL_CHATS = [-1001361570927, -1001374518507]
MODERATORS = [
    796283593,
    779031275,
    537608837,
    10518517,
    589434197,
    370300617,
    266613194,
    81100737,
    388027566,
    388064587,
    355703188,
    342120919,
    416195206,
    145512169,
    255991910,
    389340481,
    463062143]


@bot.on(telethon.events.NewMessage(incoming=True, pattern=r"\/start"))
async def start(event):
    await event.reply("Up and running")


@bot.on(
    telethon.events.NewMessage(
        incoming=True,
        pattern=r"\/suggestion|\/bug",
        forwards=False,
        chats=OFFICIAL_CHATS))
async def add_suggestions(event):
    if not event.is_reply and len(event.text.split()) == 1:
        await event.delete()
        return

    if event.text.startswith("/suggestion"):
        REPLY = "Thanks for your suggestion. Please await admin's aproval"
        data = b"sugg"
    else:
        REPLY = "Thanks for your bug report. Please await admin's aproval"
        data = b"bug"

    await bot.send_message(event.chat_id, REPLY, buttons=Button.inline("Approve", data), reply_to=event.reply_to_msg_id or event)


@bot.on(telethon.events.CallbackQuery())
async def approve(event):
    if event.data not in (b"sugg", b"bug"):
        return
    if event.sender_id not in MODERATORS:
        await event.answer("Only admins can use this button!")
        return

    rep_msg = await (await event.get_message()).get_reply_message()
    await bot.forward_messages(CHANNEL_ID, rep_msg, silent=True)

    if event.data == b"bug":
        await event.edit("Your bug repost has been forwarded to our channel! Thanks!")
    else:
        await event.edit("Your suggestion has been forwarded to our channel! Thanks!")


@bot.on(telethon.events.NewMessage(incoming=True, pattern="\/status"))
async def dispenser_check(event):
    reply = await event.reply("Checking Token Dispenser status")
    async with aiohttp.ClientSession() as session:
        status = None
        async with session.get(DISPENSER_HOOK) as response:
            status = response.status

        if status != 200:
            await reply.edit("The Token Dispenser is down! It will be fixed as soon as possible")
        else:
            await reply.edit("The Token Dispenser is up!")

@bot.on(telethon.events.NewMessage(incoming=True, pattern="\/nightly"))
async def latest_nightly(event):
    url = "http://auroraoss.com/Nightly/"
    file = None
    reply = await event.reply("Fetching apk file..")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            text = await response.text()
            versions = re.findall("/Nightly/AuroraStore-nightly-signed-(\d+)", text)
            latest_version = max(versions)
            file = "AuroraStore-Nightly-" + latest_version + ".apk"
        async with session.get(url + "/AuroraStore-nightly-signed-" + latest_version + ".apk") as f_response:
            with open(file, "wb") as apk_file:
                apk_file.write(await f_response.read())
    await event.reply(file=file)
    await reply.delete()

    if os.path.isfile(file):
        os.remove(file)



if __name__ == "__main__":
    bot.run_until_disconnected()
