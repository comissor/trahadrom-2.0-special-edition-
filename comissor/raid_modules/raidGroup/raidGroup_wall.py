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

async def send_wall_group_post(session, owner_id, token, login, index, message, photo_folder, use_photos, group_name, proxy, captcha_params=None):
    url_wall_post = 'https://api.vk.com/method/wall.post'
    url_photos_get_wall_upload_server = 'https://api.vk.com/method/photos.getWallUploadServer'
    url_photos_save_wall_photo = 'https://api.vk.com/method/photos.saveWallPhoto'
    url_docs_get_wall_upload_server = 'https://api.vk.com/method/docs.getWallUploadServer'
    url_docs_save = 'https://api.vk.com/method/docs.save'

    try:
        attachment = ''
        photo_name = ''
        post_id = None
        if use_photos:
            photo_name = random.choice(os.listdir(photo_folder))
            photo_path = os.path.join(photo_folder, photo_name)

            if photo_name.lower().endswith('.gif'):
                params_get_upload_server = {'access_token': token, 'v': '5.131', 'owner_id': -owner_id} 
                async with session.get(url_docs_get_wall_upload_server, params=params_get_upload_server, proxy=proxy) as response:
                    upload_url = (await response.json())['response']['upload_url']

                with open(photo_path, 'rb') as photo_file:
                    data = aiohttp.FormData()
                    data.add_field('file', photo_file, filename=photo_name)
                    async with session.post(upload_url, data=data, proxy=proxy) as upload_response:
                        upload_result = await upload_response.json()

                params_save_doc = {
                    'access_token': token,
                    'v': '5.131',
                    'file': upload_result['file'],
                    'owner_id': -owner_id  
                }
                async with session.post(url_docs_save, params=params_save_doc, proxy=proxy) as response:
                    save_result = await response.json()
                    doc = save_result['response']['doc']
                    attachment = f'doc{doc["owner_id"]}_{doc["id"]}'
            else:
                
                params_get_upload_server = {'access_token': token, 'v': '5.131', 'owner_id': -owner_id}  
                async with session.get(url_photos_get_wall_upload_server, params=params_get_upload_server, proxy=proxy) as response:
                    upload_url = (await response.json())['response']['upload_url']

                with open(photo_path, 'rb') as photo_file:
                    data = aiohttp.FormData()
                    data.add_field('photo', photo_file, filename=photo_name)
                    async with session.post(upload_url, data=data, proxy=proxy) as upload_response:
                        upload_result = await upload_response.json()

                params_save_wall_photo = {
                    'access_token': token,
                    'v': '5.131',
                    'photo': upload_result['photo'],
                    'server': upload_result['server'],
                    'hash': upload_result['hash'],
                    'owner_id': -owner_id 
                }
                async with session.post(url_photos_save_wall_photo, params=params_save_wall_photo, proxy=proxy) as response:
                    save_result = await response.json()
                    photo = save_result['response'][0]
                    attachment = f'photo{photo["owner_id"]}_{photo["id"]}'

        params_wall_post = {
            'owner_id': -owner_id,
            'message': message or '',
            'attachments': attachment,
            'access_token': token,
            'v': '5.131'
        }

        if captcha_params: 
            params_wall_post.update(captcha_params)

        async with session.post(url_wall_post, params=params_wall_post, proxy=proxy) as response:
            post_result = await response.json()
            if 'error' not in post_result:
                post_id = post_result['response']['post_id']
            else:
                error_code = post_result['error']['error_code']
                error_msg = post_result['error']['error_msg']
                if error_code == 14:
                    solved = False
                    while not solved:
                        try:
                            print_white(f"ВНИМАНИЕ! ОБНАРУЖЕНА КАПЧА! РЕШАЕМ...")
                            captcha_sid = post_result['error']['captcha_sid']
                            captcha_solution = await vc.solve(sid=captcha_sid, s=1)
                            print_white(f"РЕШИЛИ КАПЧУ! ВОТ ЕЁ РЕШЕНИЕ: {captcha_solution}")
                            captcha_params = {'captcha_sid': captcha_sid, 'captcha_key': captcha_solution}
                            solved = True
                            time.sleep(3)
                            return await send_wall_group_post(session, owner_id, token, login, index, message, photo_folder, use_photos, group_name, proxy, captcha_params)

                        except Exception as captcha_error:
                            print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")

                else:
                    logging.error(f"ОШИБКА VK API ПРИ РАЗМЕЩЕНИИ ПОСТА В ГРУППЕ ИЛИ ПРЕДЛОЖКЕ: {error_code} - {error_msg}")
                    return

        if post_id:
            if message and use_photos:
                print_white(f"ЛОГИН {login} РАЗМЕСТИЛ НОВУЮ ЗАПИСЬ C ID: {post_id} С СООБЩЕНИЕМ {message} И ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name} НА СТЕНЕ ИЛИ ПРЕДЛОЖКЕ ГРУППЫ {group_name} - {index}")
            elif message:
                print_white(f"ЛОГИН {login} РАЗМЕСТИЛ НОВУЮ ЗАПИСЬ C ID: {post_id} С СООБЩЕНИЕМ {message} НА СТЕНЕ ИЛИ ПРЕДЛОЖКЕ ГРУППЫ {group_name} - {index}")
            else:
                print_white(f"ЛОГИН {login} РАЗМЕСТИЛ НОВУЮ ЗАПИСЬ С ID: {post_id} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name} НА СТЕНЕ ИЛИ ПРЕДЛОЖКЕ ГРУППЫ {group_name} - {index}")

    except Exception as e:
        logging.error(f"ОШИБОЧКА: {e}")

def read_messages(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            messages = file.readlines()
            if len(messages) == 0:
                return None
            elif len(messages) == 1:
                return messages[0].strip()
            else:
                return random.choice(messages).strip()
    except FileNotFoundError:
        return None

def load_proxy(proxy_path):
    with open(proxy_path, 'r') as file:
        proxy = file.readline().strip()
    return proxy if proxy else ''

def load_headers(headers_path):
    with open(headers_path, 'r') as file:
        headers = file.read()
    return json.loads(headers)

async def run():
    owner_id = int(sys.argv[1])
    token = sys.argv[2]
    login = sys.argv[3]
    index = int(sys.argv[4])
    message_file = sys.argv[5]
    photo_folder = sys.argv[6]
    use_photos = sys.argv[7].lower() == 'true'
    group_name = sys.argv[8]
    proxy_path = sys.argv[9]
    headers_path = sys.argv[10]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        while True:
            message = read_messages(message_file)
            await send_wall_group_post(session, owner_id, token, login, index, message, photo_folder, use_photos, group_name, proxy)
            index += 1
            time.sleep(0.33)

asyncio.run(run())