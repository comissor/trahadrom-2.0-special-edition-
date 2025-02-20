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

def input_white(prompt):
    print("\033[97m" + prompt + "\033[1m", end="")
    return input()

def print_white(text):
    print(f"{WHITE}{BOLD}{text}{RESET}")

async def set_chat_theme(session, chat_id, token, login, chat_title, index, proxy, captcha_params=None):
    url_messages_set_conversation_style = 'https://api.vk.com/method/messages.setConversationStyle'
    themes = ["emerald", "midnight", "new_year", "frost", "halloween_violet", "halloween_orange", "unicorn", "twilight", "sunset", "retrowave", "marine", "lagoon", "disco", "crimson", "candy"]
    theme = random.choice(themes)
    params_set_conversation_style = {
        'style': theme,
        'peer_id': 2000000000 + chat_id,
        'access_token': token,
        'v': '5.131'
    }
    
    if captcha_params: 
            params_set_conversation_style.update(captcha_params)

    async with session.post(url_messages_set_conversation_style, params=params_set_conversation_style, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСТАНОВИЛ ТЕМУ ЧАТА {theme} В БЕСЕДЕ {chat_title} - {index}")
            return theme
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
                        return await set_chat_theme(session, chat_id, token, login, chat_title, index, proxy, captcha_params)

                    except Exception as captcha_error:
                        print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")

            else:
                logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ ТЕМЫ ЧАТА: {error_code} - {error_msg}")
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
    chat_id = int(sys.argv[1])
    token = sys.argv[2]
    login = sys.argv[3]
    chat_title = sys.argv[4]
    index = int(sys.argv[5])
    proxy_path = sys.argv[6]
    headers_path = sys.argv[7]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        while True:
            await set_chat_theme(session, chat_id, token, login, chat_title, index, proxy)
            index += 1
            time.sleep(0.33)

asyncio.run(run())