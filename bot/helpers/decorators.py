import re
from typing import Union
from .. import bot
from telethon import events


COMMANDS = []

def _on_command(command: str, prefixes: Union[list, str], *args, **kwargs):
    def decorator(f):
        global COMMANDS
        _command = ''
        for prefix in prefixes:
            _command += re.escape(prefix) + command + r'\b' + '|'
        _command = re.sub(r'\|$', '', _command)
        COMMANDS.append('**{}** - __This command can be triggered by these prefixes/this prefix:__ [`{}`]'.format(command, ', '.join(prefixes)))


        @bot.on(events.NewMessage(incoming=True, pattern=_command, **kwargs))
        async def handler(event):
            await f(event)
            return f

        return handler

    return decorator


def action(_action: str):
    def decorator(f):
        async def wrapper(event):
            async with bot.action(event.chat_id, _action):
                await f(event)

        return wrapper

    return decorator
