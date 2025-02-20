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

async def set_privacy_settings(session, token, proxy, value):
    url = "https://api.vk.com/method/account.setPrivacy"
    params = {
        'access_token': token,
        'key': 'closed_profile',
        'value': value,
        'v': 5.131
    }
    try:
        async with session.post(url, params=params, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                return await response.json()
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ НАСТРОЕК ПРИВАТНОСТИ: {error_code} - {error_msg}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")
        return 

async def change_profiles(session, tokens, action, proxy): 
    value = "true" if action == "close" else "false"
    tasks = [set_privacy_settings(session, token, proxy, value) for token in tokens.values()]
    results = await asyncio.gather(*tasks)
    for login, result in zip(tokens.keys(), results):
        if 'response' in result:
            action_text = "ЗАКРЫТ" if action == "close" else "ОТКРЫТ"
            print_white(f"ПРОФИЛЬ {login} УСПЕШНО {action_text}")
        else:
            logging.error(f"ОПАНА ОШИБОЧКА {login}: {result}")

async def set_profile_photo(session, token, login, photo_path, proxy):
    upload_server_url = 'https://api.vk.com/method/photos.getOwnerPhotoUploadServer'
    save_photo_url = 'https://api.vk.com/method/photos.saveOwnerPhoto'
    params = {'access_token': token, 'v': '5.131'}

    try:
        async with session.get(upload_server_url, params=params, proxy=proxy) as response:
            upload_url = (await response.json())['response']['upload_url']

        photo_files = [f for f in os.listdir(photo_path) if os.path.isfile(os.path.join(photo_path, f))]

        random_photo = random.choice(photo_files)
        full_photo_path = os.path.join(photo_path, random_photo)

        with open(full_photo_path, 'rb') as photo_file:
            data = {'photo': photo_file}
            async with session.post(upload_url, data=data, proxy=proxy) as upload_response:
                upload_result = await upload_response.json()

        params.update(upload_result)
        async with session.post(save_photo_url, params=params, proxy=proxy) as response:
            result = await response.json()
            if 'error' in result:
                logging.error(f"ОШИБОЧКА ДЛЯ ЛОГИНА {login}: {result['error']['error_msg']}")
            else:
                print_white(f"БЫЛА УСТАНОВЛЕНА ФОТОЧКА \"{os.path.basename(full_photo_path)}\" НА ЛОГИНЕ {login}")

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ УСТАНОВКЕ АВАТАРА: {e}")

async def change_password(session, login, old_password, new_password, token, proxy):
    url = "https://api.vk.com/method/account.changePassword"
    params = {
        "old_password": old_password,
        "new_password": new_password,
        "access_token": token,
        "v": "5.131"
    }
    try:
        async with session.post(url, params=params, proxy=proxy) as response: 
            result = await response.json()
            if 'error' not in result:
                print_white(f"ПАРОЛЬ ИЗМЕНЕН НА {new_password} НА ЛОГИНЕ {login}")
                return True
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ ПАРОЛЯ: {error_code} - {error_msg}")
                return False

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ ИЗМЕНЕНИИ ПАРОЛЯ: {e}")
        return False

async def like_action(session, email, token, owner_id, item_id, type, action, url, proxy):
    params = {'access_token': token, 'v': '5.131', 'type': type, 'owner_id': owner_id, 'item_id': item_id}
    method = f"likes.{action}"

    try:
        async with session.get(f"https://api.vk.com/method/{method}", params=params, proxy=proxy) as response:  
            result = await response.json()
            if 'error' not in result:
                print_white(f"ЛОГИН {email} {action} ЛАЙКИЧ НА {url}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ДОБАВЛЕНИИ ИЛИ УДАЛЕНИЯ ЛАЙКА: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

async def repost_action(session, email, token, object_type, object_id, message, group_id, proxy):
    params = {
        'access_token': token,
        'v': '5.131',
        'object': f"{object_type}{object_id}",
        'message': message
    }
    if group_id:
        params['group_id'] = group_id

    method = "wall.repost"

    try:
        async with session.get(f"https://api.vk.com/method/{method}", params=params, proxy=proxy) as response: 
            result = await response.json()
            if 'error' not in result:
                print_white(f"ЛОГИН {email} СДЕЛАЛ РЕПОСТ {object_type}{object_id} С ПОСЛАНИЕМ '{message}'")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ РЕПОСТЕ: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

async def get_poll_info(session, token, owner_id, poll_id, is_board, proxy): 
    params = {
        'access_token': token,
        'v': '5.131',
        'owner_id': owner_id,
        'poll_id': poll_id
    }
    if is_board == 1:
        params['is_board'] = 1

    try:
        async with session.get(f"https://api.vk.com/method/polls.getById", params=params, proxy=proxy) as response:
            return await response.json()

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")
        return None

async def vote_action(session, email, token, owner_id, poll_id, answer_id, answer_index, is_board, action, url, proxy): 
    params = {
        'access_token': token,
        'v': '5.131',
        'owner_id': owner_id,
        'poll_id': poll_id,
        'answer_ids': answer_id,
        'is_board': is_board
    }
    method = f"polls.{action}Vote"

    try:
        async with session.get(f"https://api.vk.com/method/{method}", params=params, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                action_text = "ОТДАЛ ГОЛОС ЗА" if action == "add" else "УБРАЛ ГОЛОС С"
                if action == "add":
                    print_white(f"ЛОГИН {email} {action_text} ВАРИАНТ(А) {answer_index} В ОПРОСЕ {url}")
                else:
                    print_white(f"ЛОГИН {email} {action_text} ОПРОСА {url}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ГОЛОСОВАНИИ В ОПРОСЕ: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

async def subscribe_action(session, email, token, user_id, action, proxy): 
    params = {
        'access_token': token,
        'v': '5.131',
        'user_id': user_id
    }

    method = "friends.add" if action == "subscribe" else "friends.delete"

    try:
        async with session.get(f"https://api.vk.com/method/{method}", params=params, proxy=proxy) as response: 
            result = await response.json()
            if 'error' not in result:
                action_text = "ПОДПИСАЛСЯ НА" if action == "subscribe" else "ОТПИСАЛСЯ ОТ"
                print_white(f"ЛОГИН {email} {action_text} {user_id}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ПОДПИСКЕ НА ПОЛЬЗОВАТЕЛЯ: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")


async def subscribe_group_action(session, email, token, group_id, action, proxy):  
    params = {
        'access_token': token,
        'v': '5.131',
        'group_id': group_id
    }

    method = "groups.join" if action == "subscribe" else "groups.leave"

    try:
        async with session.get(f"https://api.vk.com/method/{method}", params=params, proxy=proxy) as response:  
            result = await response.json()
            if 'error' not in result:
                action_text = "ПОДПИСАЛСЯ НА ГРУППУ" if action == "subscribe" else "ОТПИСАЛСЯ ОТ ГРУППЫ"
                print_white(f"ЛОГИН {email} {action_text} {group_id}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ПОДПИСКЕ НА ГРУППУ: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

def determine_object_type_and_id(url):
    patterns = {
        'video': r'video(-?\d+_\d+)',
        'photo': r'photo(-?\d+_\d+)',
        'post': r'wall(-?\d+_\d+)',
        'comment': r'wall(-?\d+_\d+)_r(\d+)',
        'product': r'market/product/(\d+_\d+)',
        'topic_comment': r'topic(-?\d+_\d+)_comment(\d+)',
        'video_comment': r'video(-?\d+_\d+)_comment(\d+)',
        'photo_comment': r'photo(-?\d+_\d+)_comment(\d+)',
    }
    for object_type, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            if object_type in ['comment', 'topic_comment', 'video_comment', 'photo_comment']:
                return object_type, f"{match.group(1)}_{match.group(2)}"
            return object_type, match.group(1)
    return None, None

async def parsing_objects(session, url, action, proxy):
    with open(TOKENS_FILE, 'r') as f:
        tokens = json.load(f)['user_tokens']

    object_type, object_id = determine_object_type_and_id(url)
    if not object_type or not object_id:
        logging.error("ОШИБОЧКА: НЕВЕРНЫЙ ФОРМАТ URL")
        return

    try:
        tasks = [like_action(session, email, token, object_id.split('_')[0], object_id.split('_')[1], object_type, action, url, proxy) for email, token in tokens.items()]
        await asyncio.gather(*tasks)

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

async def parsing_objectsReposts(session, url, message, group_id, proxy):
    with open(TOKENS_FILE, 'r') as f:
        tokens = json.load(f)['user_tokens']

    parsed_url = urlparse(url)

    match = re.search(r"/(wall|photo|video)(-?\d+)_(\d+)", parsed_url.path)
    if match:
        object_type, owner_id, object_id = match.groups()
    else:
        query_params = parse_qs(parsed_url.query)
        if 'z' in query_params:
            z_value = query_params['z'][0]
            match = re.search(r"(photo|video)(-?\d+)_(\d+)", z_value)
            if match:
                object_type, owner_id, object_id = match.groups()
            else:
                logging.error("ФОРМАТ НЕВЕРНЫЙ")
                return
        else:
            logging.error("ФОРМАТ НЕВЕРНЫЙ")
            return

    try:
        tasks = [repost_action(session, email, token, object_type, owner_id + "_" + object_id, message, group_id, proxy) for email, token in tokens.items()]
        await asyncio.gather(*tasks)
    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

async def parsing_objectsPolls(session, owner_id, poll_id, action, url, answer_index, is_board, proxy):
    with open(TOKENS_FILE, 'r') as f:
        tokens = json.load(f)['user_tokens']

    try:
        if action == "add":
            poll_info = await get_poll_info(session, list(tokens.values())[0], owner_id, poll_id, is_board, proxy)
            answers = poll_info['response']['answers']
            if 0 <= int(answer_index) < len(answers):
                answer_id = answers[int(answer_index) - 1]['id']
                tasks = [vote_action(session, email, token, owner_id, poll_id, answer_id, answer_index, is_board, action, url, proxy) for email, token in tokens.items()]
                await asyncio.gather(*tasks)
            else:
                print_white("НЕВЕРНЫЙ НОМЕР ВАРИАНТА ДЛЯ ГОЛОСОВАНИЯ")
        else:
            tasks = [vote_action(session, email, token, owner_id, poll_id, '', answer_index, is_board, action, url, proxy) for email, token in tokens.items()]
            await asyncio.gather(*tasks)

    except aiohttp.ClientError as e:
        logging.error(f"ОПАНА ОШИБОЧКА: {e}")

async def extract_id_from_url(url):
    if url.startswith('id'):
        return url[2:], 'user'
    elif url.startswith('public'):
        return url[6:], 'group'
    elif url.startswith('club'):
        return url[4:], 'group'
    elif url.isdigit():
        return url, 'user'
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    
    if path.startswith('id'):
        return path[2:], 'user'
    elif path.startswith('public'):
        return path[6:], 'group'
    elif path.isdigit():
        return path, 'user'
    elif path.startswith('club'):
        return path[4:], 'group'
    else:
        logging.error("НЕ УДАЛОСЬ ИЗВЛЕЧЬ ID ИЗ ССЫЛКИ, ИСПОЛЬЗУЙ ЧИСТУЮ АЙДИ ССЫЛКУ")
        return None, None

async def mass_action(url, action):
    headers = reg.load_headers()
    proxy = reg.load_proxy()
    with open(TOKENS_FILE, 'r') as f:
        tokens = json.load(f)['user_tokens']

    id, id_type = await extract_id_from_url(url)
    if not id:
        return

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        tasks = []
        for email, token in tokens.items():
            if id_type == 'user':
                tasks.append(subscribe_action(session, email, token, id, action, proxy))
            elif id_type == 'group':
                tasks.append(subscribe_group_action(session, email, token, id, action, proxy))
        await asyncio.gather(*tasks)

async def set_status(session, login, token, status, proxy):
    url = 'https://api.vk.com/method/status.set'
    params = {
        'access_token': token,
        'v': '5.131',
        'text': status
    }
    async with session.post(url, params=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' in result:
            print_white(f"ОШИБОЧКА ДЛЯ ЛОГИНА {login}: {result['error']['error_msg']}")
        else:
            print_white(f"НОВЕНЬКИЙ СТАТУС {status} УСПЕШНО УСТАНОВЛЕН ДЛЯ ЛОГИНА {login}")

async def delete_wall_posts(session, login, token, proxy):
    url_wall_get = 'https://api.vk.com/method/wall.get'
    url_wall_delete = 'https://api.vk.com/method/wall.delete'

    offset = 0

    try:
        while True:
            params_wall_get = {
                'access_token': token,
                'v': '5.131',
                'count': 100,
                'offset': offset
            }
            async with session.get(url_wall_get, params=params_wall_get, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data['response']['items']
                    if not posts:
                        break

                    for post in posts:
                        params_wall_delete = {
                            'access_token': token,
                            'v': '5.131',
                            'post_id': post['id']
                        }
                        try:
                            async with session.post(url_wall_delete, params=params_wall_delete, proxy=proxy) as response:
                                result = await response.json()
                                if 'error' not in result:
                                    print_white(f"УДАЛЕН ПОСТ С ID: {post['id']} НА ЛОГИНЕ {login}")
                                else:
                                    error_code = result['error']['error_code']
                                    error_msg = result['error']['error_msg']
                                    logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ПОСТА: {error_code} - {error_msg}")
                                await asyncio.sleep(0.33)

                        except aiohttp.ClientError as e:
                            logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ПОСТА С ID: {post['id']} НА ЛОГИНЕ {login}: {e}")

                    offset += 100
                await asyncio.sleep(0.33)

        print_white(f"НА ЛОГИНЕ {login} БЫЛА ПОЛНОСТЬЮ ОЧИЩЕНА СТЕНА ПОЛЬЗОВАТЕЛЯ")

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОСТОВ НА ЛОГИНЕ {login}: {e}")

async def delete_all_friends(session, login, token, proxy):
    url_friends_get = 'https://api.vk.com/method/friends.get'
    url_friends_delete = 'https://api.vk.com/method/friends.delete'

    params_friends_get = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_friends_get, params=params_friends_get, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                friends = data['response']['items']

        for friend_id in friends:
            params_friends_delete = {
                'access_token': token,
                'v': '5.131',
                'user_id': friend_id
            }
            try:
                async with session.post(url_friends_delete, params=params_friends_delete, proxy=proxy) as response:
                    result = await response.json()
                    if 'error' not in result:
                        print_white(f"УДАЛЕН ДРУГ С ID: {friend_id} НА ЛОГИНЕ {login}")
                    else:
                        error_code = result['error']['error_code']
                        error_msg = result['error']['error_msg']
                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ДРУГА: {error_code} - {error_msg}")
                    await asyncio.sleep(0.33)

            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ДРУГА С ID: {friend_id} НА ЛОГИНЕ {login}: {e}")

        print_white(f"НА ЛОГИНЕ {login} БЫЛИ УДАЛЕНЫ ВСЕ ДРУЗЬЯ")

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СПИСКА ДРУЗЕЙ НА ЛОГИНЕ {login}: {e}")

async def delete_all_photos(session, login, token, proxy):
    url_users_get = 'https://api.vk.com/method/users.get'
    url_photos_getAlbums = 'https://api.vk.com/method/photos.getAlbums'
    url_photos_get = 'https://api.vk.com/method/photos.get'
    url_photos_delete = 'https://api.vk.com/method/photos.delete'

    params_users_get = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_users_get, params=params_users_get, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                user_id = data['response'][0]['id']

        params_photos_getAlbums = {
            'access_token': token,
            'v': '5.131'
        }

        async with session.get(url_photos_getAlbums, params=params_photos_getAlbums, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                albums = data['response']['items']

        for album in albums:
            params_photos_get = {
                'access_token': token,
                'v': '5.131',
                'album_id': album['id']
            }
            async with session.get(url_photos_get, params=params_photos_get, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    photos = data['response']['items']

            for photo in photos:
                params_photos_delete = {
                    'access_token': token,
                    'v': '5.131',
                    'photo_id': photo['id']
                }
                try:
                    async with session.post(url_photos_delete, params=params_photos_delete, proxy=proxy) as response:
                        result = await response.json()
                        if 'error' not in result:
                            print_white(f"УДАЛЕНА ФОТОГРАФИЯ С ID: {photo['id']} ИЗ АЛЬБОМА С ID: {album['id']} НА ЛОГИНЕ {login}")
                        else:
                            error_code = result['error']['error_code']
                            error_msg = result['error']['error_msg']
                            logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ФОТОГРАФИИ: {error_code} - {error_msg}")
                        await asyncio.sleep(0.33)
  
                except aiohttp.ClientError as e:
                    logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ФОТОГРАФИИ С ID: {photo['id']} НА ЛОГИНЕ {login}: {e}")

        params_photos_get_profile = {
            'access_token': token,
            'v': '5.131',
            'owner_id': user_id,
            'album_id': 'profile'
        }

        params_photos_get_wall = {
            'access_token': token,
            'v': '5.131',
            'owner_id': user_id,
            'album_id': 'wall'
        }

        async with session.get(url_photos_get, params=params_photos_get_profile, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                profile_photos = data['response']['items']

        async with session.get(url_photos_get, params=params_photos_get_wall, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                wall_photos = data['response']['items']

        all_photos = profile_photos + wall_photos
        for photo in all_photos:
            params_photos_delete = {
                'access_token': token,
                'v': '5.131',
                'photo_id': photo['id']
            }
            try:
                async with session.post(url_photos_delete, params=params_photos_delete, proxy=proxy) as response:
                    if response.status == 200:
                        print_white(f"УДАЛЕНА ФОТОГРАФИЯ С ID: {photo['id']} ИЗ АЛЬБОМА 'Фото профиля' или 'Фото на стене'' НА ЛОГИНЕ {login}")
                    await asyncio.sleep(0.33)
    
            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ФОТОГРАФИИ С ID: {photo['id']} НА ЛОГИНЕ {login}: {e}")

        print_white(f"НА ЛОГИНЕ {login} БЫЛИ УДАЛЕНЫ ВСЕ ФОТОГРАФИИ")

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ ПОЛУЧЕНИИ ФОТОГРАФИЙ НА ЛОГИНЕ {login}: {e}")

async def delete_all_messenger(session, login, token, proxy):
    url_get_conversations = 'https://api.vk.com/method/messages.getConversations'
    url_delete_conversation = 'https://api.vk.com/method/messages.deleteConversation'

    offset = 0
    count = 200

    try:
        while True:
            params_get_conversations = {
                'access_token': token,
                'v': '5.131',
                'offset': offset,
                'count': count,
                'extended': 1
            }
            async with session.get(url_get_conversations, params=params_get_conversations, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    dialogs = data['response']['items']
                    await asyncio.sleep(0.33)
                    if not dialogs:
                        break

                    for dialog in dialogs:
                        peer_type = dialog['conversation']['peer']['type']
                        if peer_type == 'chat':
                            peer_id = 2000000000 + dialog['conversation']['peer']['local_id']
                        elif peer_type in ['user', 'group']:
                            peer_id = dialog['conversation']['peer']['id']
                        else:
                            continue

                        params_delete_conversation = {
                            'access_token': token,
                            'v': '5.131',
                            'peer_id': peer_id
                        }
                        try:
                            async with session.post(url_delete_conversation, params=params_delete_conversation, proxy=proxy) as response:
                                result = await response.json()
                                if 'error' not in result:
                                    print_white(f"УДАЛЕН ДИАЛОГ С ID: {peer_id} НА ЛОГИНЕ {login}")
                                else:
                                    error_code = result['error']['error_code']
                                    error_msg = result['error']['error_msg']
                                    logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ДИАЛОГА: {error_code} - {error_msg}")
                                await asyncio.sleep(0.33)

                        except aiohttp.ClientError as e:
                            logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ДИАЛОГА С ID: {peer_id} НА ЛОГИНЕ {login}: {e}")

                    offset += count

        print_white(f"НА ЛОГИНЕ {login} БЫЛИ УДАЛЕНЫ ВСЕ ДИАЛОГИ")
    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ДИАЛОГОВ НА ЛОГИНЕ {login}: {e}")

async def delete_all_groups_and_subscriptions(session, login, token, proxy):
    url_users_get = 'https://api.vk.com/method/users.get'
    url_groups_get = 'https://api.vk.com/method/groups.get'
    url_groups_leave = 'https://api.vk.com/method/groups.leave'
    url_users_getSubscriptions = 'https://api.vk.com/method/users.getSubscriptions'
    url_friends_delete = 'https://api.vk.com/method/friends.delete'

    params_users_get = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_users_get, params=params_users_get, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                user_id = data['response'][0]['id']

        top_groups = await reg.get_user_groups(session, user_id, token, proxy)

        for group in top_groups:
            params_groups_leave = {
                'access_token': token,
                'v': '5.131',
                'group_id': group['id']
            }
            try:
                async with session.post(url_groups_leave, params=params_groups_leave, proxy=proxy) as response:
                    result = await response.json()
                    if 'error' not in result:
                        print_white(f"УДАЛЕНА ПОДПИСКА НА ГРУППУ С ID: {group['id']} НА ЛОГИНЕ {login}")
                    else:
                        error_code = result['error']['error_code']
                        error_msg = result['error']['error_msg']
                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ПОДПИСКИ НА ГРУППУ: {error_code} - {error_msg}")
                    await asyncio.sleep(0.33)
 
            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ПОДПИСКИ НА ГРУППУ ID: {group['id']} НА ЛОГИНЕ {login}: {e}")

        subscriptions = await reg.get_subscriptions(session, token, user_id, proxy)
        users = [user for user in subscriptions]

        for user in users:
            params_friends_delete = {
                'access_token': token,
                'v': '5.131',
                'user_id': user['id']
            }
            try:
                async with session.post(url_friends_delete, params=params_friends_delete, proxy=proxy) as response:
                    result = await response.json()
                    if 'error' not in result:
                        print_white(f"УДАЛЕНА ПОДПИСКА НА ПОЛЬЗОВАТЕЛЯ С ID: {user['id']} НА ЛОГИНЕ {login}")
                    else:
                        error_code = result['error']['error_code']
                        error_msg = result['error']['error_msg']
                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ПОДПИСКИ НА ПОЛЬЗОВАТЕЛЯ: {error_code} - {error_msg}")
                    await asyncio.sleep(0.33)

            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ПОДПИСКИ НА ПОЛЬЗОВАТЕЛЯ С ID: {user['id']} НА ЛОГИНЕ {login}: {e}")

        print_white(f"НА ЛОГИНЕ {login} БЫЛИ УДАЛЕНЫ ВСЕ ПОДПИСКИ НА ГРУППЫ И ПОЛЬЗОВАТЕЛЕЙ")

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОДПИСОК НА ЛОГИНЕ {login}: {e}")

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

def extract_post_id(post_url):
    match = re.search(r'wall(-?\d+_\d+)', post_url)
    if match:
        return match.group(1)
    else:
        logging.error("НЕПРАВИЛЬНЫЙ POST URL")
        raise ValueError("НЕПРАВИЛЬНЫЙ POST URL")

def extract_user_id(link):
    match = re.search(r'id(\d+)', link)
    if match:
        return int(match.group(1))
    else:
        logging.error(f"НЕПРАВИЛЬНЫЙ ФОРМАТ ССЫЛКИ: {link}")
        raise ValueError(f"НЕПРАВИЛЬНЫЙ ФОРМАТ ССЫЛКИ: {link}")

def extract_group_id(link):
    match = re.search(r'(club|public)(\d+)', link)
    if match:
        return int(match.group(2))
    else:
        logging.error(f"НЕПРАВИЛЬНЫЙ ФОРМАТ ССЫЛКИ: {link}")
        raise ValueError(f"НЕПРАВИЛЬНЫЙ ФОРМАТ ССЫЛКИ: {link}")

def extract_video_id(link):
    match = re.search(r'video(\d+)_(\d+)', link)
    if match:
        owner_id = int(match.group(1))
        video_id = int(match.group(2))
        return owner_id, video_id 
    else:
        logging.error(f"НЕПРАВИЛЬНЫЙ ФОРМАТ ССЫЛКИ: {link}")
        raise ValueError(f"НЕПРАВИЛЬНЫЙ ФОРМАТ ССЫЛКИ: {link}")

async def upload_avatar(session, token, user_id, avatar_path, proxy):
    url = 'https://api.vk.com/method/photos.getOwnerPhotoUploadServer'
    params = {
        'access_token': token,
        'v': '5.131',
        'owner_id': user_id
    }
    async with session.get(url, params=params, proxy=proxy) as response:
        data = await response.json()
        upload_url = data['response']['upload_url']

    with open(avatar_path, 'rb') as avatar_file:
        data = {'photo': avatar_file}
        async with session.post(upload_url, data=data, proxy=proxy) as response:
            result = await response.json()

    url = 'https://api.vk.com/method/photos.save_owner_photo'
    params = {
        'access_token': token,
        'v': '5.131',
        **result
    }
    async with session.post(url, params=params, proxy=proxy) as response:
        await response.json()

async def add_friends(session, token, friends_list, proxy):
    for friend in friends_list:
        user_id = extract_user_id(friend)
        try:
            url = 'https://api.vk.com/method/friends.add'
            params = {
                'access_token': token,
                'v': '5.131',
                'user_id': user_id
            }
            async with session.post(url, params=params, proxy=proxy) as response:
                data = await response.json()
                if 'error' in data:
                    error_code = data['error']['error_code']
                    if error_code == 175:
                        logging.error(f"НЕ МОЖЕМ ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ С ID: {user_id} В ДРУЗЬЯ: blacklist")
                    elif error_code == 177:
                        logging.error(f"НЕ МОЖЕМ ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ С ID: {user_id} В ДРУЗЬЯ: user not found")
                    else:
                        logging.error(f"ОШИБКА ПРИ ДОБАВЛЕНИИ В ДРУЗЬЯ: {data['error']}")
                await asyncio.sleep(0.33)
                    
        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ДОБАВЛЕНИИ В ДРУЗЬЯ: {e}")

async def join_groups(session, token, groups_list, proxy):
    for group in groups_list:
        group_id = extract_group_id(group)
        try:
            url = 'https://api.vk.com/method/groups.join'
            params = {
                'access_token': token,
                'v': '5.131',
                'group_id': group_id
            }
            async with session.post(url, params=params, proxy=proxy) as response:
                data = await response.json()
                if 'error' in data:
                    error_code = data['error']['error_code']
                    if error_code == 15:
                        logging.error(f"НЕТ ДОСТУПА К ГРУППЕ С ID: {group_id}: {data['error']}")
                    else:
                        logging.error(f"ОШИБКА ПРИ ВСТУПЛЕНИИ В ГРУППУ: {data['error']}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ВСТУПЛЕНИИ В ГРУППУ: {e}")

async def copy_posts(session, token, posts_list, proxy):
    for post_url in posts_list:
        post_id = extract_post_id(post_url)
        try:
            url = 'https://api.vk.com/method/wall.getById'
            params = {
                'access_token': token,
                'v': '5.131',
                'posts': post_id
            }
            async with session.get(url, params=params, proxy=proxy) as response:
                post_data = await response.json()
                if 'error' in post_data:
                    logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОСТА: {post_data['error']}")
                    continue
                await asyncio.sleep(0.33)

            post = post_data['response']['items'][0]
            attachments = post.get('attachments', [])
            new_attachments = ','.join([f"{att['type']}{att[att['type']]['owner_id']}_{att[att['type']]['id']}" for att in attachments])

            url = 'https://api.vk.com/method/wall.post'
            params = {
                'access_token': token,
                'v': '5.131',
                'message': post.get('text', ''),
                'attachments': new_attachments
            }
            async with session.post(url, params=params, proxy=proxy) as response:
                data = await response.json()
                if 'error' in data:
                    logging.error(f"ОШИБКА ПРИ КОПИРОВАНИИ ПОСТА: {data['error']}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ КОПИРОВАНИИ ПОСТА: {e}")

async def add_subscriptions(session, token, subscriptions_list, proxy):
    for subscription in subscriptions_list:
        try:
            if 'id' in subscription:
                user_id = extract_user_id(subscription)
                url = 'https://api.vk.com/method/friends.add'
                params = {
                    'access_token': token,
                    'v': '5.131',
                    'user_id': user_id
                }
            elif 'club' in subscription or 'public' in subscription:
                group_id = extract_group_id(subscription)
                url = 'https://api.vk.com/method/groups.join'
                params = {
                    'access_token': token,
                    'v': '5.131',
                    'group_id': group_id
                }
            else:
                print_white(f"НЕИЗВЕСТНЫЙ ТИП ССЫЛКИ: {subscription}")
                continue

            async with session.post(url, params=params, proxy=proxy) as response:
                data = await response.json()
                if 'error' in data:
                    logging.error(f"ОШИБКА ПРИ ПОДПИСКЕ: {data['error']}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОДПИСКЕ: {e}")

async def add_videos(session, token, videos_list, proxy):
    for video_url in videos_list:
        try:
            owner_id, video_id = extract_video_id(video_url)
            url = 'https://api.vk.com/method/video.add'
            params = {
                'access_token': token,
                'v': '5.131',
                'owner_id': owner_id,
                'video_id': video_id
            }
            async with session.post(url, params=params, proxy=proxy) as response:
                data = await response.json()
                if 'error' in data:
                    logging.error(f"ОШИБКА ПРИ ДОБАВЛЕНИИ ВИДЕО: {data['error']}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБОЧКА ПРИ ДОБАВЛЕНИИ ВИДЕО: {e}")

async def clon(user_name, token):
    user_folder = os.path.join('parser', 'users', user_name)
    headers = reg.load_headers()
    proxy = reg.load_proxy()

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        url = 'https://api.vk.com/method/users.get'
        params = {
            'access_token': token,
            'v': '5.131'
        }
        async with session.get(url, params=params, proxy=proxy) as response:
            user_data = await response.json()
        user_id = user_data['response'][0]['id']

        avatar_path = os.path.join(user_folder, 'avatar.jpg')
        await upload_avatar(session, token, user_id, avatar_path, proxy)

        friends_list = read_file(os.path.join(user_folder, 'friends', 'friends.txt'))
        await add_friends(session, token, friends_list, proxy)

        groups_list = read_file(os.path.join(user_folder, 'groups', 'groups.txt'))
        await join_groups(session, token, groups_list, proxy)

        posts_list = read_file(os.path.join(user_folder, 'posts', 'posts.txt'))
        await copy_posts(session, token, posts_list, proxy)

        subscriptions_list = read_file(os.path.join(user_folder, 'subscriptions', 'subscriptions.txt'))
        await add_subscriptions(session, token, subscriptions_list, proxy)

        videos_list = read_file(os.path.join(user_folder, 'videos', 'videos.txt'))
        await add_videos(session, token, videos_list, proxy)

async def ban_user(session, user_id, token, login, user_name, proxy):
    url_account_ban = 'https://api.vk.com/method/account.ban'
    try:
        params_account_ban = {
            'owner_id': user_id,
            'access_token': token,
            'v': '5.131'
        }
        async with session.post(url_account_ban, params=params_account_ban, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                print_white(f"ПОЛЬЗОВАТЕЛЬ {user_name} УСПЕШНО ДОБАВЛЕН В ЧЕРНЫЙ СПИСОК НА ЛОГИНЕ {login}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ДОБАВЛЕНИИ ПОЛЬЗОВАТЕЛЯ В ЧЕРНЫЙ СПИСОК: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        print_white(f"ОШИБОЧКА ПРИ ДОБАВЛЕНИИ ПОЛЬЗОВАТЕЛЯ {user_name} В ЧЕРНЫЙ СПИСОК НА ЛОГИНЕ {login}: {e}")

async def unban_user(session, user_id, token, login, user_name, proxy):
    url_account_unban = 'https://api.vk.com/method/account.unban'
    try:
        params_account_unban = {
            'owner_id': user_id,
            'access_token': token,
            'v': '5.131'
        }
        async with session.post(url_account_unban, params=params_account_unban, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                print_white(f"ПОЛЬЗОВАТЕЛЬ {user_name} УСПЕШНО УДАЛЕН ИЗ ЧЕРНОГО СПИСКА НА ЛОГИНЕ {login}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ПОЛЬЗОВАТЕЛЯ ИЗ ЧЕРНОГО СПИСКА: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        print_white(f"ОШИБОЧКА ПРИ УДАЛЕНИИ ПОЛЬЗОВАТЕЛЯ {user_name} ИЗ ЧЕРНОГО СПИСКА НА ЛОГИНЕ {login}: {e}")
        
async def ban_group(session, group_id, token, login, group_name, proxy):
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

async def set_name(session, login, token, name_file, proxy):
    first_name, last_name = reg.read_names(name_file)
    url = 'https://api.vk.com/method/account.saveProfileInfo'
    params = {
        'access_token': token,
        'v': '5.131',
        'first_name': first_name,
        'last_name': last_name
    }
    async with session.post(url, params=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' in result:
            print_white(f"ОШИБКА ДЛЯ ЛОГИНА {login} ПРИ СМЕНЕ НИКНЕЙМА: {result['error']['error_msg']}")
        else:
            if result['response']['changed'] == 0:
                reason = result['response']['name_request']['lang']
                print_white(f"НЕ УДАЛОСЬ ИЗМЕНИТЬ НИКНЕЙМ ДЛЯ ЛОГИНА {login} ОПИСАНИЕ ПРИЧИНЫ: {reason}")
            else:
                print_white(f"НОВЫЙ НИКНЕЙМ {first_name} {last_name} УСПЕШНО УСТАНОВЛЕН ДЛЯ ЛОГИНА {login}")
