import datetime

from .helpers import CommandHandler, action, COMMANDS
from telethon.tl.custom import Button
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
from telethon.events import CallbackQuery, ChatAction
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from . import bot, config
import aiohttp
import re
import os

EMAIL_REGEX = '''(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])'''


PM_START_TEXT = \
"""
Hi {}, my name is {}! If you have any questions on how to use me, read /help!

I'm a bot made for the AuroraOSS groups to help with managing suggestions, bug reports and more. I'm made in python using the telethon library.

My [creator](https://t.me/nitanmarcel) made me in that way I can join only AuroraOSS groups so if you try to add me to other groups, channels I will leave, as I shouldn't be there.


You can find the list of available commands with /help.

If you want me in your groups you can find my source code [here](https://github.com/nitanmarcel/AuroraOSSBot/) and modify it to your liking!
"""

@CommandHandler('start', prefixes=['/', '!'])
@action('typing')
async def start(event):
    if not event.message.is_private:
        return await event.reply("Up and running!")
    else:
        me = await bot.get_me()
        sender = await event.get_sender()
        return await event.reply(PM_START_TEXT.format(sender.first_name, me.first_name))
@CommandHandler('help', prefixes=['/', '!'])
@action('typing')
async def show_help(event):
    return await event.reply(
        '''
        Available commands:
        \n{}
        '''.format('\n'.join(sorted(COMMANDS)))

    )

@CommandHandler('status', prefixes=['/', '!'])
@action('typing')
async def dispenser_check(event):
    reply = await event.reply("Checking Token Dispenser status! Please wait...")
    status = False
    async with aiohttp.ClientSession() as session:
        async with session.get(config.get_property('DISPENSER_HOOK')) as response:
            if response.status == 200:
                if re.match(EMAIL_REGEX, await response.text()):
                    status = True
    if status is False:
        await reply.edit("The Token Dispenser is down! It will be fixed as soon as possible")
        return
    await reply.edit("The Token Dispenser is up!")


@CommandHandler('nightly', prefixes=['/', '!', '#'],
                )  # , chats=[-1001361570927])
@action('file')
async def latest_nightly(event):
    reply = await event.reply("Fetching apk file..")
    file_name = None
    async with aiohttp.ClientSession() as session:
        async with session.get(config.get_property('NIGHTLY_URL')) as response:
            if response.status == 200:
                text = await response.text()
                versions = re.findall(config.get_property('NIGHTLY_NAME_MATCH'), text)
                latest_version = config.get_property('NIGHTLY_ALGO')(versions)
                file_name = "AuroraStore-Nightly-" + latest_version + ".apk"
                async with session.get(config.get_property('NIGHTLY_URL') + file_name) as f_response:
                    with open(file_name, "wb") as apk_file:
                        apk_file.write(await f_response.read())
    if not file_name:
        return await reply.edit('Failed to fetch the latest nightly version! Try again later..')
    await event.reply(file=file_name)
    await reply.delete()
    return os.remove(os.path.join(os.getcwd(), file_name))


@CommandHandler('suggestion', prefixes=['/', '!'], chats=config.get_property('ALLOWED_CHATS'))
@action('typing')
async def add_suggestions(event):
    if not event.is_reply and len(event.text.split()) == 1:
        return await event.delete()
    await bot.send_message(event.chat_id, 'Thanks for your suggestion. Please await admin\'s approval',
                           buttons=[Button.inline("Approve", b'sugg'), Button.inline("Reject", b"no" + b'sugg')],
                           reply_to=event.reply_to_msg_id or event)


@CommandHandler('bug', prefixes=['/', '!'], chats=config.get_property('ALLOWED_CHATS'))
@action('typing')
async def add_bug(event):
    if not event.is_reply and len(event.text.split()) == 1:
        return await event.delete()
    await bot.send_message(event.chat_id, 'Thanks for your bug report. Please await admin\'s approval',
                           buttons=[Button.inline("Approve", b'bug'), Button.inline("Reject", b"no" + b'bug')],
                           reply_to=event.reply_to_msg_id or event)


@bot.on(ChatAction)
@action('typing')
async def welcome_mute(event):
    if event.user_added or event.user_joined:
        user = await event.get_user()
        participant = await bot(GetParticipantRequest(event.chat_id, user.id))
        if not isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
            return

        await bot(EditBannedRequest(event.input_chat, user.id,
                                    ChatBannedRights(
                                        until_date=None,
                                        view_messages=None,
                                        send_messages=True,
                                        send_media=True,
                                        send_stickers=True,
                                        send_gifs=True,
                                        send_games=True,
                                        send_inline=True,
                                        embed_links=True
                                    )
                                    ))
        await bot.send_message(event.input_chat,
                               "Hi {}! Please confirm you are not a bot !".format(user.username or user.first_name),
                               buttons=[Button.inline("Click here to confirm", bytes(str(user.id).encode('utf8')))])


@bot.on(ChatAction)
@action('typing')
async def restrict_chat(event):
    chat_id = (await event.get_chat()).id
    if chat_id not in config.get_property('ALLOWED_CHATS') and event.user_added:
        try:
            await event.reply('I shouldn\'t be here!')
            return await bot.kick_participant(chat_id, 'me')
        except Exception:
            pass


@bot.on(CallbackQuery)
@action('typing')
async def check_report(event):
    sender = await event.get_sender()
    participant = await bot(GetParticipantRequest(event.chat_id, sender.id))
    if not isinstance(participant.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)):
        return await event.answer("Only admins can use this button!")

    by_admin = "[{}](tg://user?id={})".format(sender.first_name, sender.id)
    at_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    if event.data.decode() == 'nosugg':
        return await event.edit("Your suggestion has been rejected by {} at `{}`!".format(by_admin, at_time))
    if event.data.decode() == 'nobug':
        return await event.edit("Your bug report has been rejected by {} at `{}`!".format(by_admin, at_time))
    rep_msg = await (await event.get_message()).get_reply_message()
    by_user = "[{}](tg://user?id={})".format(rep_msg.sender.first_name, rep_msg.sender.id)
    in_chat = "[{}](https://t.me/{})".format(rep_msg.chat.title, rep_msg.chat.username)
    file = rep_msg.photo or rep_msg.document
    text = rep_msg.text
    report_type = None
    if text:
        if text.startswith("/bug"):
            text = re.sub(r"^/bug ", "", text)
            report_type = 'bug'
        if text.startswith("/suggestion"):
            report_type = 'suggestion'
            text = re.sub(r"^/suggestion ", "", text)
    approved_format = "{} from {} in {} \n\n{} \n\nApproved by {} at `{}`".format(
        "Bug" if rep_msg.text.startswith("/bug") else "Suggestion",
        by_user, in_chat, text, by_admin, at_time)
    print(config.get_property('SUGGESTIONS_BUGS_CHAT'))
    await bot.send_message(config.get_property('SUGGESTIONS_BUGS_CHAT'), message=approved_format, silent=True,
                           file=file)
    if report_type == 'bug':
        await event.edit(
            "Your bug report has been forwarded to our channel by {} at `{}`! Thanks!".format(by_admin, at_time))
    else:
        await event.edit(
            "Your suggestion has been forwarded to our channel by {} at `{}`! Thanks!".format(by_admin, at_time))


@bot.on(CallbackQuery)
async def unmute_button(event):
    if not event.data.decode().isdigit():
        return
    user = await event.get_sender()
    if int(event.data.decode()) != int(user.id):
        return await event.answer("Who are you again?")
    await bot(EditBannedRequest(event.input_chat, user.id,
                                ChatBannedRights(
                                    until_date=None,
                                    send_messages=None,
                                    send_media=None,
                                    send_stickers=None,
                                    send_gifs=None,
                                    send_games=None,
                                    send_inline=None,
                                    embed_links=None
                                )
                                ))
    await event.delete()


if __name__ == '__main__':
    bot.run_until_disconnected()
