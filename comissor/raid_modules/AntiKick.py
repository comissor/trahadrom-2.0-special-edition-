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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
chats = {}

def input_white(prompt):
    print("\033[97m" + prompt + "\033[1m", end="")
    return input()

def print_white(text):
    print(f"{WHITE}{BOLD}{text}{RESET}")

async def antikick(session, token, login, proxy):
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    async def listen_longpoll():
        for event in longpoll.listen():
            try:
                if event.type_id == VkChatEventType.USER_KICKED:
                    chat_id = event.chat_id
                    chat_title = await get_chat_title(session, token, chat_id, proxy)
                    logging.debug(f"ПОЛЬЗОВАТЕЛЬ {event.info['user_id']} БЫЛ КИКНУТ ИЗ БЕСЕДЫ {chat_title}")
                    await add_user_to_chat(session, token, chat_id, event.info['user_id'], login, chat_title, proxy)

            except Exception as e:
                logging.error(f"ОШИБКА ПРИ ОБРАБОТКЕ СОБЫТИЯ: {e}")

    async def add_user_to_chat(session, token, chat_id, user_id, login, chat_title, proxy):
        url = 'https://api.vk.com/method/messages.addChatUser'
        params = {
            'access_token': token,
            'v': '5.131',
            'chat_id': chat_id,
            'user_id': user_id
        }
        try:
            async with session.post(url, params=params, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    user_info = await get_user_info(session, token, user_id, proxy)
                    user_name = f"{user_info['first_name']} {user_info['last_name']}"
                    print_white(f"ЛОГИН {login} ВЕРНУЛ ДРУГА {user_name} В БЕСЕДУ {chat_title}")
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ ДОБАВЛЕНИИ ОБРАТНО В ЧАТ: {error_code} - {error_msg}")

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ДОБАВЛЕНИИ ПОЛЬЗОВАТЕЛЯ {user_id} В БЕСЕДУ {chat_id}: {e}")

    await listen_longpoll()

async def get_user_info(session, token, user_id, proxy):
    url = 'https://api.vk.com/method/users.get'
    params = {
        'access_token': token,
        'v': '5.131',
        'user_ids': user_id
    }
    async with session.get(url, params=params, proxy=proxy) as response:
        if response.status == 200:
            result = await response.json()
            return result['response'][0]

async def get_chat_title(session, token, chat_id, proxy):
    url = 'https://api.vk.com/method/messages.getChat'
    params = {
        'access_token': token,
        'v': '5.131',
        'chat_id': chat_id
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'error' in data:
                    logging.error(f"ОШИБКА: {data['error']['error_msg']}")
                    return None
                else:
                    return data['response']['title']  

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА: {e}")
        return 

def load_proxy(proxy_path):
    with open(proxy_path, 'r') as file:
        proxy = file.readline().strip()
    return proxy if proxy else ''

def load_headers(headers_path):
    with open(headers_path, 'r') as file:
        headers = file.read()
    return json.loads(headers)

async def run():
    token = sys.argv[1]
    login = sys.argv[2]
    proxy_path = sys.argv[3]
    headers_path = sys.argv[4]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        await antikick(session, token, login, proxy)

asyncio.run(run())