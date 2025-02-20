import asyncio
import json
import logging
import os
import random
import re
import ssl
import subprocess
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import aiofiles
import aiohttp
import requests
import vk_api
import vk_captchasolver as vc
import vkbottle
import g4f
from g4f.client import AsyncClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from neuro_cfg.config import cfg
from vk_api import VkApi
from vk_api.exceptions import ApiError, VkApiError
from vk_api.longpoll import VkLongPoll, VkChatEventType, VkEventType
from vk_api.upload import VkUpload
from vkbottle import API, VKAPIError, GroupEventType, GroupTypes, Bot

WHITE = "\033[97m"
RESET = "\033[0m"
BOLD = "\033[1m"
BASE_DIR = "base"
TOKENS_FILE = os.path.join(BASE_DIR, "data.json")
AVATARS_FOLDER = 'avatars'

model = cfg['model']
prompt = cfg['prompt']
provider = cfg['provider']
g4f.debug.logging = True
g4f.debug.version_check = True
client = AsyncClient()

def input_white(prompt):
    print("\033[97m" + prompt + "\033[1m", end="")
    return input()

def print_white(text):
    print(f"{WHITE}{BOLD}{text}{RESET}")

async def neuro(session, token, login, friend_ids, proxy):
    captcha_params = None
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    async def listen_longpoll():
        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW:
                    if hasattr(event, 'user_id'):
                        user_id = event.user_id
                    elif hasattr(event, 'group_id'):
                        user_id = event.group_id

                    peer_id = event.peer_id
                    reply_to = event.message_id

                    if event.from_me:
                        continue

                    if user_id in friend_ids:
                        print_white(f"ЛОГИН {login} ПРОПУСТИЛ СООБЩЕНИЕ ОТ ДРУГА С ID: {user_id} ИЗ СПИСКА ФРЕНДЛИСТА")
                        continue
                    
                    user_message = event.text
                    task = asyncio.create_task(neuro_generate(user_message))
                    message = await task
                    if message:
                        await send_message(session, token, login, peer_id, reply_to, message, event, proxy, captcha_params)

            except Exception as e:
                logging.error(f"ОШИБКА ПРИ ОБРАБОТКЕ СОБЫТИЯ: {e}")

    await listen_longpoll()

async def send_message(session, token, login, peer_id, reply_to, message, event, proxy, captcha_params):
    url_messages_send = 'https://api.vk.com/method/messages.send'

    message_id = None
    probability = 0.5

    if random.random() < probability:
        pass
    else:
        reply_to = ''

    params_send = {
        'peer_id': peer_id,
        'reply_to': reply_to,
        'message': message or '',
        'random_id': random.randint(1, 999999),
        'access_token': token,
        'v': '5.131'
    }

    if captcha_params:
        params_send.update(captcha_params)

    async with session.post(url_messages_send, params=params_send, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            message_id = result['response']
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            if error_code == 14:
                solved = False
                while not solved:
                    try:
                        print_white(f"ВНИМАНИЕ! ОБНАРУЖЕНА КАПЧА! РЕШАЕМ...")
                        captcha_sid = result['error']['captcha_sid']
                        captcha_solution = await vc.solve(sid=captcha_sid, s=1)
                        print_white(f"РЕШИЛИ КАПЧУ! ВОТ ЕЁ РЕШЕНИЕ: {captcha_solution}")
                        captcha_params = {'captcha_sid': captcha_sid, 'captcha_key': captcha_solution}
                        solved = True
                        time.sleep(3)
                        return await send_message(session, token, login, peer_id, reply_to, message, event, proxy, captcha_params)

                    except Exception as captcha_error:
                        print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")
            else:
                logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ: {error_code} - {error_msg}")
                return

    if message_id:
        if reply_to:
            print_white(f"НЕЙРОСЕТЬ {login} УСПЕШНО ПЕРЕСЛАЛ СООБЩЕНИЕ С ID: {event.message_id} С СООБЩЕНИЕМ {message} В ДИАЛОГЕ /// БЕСЕДЕ С ID: {event.peer_id}")
        else:
            print_white(f"НЕЙРОСЕТЬ {login} УСПЕШНО ОТВЕТИЛ НА СООБЩЕНИЕ С ID: {event.message_id} С СООБЩЕНИЕМ {message} В ДИАЛОГЕ /// БЕСЕДЕ С ID: {event.peer_id}")

async def neuro_generate(user_message):
    response = await client.chat.completions.create(
        model=model,
        provider=provider,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ]
    )
    message = response.choices[0].message.content
    if message and filter_message(message):
        return message
    else:
        if random.random() < 0.5:
            print_white("ГЕНЕРИРУЕМ НОВОЕ СООБЩЕНИЕ...")
            return await neuro_generate(user_message)
        else:
            return None

def load_proxy(proxy_path):
    with open(proxy_path, 'r') as file:
        proxy = file.readline().strip()
    return proxy if proxy else ''

def load_headers(headers_path):
    with open(headers_path, 'r') as file:
        headers = file.read()
    return json.loads(headers)

def filter_message(message):
    forbidden_patterns = [
        r"\bизвини\b",
        r"\bпрости\b",
        r"\bне могу помочь\b",
        r"\bне готов обсуждать\b",
        # ... другие паттерны
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            print_white("СООБЩЕНИЕ НЕ БУДЕТ ОТПРАВЛЕНО ИЗ-ЗА ФИЛЬТРА!")
            return None
    return message

async def run():
    token = sys.argv[1]
    login = sys.argv[2]
    friend_ids_str = sys.argv[3]
    proxy_path = sys.argv[4]
    headers_path = sys.argv[5]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)

    friend_ids = [int(id) for id in friend_ids_str.split(',') if id]
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        await neuro(session, token, login, friend_ids, proxy)

asyncio.run(run())