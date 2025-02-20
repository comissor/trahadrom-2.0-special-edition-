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
from raid_utils import reg

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

async def join_chat(session, login, token, chat_link, proxy):
    url = 'https://api.vk.com/method/messages.joinChatByInviteLink'
    params = {
        'access_token': token,
        'v': '5.131',
        'link': chat_link
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'error' in data:
                    logging.error(f"ОШИБКА НА ЛОГИНЕ {login}: {data['error']['error_msg']}")
                else:
                    chat_id = data['response']['chat_id']
                    print_white(f"ЛОГИН {login} ЗАШЕЛ В БЕСЕДУ {chat_link}")
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА: {e}")

async def invite_friends_to_chat(session, login, token, chat_id, chat_title, proxy):
    friends = await reg.get_friends_token(session, token, proxy)

    friend_infos = await reg.get_user_info(session, token, friends, proxy)  

    url = 'https://api.vk.com/method/messages.addChatUser'
    for friend_info in friend_infos: 
        friend_id = friend_info['id']
        params = {
            'access_token': token,
            'v': '5.131',
            'chat_id': chat_id,
            'user_id': friend_id
        }
        try:
            async with session.post(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'error' in data:
                        logging.error(f"ОШИБКА НА ЛОГИНЕ {login}: {data['error']['error_msg']}")
                    else:
                        friend_name = f"{friend_info['first_name']} {friend_info['last_name']}"
                        print_white(f"ПРИГЛАШЕН ДРУГ {friend_name} В БЕСЕДУ {chat_title} НА ЛОГИНЕ {login}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА: {e}")