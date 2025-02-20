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

async def send_message(session, group_id, token, login, index, message, use_photos, photo_folder, group_name, manager_state, attach, proxy, captcha_params=None):
    url_messages_send = 'https://api.vk.com/method/messages.send'
    url_messages_edit = 'https://api.vk.com/method/messages.edit'
    url_photos_get_messages_upload_server = 'https://api.vk.com/method/photos.getMessagesUploadServer'
    url_photos_save_messages_photo = 'https://api.vk.com/method/photos.saveMessagesPhoto'
    url_docs_get_messages_upload_server = 'https://api.vk.com/method/docs.getMessagesUploadServer'
    url_docs_save = 'https://api.vk.com/method/docs.save'

    try:
        attachment = attach or ''
        photo_name = ''
        message_id = None
        if use_photos:
            photo_name = random.choice(os.listdir(photo_folder))
            photo_path = os.path.join(photo_folder, photo_name)

            if photo_name.lower().endswith('.gif'):
                params_get_upload_server = {'access_token': token, 'v': '5.131', 'peer_id': -group_id}
                async with session.get(url_docs_get_messages_upload_server, params=params_get_upload_server, proxy=proxy) as response:
                    upload_url = (await response.json())['response']['upload_url']

                with open(photo_path, 'rb') as photo_file:
                    data = aiohttp.FormData()
                    data.add_field('file', photo_file, filename=photo_name)
                    async with session.post(upload_url, data=data, proxy=proxy) as upload_response:
                        upload_result = await upload_response.json()

                params_save_doc = {
                    'access_token': token,
                    'v': '5.131',
                    'file': upload_result['file']
                }
                async with session.post(url_docs_save, params=params_save_doc, proxy=proxy) as response:
                    save_result = await response.json()
                    doc = save_result['response']['doc']
                    if attachment:
                        attachment += ',' + f'doc{str(doc["owner_id"])}_{str(doc["id"])}'
                    else:
                        attachment = f'doc{str(doc["owner_id"])}_{str(doc["id"])}'

            else:
                
                params_get_upload_server = {'access_token': token, 'v': '5.131', 'peer_id': -group_id}
                async with session.get(url_photos_get_messages_upload_server, params=params_get_upload_server, proxy=proxy) as response:
                    upload_url = (await response.json())['response']['upload_url']

                with open(photo_path, 'rb') as photo_file:
                    data = aiohttp.FormData()
                    data.add_field('photo', photo_file, filename=photo_name)
                    async with session.post(upload_url, data=data, proxy=proxy) as upload_response:
                        upload_result = await upload_response.json()

                params_save_messages_photo = {
                    'access_token': token,
                    'v': '5.131',
                    'photo': upload_result['photo'],
                    'server': upload_result['server'],
                    'hash': upload_result['hash']
                }
                async with session.post(url_photos_save_messages_photo, params=params_save_messages_photo, proxy=proxy) as response:
                    save_result = await response.json()
                    photo = save_result['response'][0]
                    if attachment:
                        attachment += ',' + f'photo{str(photo["owner_id"])}_{str(photo["id"])}'
                    else:
                        attachment = f'photo{str(photo["owner_id"])}_{str(photo["id"])}'

        if manager_state:
            params_send = {
                'peer_id': -group_id,  
                'message': "ГОЙДА",
                'random_id': random.randint(1, 999999),
                'access_token': token,
                'v': '5.131'
            }

            if captcha_params: 
                params_send.update(captcha_params)

            async with session.post(url_messages_send, params=params_send, proxy=proxy) as response:
                send_message_result = await response.json()
                if 'error' not in send_message_result:
                    send_message_id = send_message_result['response']
                else:
                    error_code = send_message_result['error']['error_code']
                    error_msg = send_message_result['error']['error_msg']
                    if error_code == 14:
                        solved = False
                        while not solved:
                            try:
                                print_white(f"ВНИМАНИЕ! ОБНАРУЖЕНА КАПЧА! РЕШАЕМ...")
                                captcha_sid = send_message_result['error']['captcha_sid']
                                captcha_solution = await vc.solve(sid=captcha_sid, s=1)
                                print_white(f"РЕШИЛИ КАПЧУ! ВОТ ЕЁ РЕШЕНИЕ: {captcha_solution}")
                                captcha_params = {'captcha_sid': captcha_sid, 'captcha_key': captcha_solution}
                                solved = True
                                time.sleep(3)
                                return await send_message(session, group_id, token, login, index, message, use_photos, photo_folder, group_name, manager_state, attach, proxy, captcha_params)

                            except Exception as captcha_error:
                                print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")

                    else:
                        logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ: {error_code} - {error_msg}")
                        return

            params_edit = {
                'peer_id': -group_id, 
                'message': message or '',
                'attachment': attachment,
                'message_id': send_message_id,
                'random_id': random.randint(1, 999999),
                'access_token': token,
                'v': '5.131'
            }

            if captcha_params: 
                params_edit.update(captcha_params)

            async with session.post(url_messages_edit, params=params_edit, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    message_id = result
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
                                return await send_message(session, group_id, token, login, index, message, use_photos, photo_folder, group_name, manager_state, attach, proxy, captcha_params)

                            except Exception as captcha_error:
                                print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")

                    else:
                        logging.error(f"ОШИБКА VK API ПРИ РЕДАКТИРОВАНИИ СООБЩЕНИЯ: {error_code} - {error_msg}")
                        return
        else:
            params_send = {
                'peer_id': -group_id,
                'message': message or '',
                'attachment': attachment,
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
                                return await send_message(session, group_id, token, login, index, message, use_photos, photo_folder, group_name, manager_state, attach, proxy, captcha_params)

                            except Exception as captcha_error:
                                print_white(f"ОШИБОЧКА ПРИ РЕШЕНИИ КАПЧИ: {captcha_error}")

                    else:
                        logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ: {error_code} - {error_msg}")
                        return

        if message_id:
            if manager_state:
                message_part = f"ГОЙДА А ЗАТЕМ ИЗМЕНИЛ НА {message}"
            else:
                message_part = message

            if message and use_photos and attach:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ {message_part} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name}, ВЛОЖЕНИЕМ - {attach} В ЛС ГРУППЫ {group_name} - {index}")
            elif message and use_photos:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ {message_part} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name} В ЛС ГРУППЫ {group_name} - {index}")
            elif message and attach:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ {message_part} С ВЛОЖЕНИЕМ - {attach} В ЛС ГРУППЫ {group_name} - {index}")
            elif message:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ {message_part} В ЛС ГРУППЫ {group_name} - {index}")
            elif use_photos and attach:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ {'СООБЩЕНИЕ ГОЙДА А ЗАТЕМ ИЗМЕНИЛ НА ' if manager_state else ''}ФОТОГРАФИЮ ИЛИ ГИФКУ - {photo_name}, ВЛОЖЕНИЕМ - {attach} В ЛС ГРУППЫ {group_name} - {index}")
            elif use_photos:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ {'СООБЩЕНИЕ ГОЙДА А ЗАТЕМ ИЗМЕНИЛ НА ' if manager_state else ''}ФОТОГРАФИЮ ИЛИ ГИФКУ - {photo_name} В ЛС ГРУППЫ {group_name} - {index}")
            else:
                print_white(f"ЛОГИН {login} ОТПРАВИЛ {'СООБЩЕНИЕ ГОЙДА А ЗАТЕМ ИЗМЕНИЛ НА ' if manager_state else ''}ВЛОЖЕНИЕ - {attach} В ЛС ГРУППЫ {group_name} - {index}")

    except Exception as e:
        logging.error(f"ОШИБОЧКА: {e}")

async def ban_group(session, group_id, token, login, group_name, proxy=proxy):
    url_account_ban = 'https://api.vk.com/method/account.ban'
    try:
        params_account_ban = {
            'owner_id': -group_id,
            'access_token': token,
            'v': '5.131'
        }
        async with session.post(url_account_ban, params=params_account_ban, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                print_white(f"ГРУППА {group_name} УСПЕШНО ДОБАВЛЕНА В ЧЕРНЫЙ СПИСОК НА ЛОГИНЕ {login}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ДОБАВЛЕНИИ ГРУППЫ В ЧЕРНЫЙ СПИСОК: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        print_white(f"ОШИБОЧКА ПРИ ДОБАВЛЕНИИ ГРУППЫ {group_name} В ЧЕРНЫЙ СПИСОК НА ЛОГИНЕ {login}: {e}")

async def unban_group(session, group_id, token, login, group_name, proxy):
    url_account_unban = 'https://api.vk.com/method/account.unban'
    try:
        params_account_unban = {
            'owner_id': -group_id,
            'access_token': token,
            'v': '5.131'
        }
        async with session.post(url_account_unban, params=params_account_unban, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                print_white(f"ГРУППА {group_name} УСПЕШНО УДАЛЕНА ИЗ ЧЕРНОГО СПИСКА НА ЛОГИНЕ {login}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ГРУППЫ ИЗ ЧЕРНОГО СПИСКА: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        print_white(f"ОШИБОЧКА ПРИ УДАЛЕНИИ ГРУППЫ {group_name} ИЗ ЧЕРНОГО СПИСКА НА ЛОГИНЕ {login}: {e}")

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
    group_id = int(sys.argv[1])
    token = sys.argv[2]
    login = sys.argv[3]
    index = int(sys.argv[4])
    message_file = sys.argv[5]
    photo_folder = sys.argv[6]
    use_photos = sys.argv[7].lower() == 'true'
    group_name = sys.argv[8]
    manager_state = sys.argv[9].lower() == 'true'
    attach_file = sys.argv[10]
    use_attach = sys.argv[11].lower() == 'true'
    proxy_path = sys.argv[12]
    headers_path = sys.argv[13]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        while True:
            message = read_messages(message_file)
            if use_attach:
                attach = read_messages(attach_file)
            else:
                attach = ''
            await unban_group(session, group_id, token, login, group_name, proxy)
            await send_message(session, group_id, token, login, index, message, use_photos, photo_folder, group_name, manager_state, attach, proxy)
            await ban_group(session, group_id, token, login, group_name, proxy)
            index += 1
            time.sleep(0.33)

asyncio.run(run())