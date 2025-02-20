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

async def antichange(session, chat_id, token, login, new_title, new_message, use_photo, photo_folder, avatars_folder, use_avatar, attach, proxy):
    url_messages_edit_chat = 'https://api.vk.com/method/messages.editChat'
    url_photos_get_chat_upload_server = 'https://api.vk.com/method/photos.getChatUploadServer'
    url_messages_set_chat_photo = 'https://api.vk.com/method/messages.setChatPhoto'
    url_messages_send = 'https://api.vk.com/method/messages.send'
    url_messages_pin = 'https://api.vk.com/method/messages.pin'
    url_messages_get_conversations_by_id = 'https://api.vk.com/method/messages.getConversationsById'
    url_photos_get_messages_upload_server = 'https://api.vk.com/method/photos.getMessagesUploadServer'
    url_photos_save_messages_photo = 'https://api.vk.com/method/photos.saveMessagesPhoto'
    url_docs_get_messages_upload_server = 'https://api.vk.com/method/docs.getMessagesUploadServer'
    url_docs_save = 'https://api.vk.com/method/docs.save'

    try:
        if new_title != "None":
            params_edit_chat = {
                'chat_id': chat_id,
                'title': new_title,
                'access_token': token,
                'v': '5.131'
            }
            async with session.post(url_messages_edit_chat, params=params_edit_chat, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    print_white(f"ЛОГИН {login} ИЗМЕНИЛ НАЗВАНИЕ БЕСЕДЫ НА {new_title} В БЕСЕДЕ С ID: {chat_id}")
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
                        logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ НАЗВАНИЯ В БЕСЕДЕ: {error_code} - {error_msg}")

        if use_avatar == "Yes":
            photos = [os.path.join(avatars_folder, f) for f in os.listdir(avatars_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            random_photo = random.choice(photos)

            params_get_chat_upload_server = {
                'chat_id': chat_id,
                'access_token': token,
                'v': '5.131'
            }
            async with session.get(url_photos_get_chat_upload_server, params=params_get_chat_upload_server, proxy=proxy) as response:
                upload_server = await response.json()

            with open(random_photo, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('photo', f, filename=os.path.basename(random_photo))
                async with session.post(upload_server['response']['upload_url'], data=data, proxy=proxy) as response:
                    result = await response.json()

            params_set_chat_photo = {
                'file': result['response'],
                'access_token': token,
                'v': '5.131'
            }
            async with session.post(url_messages_set_chat_photo, params=params_set_chat_photo, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    print_white(f"ЛОГИН {login} ИЗМЕНИЛ АВАТАРКУ В БЕСЕДЕ C ID: {chat_id}")
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
                        logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ АВАТАРКИ В БЕСЕДЕ: {error_code} - {error_msg}")

        if new_message != "None":
            attachment = attach or '',
            photo_name = ''
            if use_photo:
                photo_name = random.choice(os.listdir(photo_folder))
                photo_path = os.path.join(photo_folder, photo_name)

                if photo_name.lower().endswith('.gif'):
                    params_get_upload_server = {'access_token': token, 'v': '5.131', 'peer_id': 2000000000 + chat_id}
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
                    params_get_upload_server = {'access_token': token, 'v': '5.131','peer_id': 2000000000 + chat_id}
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

            params_send = {
                'chat_id': chat_id,
                'message': new_message,
                'attachment': attachment,
                'random_id': random.randint(1, 999999),
                'access_token': token,
                'v': '5.131'
            }
            async with session.post(url_messages_send, params=params_send, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    message_id = result['response']
                    if use_photo and attach:
                        print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name}, ВЛОЖЕНИЕМ - {attach} В БЕСЕДЕ С ID: {chat_id}")
                    elif use_photo:
                        print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name} В БЕСЕДЕ С ID: {chat_id}")
                    elif attach:
                        print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} С ВЛОЖЕНИЕМ - {attach} В БЕСЕДЕ С ID: {chat_id}")
                    else:
                        print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} В БЕСЕДЕ С ID: {chat_id}")
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
                        logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ В БЕСЕДУ: {error_code} - {error_msg}")

            params_pin = {
                'peer_id': 2000000000 + chat_id,
                'message_id': message_id,
                'access_token': token,
                'v': '5.131'
            }
            async with session.post(url_messages_pin, params=params_pin, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    print_white(f"ЛОГИН {login} ЗАКРЕПИЛ СООБЩЕНИЕ С ID: {message_id} В БЕСЕДЕ С ID: {chat_id}")
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
                        logging.error(f"ОШИБКА VK API ПРИ ЗАКРЕПЛЕНИИ СООБЩЕНИЯ В БЕСЕДЕ: {error_code} - {error_msg}")
                        
        params_getById = {
            'peer_ids': 2000000000 + chat_id,
            'access_token': token,
            'v': '5.131'
        }
        async with session.post(url_messages_get_conversations_by_id, params=params_getById, proxy=proxy) as response:
            chat_info = await response.json()

        if new_title != "None":
            current_title = chat_info['response']['items'][0]['chat_settings']['title'] 
        if use_avatar == "Yes":
            current_photo_url = chat_info['response']['items'][0]['chat_settings']['photo']['photo_200'] if 'photo' in chat_info['response']['items'][0]['chat_settings'] else None
        if new_message != "None":
            current_pinned_message_id = message_id

        while True:
            try:
                params_getById = {
                'peer_ids': 2000000000 + chat_id,
                'access_token': token,
                'v': '5.131'
                }
                async with session.post(url_messages_get_conversations_by_id, params=params_getById, proxy=proxy) as response:
                    chat_info = await response.json()
                
                if new_title != "None":
                    new_title = chat_info['response']['items'][0]['chat_settings']['title']

                if 'pinned_message' in chat_info['response']['items'][0]['chat_settings']:
                    new_pinned_message_id = chat_info['response']['items'][0]['chat_settings']['pinned_message']['id']
                else:
                    new_pinned_message_id = None

                if 'photo' in chat_info['response']['items'][0]['chat_settings']:
                    new_photo_url = chat_info['response']['items'][0]['chat_settings']['photo']['photo_200']
                else:
                    new_photo_url = None

                if new_title != "None":
                    if new_title != current_title:
                        params_edit_chat = {
                            'chat_id': chat_id,
                            'title': current_title,
                            'access_token': token,
                            'v': '5.131'
                        }
                        async with session.post(url_messages_edit_chat, params=params_edit_chat, proxy=proxy) as response:
                            result = await response.json()
                            if 'error' not in result:
                                print_white(f"ЛОГИН {login} ВЕРНУЛ НАЗВАНИЕ БЕСЕДЫ НА {current_title} В БЕСЕДЕ С ID: {chat_id}")
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
                                    logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ НАЗВАНИЯ В БЕСЕДЕ: {error_code} - {error_msg}")

                if use_avatar == "Yes":
                    if new_photo_url != current_photo_url:
                        photos = [os.path.join(avatars_folder, f) for f in os.listdir(avatars_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                        random_photo = random.choice(photos)

                        params_get_chat_upload_server = {
                            'chat_id': chat_id,
                            'access_token': token,
                            'v': '5.131'
                        }
                        async with session.get(url_photos_get_chat_upload_server, params=params_get_chat_upload_server, proxy=proxy) as response:
                            upload_server = await response.json()

                        with open(random_photo, 'rb') as f:
                            data = aiohttp.FormData()
                            data.add_field('photo', f, filename=os.path.basename(random_photo))
                            async with session.post(upload_server['response']['upload_url'], data=data, proxy=proxy) as response:
                                result = await response.json()

                        params_set_chat_photo = {
                            'file': result['response'],
                            'access_token': token,
                            'v': '5.131'
                        }
                        async with session.post(url_messages_set_chat_photo, params=params_set_chat_photo, proxy=proxy) as response:
                            result = await response.json()
                            if 'error' not in result:
                                print_white(f"ЛОГИН {login} ИЗМЕНИЛ АВАТАРКУ В БЕСЕДЕ C ID: {chat_id}")
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
                                    logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ АВАТАРКИ В БЕСЕДЕ: {error_code} - {error_msg}")

                        params_get_conversations_by_id = {
                            'peer_ids': 2000000000 + chat_id,
                            'access_token': token,
                            'v': '5.131'
                        }
                        async with session.get(url_messages_get_conversations_by_id, params=params_get_conversations_by_id, proxy=proxy) as response:
                            chat_info = await response.json()
                            current_photo_url = chat_info['response']['items'][0]['chat_settings']['photo']['photo_200'] if 'photo' in chat_info['response']['items'][0]['chat_settings'] else None

                if new_message != "None":
                    if new_pinned_message_id != current_pinned_message_id:
                        try:
                            params_pin = {
                                'peer_id': 2000000000 + chat_id,
                                'message_id': current_pinned_message_id,
                                'access_token': token,
                                'v': '5.131'
                            }
                            async with session.post(url_messages_pin, params=params_pin, proxy=proxy) as response:
                                params_get_conversations_by_id = {
                                    'peer_ids': 2000000000 + chat_id,
                                    'access_token': token,
                                    'v': '5.131'
                                }
                                async with session.get(url_messages_get_conversations_by_id, params=params_get_conversations_by_id, proxy=proxy) as response:
                                    chat_info = await response.json()
                                    if 'error' not in chat_info:
                                        pinned_message_id = chat_info['response']['items'][0]['chat_settings']['pinned_message']['id']
                                        if pinned_message_id == current_pinned_message_id:
                                            print_white(f"ЛОГИН {login} УСПЕШНО ЗАКРЕПИЛ СТАРОЕ СООБЩЕНИЕ С ID: {current_pinned_message_id} В БЕСЕДЕ С ID: {chat_id}")
                                    else:
                                        error_code = chat_info['error']['error_code']
                                        error_msg = chat_info['error']['error_msg']
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
                                            logging.error(f"ОШИБКА VK API ПРИ ПОЛУЧЕНИИ СТАРОГО СООБЩЕНИЯ: {error_code} - {error_msg}")
                        
                        except Exception as e:
                            if isinstance(e, KeyError) and e.args[0] == 'pinned_message':
                                print_white(f"ЛОГИН {login}: ЗАКРЕПЛЕННОЕ СООБЩЕНИЕ БЫЛО УДАЛЕНО В БЕСЕДЕ С ID: {chat_id}")

                                attachment = attach or '',
                                photo_name = ''
                                if use_photo:
                                    photo_name = random.choice(os.listdir(photo_folder))
                                    photo_path = os.path.join(photo_folder, photo_name)

                                    if photo_name.lower().endswith('.gif'):
                                        params_get_upload_server = {'access_token': token, 'v': '5.131', 'peer_id': 2000000000 + chat_id}
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
                                        params_get_upload_server = {'access_token': token, 'v': '5.131','peer_id': 2000000000 + chat_id}
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

                                params_send = {
                                    'chat_id': chat_id,
                                    'message': new_message,
                                    'attachment': attachment,
                                    'random_id': random.randint(1, 999999),
                                    'access_token': token,
                                    'v': '5.131'
                                }
                                async with session.post(url_messages_send,params=params_send, proxy=proxy) as response:
                                    result = await response.json()
                                    if 'error' not in result:
                                        message_id = result['response']
                                        if use_photo and attach:
                                            print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name}, ВЛОЖЕНИЕМ - {attach} В БЕСЕДЕ С ID: {chat_id}")
                                        elif use_photo:
                                            print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} С ФОТОГРАФИЕЙ ИЛИ ГИФКОЙ - {photo_name} В БЕСЕДЕ С ID: {chat_id}")
                                        elif attach:
                                            print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} С ВЛОЖЕНИЕМ - {attach} В БЕСЕДЕ С ID: {chat_id}")
                                        else:
                                            print_white(f"ЛОГИН {login} ОТПРАВИЛ СООБЩЕНИЕ: {new_message} В БЕСЕДЕ С ID: {chat_id}")
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
                                            logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ В БЕСЕДУ: {error_code} - {error_msg}")

                                params_pin = {
                                    'peer_id': 2000000000 + chat_id,
                                    'message_id': message_id,
                                    'access_token': token,
                                    'v': '5.131'
                                }
                                async with session.post(url_messages_pin, params=params_pin, proxy=proxy) as response:
                                    result = await response.json()
                                    if 'error' not in result:
                                        current_pinned_message_id = message_id
                                        print_white(f"ЛОГИН {login} ЗАКРЕПИЛ СООБЩЕНИЕ С ID: {message_id} В БЕСЕДЕ С ID: {chat_id}")
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
                                            logging.error(f"ОШИБКА VK API ПРИ ЗАКРЕПЛЕНИИ СООБЩЕНИЯ В БЕСЕДЕ: {error_code} - {error_msg}")

            except Exception as e:
                logging.error(f"ОШИБКА: {e}")

            await asyncio.sleep(3)

    except Exception as e:
        logging.error(f"ОШИБКА: {e}")
        
def read_messages(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            messages = file.readlines()
            if len(messages) == 0:
                return
            elif len(messages) == 1:
                return messages[0].strip()
            else:
                return random.choice(messages).strip()
    except FileNotFoundError:
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
    new_title = sys.argv[5]
    new_message = sys.argv[6]
    use_photo = sys.argv[7].lower() == 'true'
    use_avatar = sys.argv[8]
    photo_folder = sys.argv[9]
    avatars_folder = sys.argv[10]
    attach_file = sys.argv[11]
    use_attach = sys.argv[12].lower() == 'true'
    proxy_path = sys.argv[13]
    headers_path = sys.argv[14]

    headers = load_headers(headers_path)
    proxy = load_proxy(proxy_path)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        if use_attach:
            attach = read_messages(attach_file)
        else:
            attach = ''
        await antichange(session, chat_id, token, login, new_title, new_message, use_photo, photo_folder, avatars_folder, use_avatar, attach, proxy)

asyncio.run(run())