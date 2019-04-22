import logging
import os

import telethon
from telethon.tl.custom import Button

logging.basicConfig(level=logging.INFO)

try:
    API_ID = os.environ["APP_ID"]
    API_HASH = os.environ["APP_HASH"]
    TOKEN = os.environ["TOKEN"]
except KeyError as e:
    quit(e.args[0] + ' missing from environment variables')

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


if __name__ == "__main__":
    bot.run_until_disconnected()
