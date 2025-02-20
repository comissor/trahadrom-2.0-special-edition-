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

async def send_sticker(session, chat_id, token, login, chat_title, index, theme_state, proxy, captcha_params=None):
    url_messages_send = 'https://api.vk.com/method/messages.send'
    url_messages_set_conversation_style = 'https://api.vk.com/method/messages.setConversationStyle'
    sticker_id = random.randint(9008, 9047)
    message_id = None

    try:
        params_send = {
            'chat_id': chat_id, 
            'random_id': random.randint(1, 999999),
            'sticker_id': sticker_id,
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
                            return await send_sticker(session, chat_id, token, login, chat_title, index, theme_state, proxy, captcha_params)

                        except Exception as captcha_error:
                            print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")

                else:
                    logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СТИКЕРА: {error_code} - {error_msg}")
                    return

        if message_id:
            if theme_state == "True":
                theme = await set_chat_theme(session, token, chat_id, proxy) 
                print_white(f"ЛОГИН {login} ОТПРАВИЛ СТИКЕР {sticker_id} В БЕСЕДУ {chat_title} И ИЗМЕНИЛ ТЕМУ НА {theme} - {index}")
            else:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ СТИКЕР {sticker_id} В БЕСЕДУ {chat_title} - {index}")
            return {"success": True}

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ОТПРАВКЕ СТИКЕРА: {e}")
        return {"error": str(e)}

async def set_chat_theme(session, token, chat_id, proxy):
    url_messages_set_conversation_style = 'https://api.vk.com/method/messages.setConversationStyle'
    themes = ["emerald", "midnight", "new_year", "frost", "halloween_violet", "halloween_orange", "unicorn", "twilight", "sunset", "retrowave", "marine", "lagoon", "disco", "crimson", "candy"]
    theme = random.choice(themes)
    params_set_conversation_style = {
        'style': theme,
        'peer_id': 2000000000 + chat_id,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post(url_messages_set_conversation_style, params=params_set_conversation_style, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
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
                        solved = True

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
    theme_state = sys.argv[6]
    proxy_path = sys.argv[7]
    headers_path = sys.argv[8]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        while True:
            await send_sticker(session, chat_id, token, login, chat_title, index, theme_state, proxy)
            index += 1
            time.sleep(0.33)

asyncio.run(run())