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

async def accept_friend_requests(session, token, login, proxy):
    last_seen_request_id = None

    while True:
        try:
            async with session.get('https://api.vk.com/method/friends.getRequests', params={'access_token': token, 'v': '5.131', 'out': 0}, proxy=proxy) as response:
                friend_requests = await response.json()

            if friend_requests['response']['count'] > 0 and friend_requests['response']['items'][0] != last_seen_request_id:
                for user_id in friend_requests['response']['items']:
                    if user_id != last_seen_request_id:
                        async with session.get('https://api.vk.com/method/users.get', params={'access_token': token, 'v': '5.131', 'user_ids': user_id}, proxy=proxy) as user_response:
                            user_info = await user_response.json()
                            if user_info['response'][0].get('deactivated') not in ['deleted', 'banned']:
                                async with session.get('https://api.vk.com/method/friends.add', params={'access_token': token, 'v': '5.131', 'user_id': user_id}, proxy=proxy) as add_response:
                                    add_result = await add_response.json()
                                    if 'error' not in add_result:
                                        print_white(f'НА ЛОГИНЕ {login} ПРИНЯТА ЗАЯВКА В ДРУЗЬЯ ОТ {user_info["response"][0]["first_name"]} {user_info["response"][0]["last_name"]} (ID: {user_id})')
                                    else:
                                        error_code = add_result['error']['error_code']
                                        error_msg = add_result['error']['error_msg']
                                        logging.error(f"ОШИБКА VK API ПРИ ПРИНЯТИИ ЗАЯВКИ В ДРУЗЬЯ: {error_code} - {error_msg}")
                            else:
                                print_white(f'ЗАЯВОЧКА ОТ ДРУГА С ID: {user_id} ПРОИГНОРИРОВАНА - ОН ЗАБАНЕН ИЛИ УДАЛЕН')

                    last_seen_request_id = user_id

        except Exception as e:
            logging.error(f'ОШИБОЧКА: {e}')

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
        await accept_friend_requests(session, token, login, proxy)
        
asyncio.run(run())