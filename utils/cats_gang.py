import random
import time
from typing import Union
from utils.core import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
import asyncio
from urllib.parse import unquote, quote
from data import config
import aiohttp
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector


class CatsGang:
    def __init__(self, thread: int, session_name: str, phone_number: str, proxy: Union[str, None]):
        self.account = session_name + '.session'
        self.thread = thread
        self.ref = 'nbqLDmjEs8-3Yf_yEpuG1'
        self.proxy = f"{config.PROXY['TYPE']['REQUESTS']}://{proxy}" if proxy is not None else None
        self.buffer_cats = []
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)

        if proxy:
            proxy = {
                "scheme": config.PROXY['TYPE']['TG'],
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

        self.client = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            workdir=config.WORKDIR,
            proxy=proxy,
            lang_code='ru'
        )

        headers = {
            'User-Agent': UserAgent(os='android', browsers='chrome').random,
        }
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def stats(self):
        await self.login()

        user = await self.user()
        balance = str(user.get('totalRewards'))
        referral_link = f"https://t.me/catsgang_bot/join?startapp={user.get('referrerCode')}"

        r = await (await self.session.get('https://api.catshouse.club/leaderboard')).json()
        leaderboard = r.get('userPlace')

        await self.logout()

        await self.client.connect()
        me = await self.client.get_me()
        phone_number, name = "'" + me.phone_number, f"{me.first_name} {me.last_name if me.last_name is not None else ''}"
        await self.client.disconnect()

        proxy = self.proxy.replace('http://', "") if self.proxy is not None else '-'

        return [phone_number, name, balance, leaderboard, referral_link, proxy]

    async def user(self):
        resp = await self.session.get('https://api.catshouse.club/user')
        return await resp.json()

    async def logout(self):
        await self.session.close()

    async def check_task(self, task_id: int):
        try:
            resp = await self.session.post(f'https://api.catshouse.club/tasks/{task_id}/check')
            return (await resp.json()).get('completed')
        except:
            return False

    async def complete_task(self, task_id: int):
        try:
            resp = await self.session.post(f'https://api.catshouse.club/tasks/{task_id}/complete')
            return (await resp.json()).get('success')
        except:
            return False

    async def get_tasks(self):
        resp = await self.session.get('https://api.catshouse.club/tasks/user?group=cats')
        return (await resp.json()).get('tasks')

    async def register(self):
        resp = await self.session.post(f'https://api.catshouse.club/user/create?referral_code=nbqLDmjEs8-3Yf_yEpuG1')
        return resp.status == 200
    

    async def upload_cat(self):
        while True:
            cat = random.randint(1,47)
            while cat in self.buffer_cats:
                cat = random.randint(1,47)

            self.buffer_cats.append(cat)
            
            with open(f'utils/cats/cat{cat}.jpg', 'rb') as image_file:
                form_data = aiohttp.FormData()
                form_data.add_field('photo', image_file, filename=f'cat{cat}.jpg')

                resp = await self.session.post(
                    "https://api.catshouse.club/user/avatar/upgrade", 
                    data=form_data
                )
                if resp.status == 200 or resp.status == 201:
                    logger.success(f"Thread {self.thread} | {self.account} | Upload a cat")
                else:
                    logger.info(f"Thread {self.thread} | {self.account} | Can't upload a cat")
                    break
    

    async def login(self):
        await asyncio.sleep(random.uniform(*config.DELAYS['ACCOUNT']))
        self.ref = 'nbqLDmjEs8-3Yf_yEpuG1'
        query = await self.get_tg_web_data()

        if query is None:
            logger.error(f"Thread {self.thread} | {self.account} | Session {self.account} invalid")
            await self.logout()
            return None, None

        self.session.headers['Authorization'] = 'tma ' + query

        r = await (await self.session.get('https://api.catshouse.club/user')).text()
        if r == '{"name":"Error","message":"User was not found"}':
            if await self.register():
                logger.success(f"Thread {self.thread} | {self.account} | Register")

    async def get_tg_web_data(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestAppWebView(
                peer=await self.client.resolve_peer('catsgang_bot'),
                app=InputBotAppShortName(bot_id=await self.client.resolve_peer('catsgang_bot'), short_name="join"),
                platform='android',
                write_allowed=True,
                start_param=self.ref
            ))
            await self.client.disconnect()

            auth_url = web_view.url
            query = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            return query

        except:
            return None
