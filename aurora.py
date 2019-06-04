import logging
import os
import re

import telethon
import aiohttp
from telethon.tl.custom import Button
import datetime

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

    await bot.send_message(event.chat_id, REPLY, buttons=[Button.inline("Approve", data), Button.inline("Reject", b"no" + data)], reply_to=event.reply_to_msg_id or event)


@bot.on(telethon.events.CallbackQuery())
async def approve(event):
    if event.sender_id not in MODERATORS:
        await event.answer("Only admins can use this button!")
        return

    if event.data not in (b"sugg", b"bug", b"nosugg", b"nobug"):
        return
    sender = await event.get_sender()
    admin = "[{}](tg://user?id={})".format(sender.first_name, sender.id)
    time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    if event.data == b"nosugg":
        await event.edit("Your suggestion has been rejected by {} at `{}`!".format(admin, time))
    elif event.data == b"nobug":
        await event.edit("Your bug report has been rejected by {} at `{}`!".format(admin, time))
    else:
        rep_msg = await (await event.get_message()).get_reply_message()
        user = "[{}](tg://user?id={})".format(rep_msg.sender.first_name, rep_msg.sender.id)
        chat = "[{}](https://t.me/{})".format(rep_msg.chat.title, rep_msg.chat.username)
        file = rep_msg.photo or rep_msg.document
        text = rep_msg.text

        if text:
            if text.startswith("/bug"):
                text = re.sub(r"^/bug ", "", text)
            elif text.startswith("/suggestion"):
                text = re.sub(r"^/suggestion ", "", text)


        out_format = "{} from {} in {} \n\n{} \n\nApproved by {} at `{}`".format("Bug" if rep_msg.text.startswith("/bug") else "Suggestion",
                                    user, chat, text, admin, time)

        await bot.send_message(CHANNEL_ID, message=out_format, silent=True, file=file)

        if event.data == b"bug":
            await event.edit("Your bug report has been forwarded to our channel by {} at `{}`! Thanks!".format(admin, time))
        else:
            await event.edit("Your suggestion has been forwarded to our channel by {} at `{}`! Thanks!".format(admin, time))



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

@bot.on(telethon.events.NewMessage(incoming=True, pattern="\/nightly", chats=[-1001361570927]))
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
        
        
        
@bot.on(telethon.events.NewMessage(incoming=True, pattern="\/broadcast", from_users=[416195206]))
async def broadcast(event):
    for chat in OFFICIAL_CHATS:
        message = event.text.split(None, 1)
        if len(message) > 1:
            await bot.send_message(chat, message[1])

def __chat_action_lock(event):
    if event.user_added:
        return True
    if event.user_joined:
        return True
    return

@bot.on(telethon.events.ChatAction(func=__chat_action_lock))
async def welcomemute(event):
    if event.user_added:
        user = event.get_added_by()
    else:
        user = event.get_input_user()
    await bot(telethon.tl.functions.channel.EditBannedRequest(
            telethon.tl.types.ChatBannedRights(
                    send_messages=True,
                    send_media=True,
                    send_stickers=True,
                    send_gifs=True,
                    send_games=True,
                    send_inline=True,
                    embed_links=True
            )
    ))
    await bot.send_message(event.input_chat, "Before continuing please press the button bellow!",
                           buttons=[Button.inline("Press me to prove that you are human!", b'{}'.format(user.id))], reply_to=event.message.id)


def __button_lock(event):
    if not event.data.isalpha():
        return True
    return


@bot.on(telethon.events.CallbackQuery(func=__button_lock))
async def unmute_button(event):
    sender = await event.get_sender()
    if int(event.data) != int(sender.id):
        event.answer("Who are you again?")
    else:
        await bot(telethon.tl.functions.channel.EditBannedRequest(
                telethon.tl.types.ChatBannedRights(
                        send_messages=None,
                        send_media=None,
                        send_stickers=None,
                        send_gifs=None,
                        send_games=None,
                        send_inline=None,
                        embed_links=None
                )
        ))
        event.delete()

if __name__ == "__main__":
    bot.run_until_disconnected()
