import telethon
from telethon import TelegramClient, events
import asyncio
from functools import wraps
from loguru import logger


# При желании можно заменить API ID и API HASH
api_id = 6
api_hash = 'eb06d4abfb49dc3eeb1aeb98ae0f581e'

loop = asyncio.new_event_loop()


def slot(*args):
    def outer_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return asyncio.ensure_future(fn(*args, **kwargs))
        return wrapper
    return outer_decorator


logger.add('log.log', enqueue=True)


class MyClient():
    def __init__(self, loop):
        self.logger = logger
        self.phone_number = input('Введите номер телефона для авторизации: ')
        self.loop = loop
        asyncio.set_event_loop(self.loop)
        self.client = TelegramClient(f'{self.phone_number}.session', api_id=api_id, api_hash=api_hash,
                                     auto_reconnect=True)
        self.me = None
        self.conn_tg()


    async def while_get_dialogs(self):
        while True:
            await self.client.get_dialogs()
            await asyncio.sleep(600)


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
        loop.create_task(self.while_get_dialogs())


    @slot()
    async def log(self, message):
        self.logger.info(message)


Cl = MyClient(loop)
client = Cl.client


def add_user_to_list(uid, uname):
    line = f'{uid}:{uname}\n' # Изменить тут вид записи, если нужно
    with open('list_users.txt', 'a+', encoding='utf-8') as f:
        f.write(line)


def check_base(user_id):
    with open('list_users.txt', 'a+', encoding='utf-8') as f:
        in_file = f.read().splitlines()
        return bool(user_id in in_file)


@client.on(events.NewMessage(incoming=True))
async def new_message(event):
    if hasattr(event._chat_peer, 'chat_id'):
        chat = event._chat_peer.chat_id
    elif hasattr(event._chat_peer, 'channel_id'):
        chat = event._chat_peer.channel_id
    else:
        return await event.delete()
    try:
        sender = await event.get_input_sender()
        dct = event.message.from_id.to_dict()

        if 'user_id' in dct:

            if check_base(dct['user_id']):
                return await event.delete()

            ent = await client.get_entity(sender.user_id)

            if ent.bot:
                return await event.delete()
            uname, uid = ent.username, ent.id

            if uname:
                add_user_to_list(uid, uname)
                logger.success(f"NEW USER | {uname}")
                return await event.delete()

    except:
        logger.error('Ошибочка вышла')
        pass
    return await event.delete()


Cl.loop.run_forever()
