import telethon
from telethon import TelegramClient, events
import asyncio
from functools import wraps
from loguru import logger
from telethon.tl.types import InputMediaDice

api_id = 6
api_hash = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'
loop = asyncio.new_event_loop()

logger.add('log.log', enqueue=True)


class MyClient():
    def __init__(self, loop):
        self.loop = loop
        asyncio.set_event_loop(self.loop)
        self.phone_number = input('Введите номер телефона для авторизации: ')
        self.client = TelegramClient(f'{self.phone_number}.session', api_id=api_id, api_hash=api_hash,
                                     auto_reconnect=True)
        self.me = None
        self.logger = logger
        self.conn_tg()

    def slot(*args):
        def outer_decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                return asyncio.ensure_future(fn(*args, **kwargs))

            return wrapper

        return outer_decorator

    @slot()
    async def conn_tg(self):
        await self.client.connect()
        is_auth = await self.client.is_user_authorized()
        if not is_auth:
            y = await self.client.send_code_request(self.phone_number)
            self.code = input("Введите код авторизации : ")
            try:
                await self.client.sign_in(self.phone_number, code=self.code)
            except telethon.errors.SessionPasswordNeededError:
                password2fa = input("Введите 2FA пароль: ")
                await self.client.sign_in(password=password2fa)
        else:
            await self.log(f"Авторизация завершена. Код не потребовался")
        self.me = await self.client.get_me()
        await self.log(f"Авторизован по номеру {self.me.phone}")


    @slot()
    async def log(self, message):
        self.logger.info(message)

Cl = MyClient(loop)
client = Cl.client

@client.on(events.NewMessage(outgoing=True))
async def new_message(event):
    text = event.message.text
    message = event.message
    chat_id = event.peer_id
    if text.startswith('.dice'):
        command, emoji, need_value = text.split(' ')
        await message.delete()
        while True:
            res = await client.send_file(chat_id, InputMediaDice(emoticon=emoji))
            if int(res.media.value) != int(need_value):
                await Cl.client.delete_messages(res.peer_id, res.id)
            else:
                return

Cl.loop.run_forever()