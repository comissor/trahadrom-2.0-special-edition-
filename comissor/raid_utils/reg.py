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
from selenium.webdriver.chrome.options import Options
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
user_cache = {}
group_cache = {}
conversation_cache = {}
subscription_cache = {}
video_cache = {}

def input_white(prompt):
    print("\033[97m" + prompt + "\033[1m", end="")
    return input()

def print_white(text):
    print(f"{WHITE}{BOLD}{text}{RESET}")

async def get_token_permissions_user(session, login, token, proxy):
    url = 'https://api.vk.com/method/account.getAppPermissions'
    params = {
        'access_token': token,
        'v': '5.131'
    }

    async with session.get(url, params=params, proxy=proxy) as response:
        if response.status == 200:
            result = await response.json()
            if 'error' in result:
                print_white(f"ОШИБКА ПРИ ПРОВЕРКЕ ПРАВ ТОКЕНА {token}: {result['error']['error_msg']}")
            else:
                permissions = result['response']
                print_white(f"*ЛОГИН* - {login}")
                print_white(f"*ТОКЕН ЮЗЕРА* - {token}")
                print_white(f"*БИТОВАЯ МАСКА ЮЗЕРА: {permissions}")
                interpret_permissions_user(permissions)

async def get_token_permissions_community(session, group_id, token, proxy):
    url = 'https://api.vk.com/method/groups.getTokenPermissions'
    params = {
        'access_token': token,
        'v': '5.131'
    }

    async with session.get(url, params=params, proxy=proxy) as response:
        if response.status == 200:
            result = await response.json()
            if 'error' in result:
                print_white(f"ОШИБКА ПРИ ПРОВЕРКЕ ПРАВ ТОКЕНА {token}: {result['error']['error_msg']}")
            else:
                mask = result['response']['mask']
                permissions = result['response']
                print_white(f"*СООБЩЕСТВО* - {group_id}")
                print_white(f"*ТОКЕН СООБЩЕСТВА* - {token}")
                print_white(f"*БИТОВАЯ МАСКА СООБЩЕСТВА*: {mask}")
                interpret_community_permissions(permissions)

def interpret_permissions_user(permissions):
    rights = {
        1: 'notify (ДОСТУП К УВЕДОМЛЕНИЯМ)',
        2: 'friends (ДОСТУП К ДРУЗЬЯМ)',
        4: 'photos (ДОСТУП К ФОТОГРАФИЯМ)',
        8: 'audio (ДОСТУП К АУДИОЗАПИСЯМ)',
        16: 'video (ДОСТУП К ВИДЕОЗАПИСЯМ)',
        64: 'stories (ДОСТУП к ИСТОРИЯМ)',
        128: 'pages (ДОСТУП К СТРАНИЦАМ)',
        256: 'menu (ДОБАВЛЕНИЕ ССЫЛКИ НА ПРИЛОЖЕНИЕ В МЕНЮ СЛЕВА)',
        1024: 'status (ДОСТУП К СТАТУСУ)',
        2048: 'notes (ДОСТУП К ЗАМЕТКАМ)',
        4096: 'messages (ДОСТУП К СООБЩЕНИЯМ)',
        8192: 'wall (ДОСТУП К СТЕНЕ)',
        32768: 'ads (ДОСТУП К РЕКЛАМНОМУ API)',
        65536: 'offline (РАБОТА В ОФФЛАЙН-РЕЖИМЕ)',
        131072: 'docs (ДОСТУП К ДОКУМЕНТАМ)',
        262144: 'groups (ДОСТУП К ГРУППАМ)',
        524288: 'notifications (ДОСТУП К ОПОВЕЩЕНИЯМ)',
        1048576: 'stats (ДОСТУП К СТАТИСТИКЕ)',
        4194304: 'email (ДОСТУП К EMAIL)',
        134217728: 'market (ДОСТУП К ТОВАРАМ)',
        268435456: 'phone_number (ДОСТУП К НОМЕРУ ТЕЛЕФОНА)'
    }
    
    print_white("*ПРАВА ТОКЕНА ЮЗЕРА*:")
    for key, value in rights.items():
        has_permission = permissions & key
        print_white(f"- {value}: {'True' if has_permission else 'False'}")

def interpret_community_permissions(permissions):
    rights = {
        1: 'stories (ДОСТУП К ИСТОРИЯМ)',
        4: 'photos (ДОСТУП К ФОТОГРАФИЯМ)',
        64: 'app_widget (ДОСТУП К ВИДЖЕТАМ ПРИЛОЖЕНИЙ СООБЩЕСТВА)',
        4096: 'messages (ДОСТУП К СООБЩЕНИЯМ СООБЩЕСТВА)',
        131072: 'docs (ДОСТУП К ДОКУМЕНТАМ)',
        262144: 'manage (ДОСТУП К АДМИНИСТРИРОВАНИЮ СООБЩЕСТВА)',
    }

    print_white("*ПРАВА ТОКЕНА СООБЩЕСТВА*:")
    for key, value in rights.items():
        has_permission = permissions['mask'] & key
        print_white(f"- {value}: {'True' if has_permission else 'False'}")

def load_theme_state():
    with open(TOKENS_FILE) as file:
        data = json.load(file)
        return data.get("Theme", {}).get("state", "False") == "True"

def load_proxy():
    with open('base/proxy.txt', 'r') as file:
        proxy = file.readline().strip()
    return proxy if proxy else ''

def load_headers():
    with open('base/headers.txt', 'r') as file:
        headers = file.read()
    return json.loads(headers)

def load_manager_state():
    with open(TOKENS_FILE) as file:
        data = json.load(file)
        return data.get("Manager", {}).get("state", "False") == "True"

def extract_comment_id(url):
    match = re.search(r'wall(-?\d+)_\d+_r(\d+)', url)
    if match:
        owner_id = match.group(1)
        comment_id = match.group(2)
        return owner_id, comment_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return None, None

def extract_owner_post_id(url):
    match = re.search(r'wall(-?\d+)_\d+_r(\d+)', url)
    if match:
        owner_id = match.group(1)
        post_id = match.group(2)
        return owner_id, post_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return None, None

def extract_album_info(url):
    match = re.search(r'album(-?\d+)_(\d+)', url)
    if match:
        group_id, album_id = match.groups()
        return group_id, album_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return None, None

def extract_video_id(url):
    match = re.search(r'video(-?\d+_\d+)', url)
    if match:
        video_id = match.group(1)
        return video_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return

def extract_owner_id(url):
    match = re.search(r'video(-?\d+)_', url)
    if match:
        owner_id = int(match.group(1))
        return owner_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return 

def extract_photo_id(url):
    match = re.search(r'photo(-?\d+_\d+)', url)
    if match:
        photo_id = match.group(1)
        return photo_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return

def extract_market_item_id(url):
    match = re.search(r'market/product/[^/]+-(\d+)-(\d+)', url)
    if match:
        owner_id = match.group(1)
        item_id = match.group(2)
        return owner_id, item_id
    else:
        logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
        return None, None

def extract_market_comment_id(url):
    match = re.search(r'market(-?\d+_\d+)_r(\d+)', url)
    if match:
        owner_id = match.group(1)
        comment_id = match.group(2)
        return owner_id, comment_id
    else:
        match = re.search(r'market_comment(-?\d+_\d+)', url)
        if match:
            owner_id, comment_id = match.group(1).split('_')
            return owner_id, comment_id
        else:
            logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
            return None, None

def extract_photo_comment_id(url):
    match = re.search(r'photo(-?\d+_\d+)_r(\d+)', url)
    if match:
        owner_id = match.group(1)
        comment_id = match.group(2)
        return owner_id, comment_id
    else:
        match = re.search(r'photo_comment(-?\d+_\d+)', url)
        if match:
            owner_id, comment_id = match.group(1).split('_')
            return owner_id, comment_id
        else:
            logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
            return None, None

def extract_video_comment_id(url):
    match = re.search(r'video\?z=video(-?\d+_\d+)%2Fcomment(-?\d+_\d+)', url)
    if match:
        owner_id = match.group(1)
        comment_id = match.group(2)
        return owner_id, comment_id
    else:
        match = re.search(r'video_comment(-?\d+_\d+)', url)
        if match:
            owner_id, comment_id = match.group(1).split('_')
            return owner_id, comment_id
        else:
            logging.error("ФОРМАТ ССЫЛКИ НЕВЕРНЫЙ")
            return None, None

def extract_post_id(input_str):
    if input_str.startswith("https://vk.com/") or input_str.startswith("vk.com/"):
        post_id = input_str.split('wall')[-1]  
    elif input_str.startswith("wall"):
        post_id = input_str.split('wall')[-1] 
    else:
        post_id = input_str
    
    if '_' in post_id:  
        post_id = post_id.split('_')[-1]
    
    return post_id

def extract_topic_id(input_str):
    if input_str.startswith("https://vk.com/") or input_str.startswith("vk.com/"):
        parts = input_str.split('/')[-1].split('_')
        if len(parts) == 2:
            return parts[1] 
        else:
            return 
    elif input_str.startswith("topic-"):
        parts = input_str.split('-')[1].split('_')
        if len(parts) == 2:
            return parts[1]
        else:
            return
    else:
        return

def extract_poll_owner_ids(input_str):
    if input_str.startswith("https://vk.com/") or input_str.startswith("vk.com/"):
        parts = input_str.split('/')[-1]
        if '?w=poll' in parts:
            parts = parts.split('?w=poll')[1]
        elif '?w=board_poll-' in parts:
            parts = parts.split('?w=board_poll')[1]
        elif 'poll' in parts:
            parts = parts.split('poll')[1]
        elif 'board_poll-' in parts:
            parts = parts.split('board_poll')[1]
        owner_id, poll_id = parts.split('_')
        return owner_id, poll_id
    elif input_str.startswith("poll"):
        owner_id, poll_id = input_str.replace("poll", "").split('_')
        return owner_id, poll_id
    elif input_str.startswith("topic-"):
        parts = input_str.split('?w=board_poll')[1]
        owner_id, poll_id = parts.split('_')
        return owner_id, poll_id
    elif input_str.startswith("board_poll"):
        owner_id, poll_id = input_str.replace("board_poll", "").split('_')
        return owner_id, poll_id
    else:
        return input_str

def extract_group_id(input_str):
    if input_str.startswith("https://vk.com/") or input_str.startswith("vk.com/"):
        parts = input_str.split('/')[-1].split('_')
        if len(parts) == 2:
            return parts[0].replace("wall", "").replace("-", "").replace("topic", "")
        else:
            return input_str.split('/')[-1].replace("club", "").replace("public", "").replace("event", "")
    elif input_str.startswith("club") or input_str.startswith("public") or input_str.startswith("event"):
        return input_str.replace("club", "").replace("public", "").replace("event", "")
    elif input_str.startswith("id"):
        return input_str.replace("id", "")
    elif input_str.startswith("topic-"):
        parts = input_str.split('_')
        if len(parts) == 2:
            return parts[0].replace("topic-", "")
        else:
            return input_str
    else:
        return input_str

def extract_user_id(input_str):
    if input_str.startswith("https://vk.com/") or input_str.startswith("vk.com/"):
        wall_part = input_str.split('/')[-1]
        user_id = wall_part.split('_')[0].replace("wall", "")
        return user_id.replace("id", "")
    elif input_str.startswith("id"):
        return input_str.replace("id", "")
    elif input_str.startswith("wall"):  
        wall_part = input_str.split('_')[0]  
        user_id = wall_part.replace("wall", "") 
        return user_id
    else:
        return input_str

def write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def update_state_theme(file_path, new_state):
    data = read_json_file(file_path)
    data['Theme'] = {"state": new_state}
    write_json_file(file_path, data)

def update_state_manager(file_path, new_state):
    data = read_json_file(file_path)
    data['Manager'] = {"state": new_state}
    write_json_file(file_path, data)

async def get_friends_token(session, token, proxy):
    url = 'https://api.vk.com/method/friends.get'
    all_friends = []
    offset = 0
    count = 5000 

    while True:
        params = {
            'access_token': token,
            'v': '5.131',
            'order': 'hints',
            'count': count,
            'offset': offset
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data:
                        friends = data['response']['items']
                        all_friends.extend(friends) 
                        total_count = data['response']['count'] 
                        if offset + count >= total_count:
                            break  
                        offset += count
                    await asyncio.sleep(0.33)  

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СПИСКА ДРУЗЕЙ: {e}")
            return []

    return all_friends

async def get_friends(session, token, user_id, proxy, count=5000):  
    url = 'https://api.vk.com/method/friends.get'
    all_friends = []
    offset = 0

    while True:
        params = {
            'access_token': token,
            'v': '5.131',
            'user_id': user_id,
            'order': 'hints',
            'fields': 'first_name,last_name',
            'count': count,
            'offset': offset 
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data:
                        friends = data['response']['items']
                        all_friends.extend(friends) 

                        if len(friends) < count:
                            break  

                        offset += count
                    await asyncio.sleep(0.33) 

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СПИСКА ДРУЗЕЙ ПОЛЬЗОВАТЕЛЯ С ID: {user_id}: {e}")
            return

    return all_friends
        
async def get_user_groups(session, user_id, token, proxy, count=1000):
    url = "https://api.vk.com/method/groups.get"
    all_groups = []
    offset = 0

    while True:
        params = {
            "user_id": user_id,
            "extended": 1,
            "fields": "contacts",
            "access_token": token,
            "v": "5.131",
            'count': count, 
            'offset': offset  
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data:
                        groups = data['response']['items']
                        all_groups.extend(groups)  

                        if len(groups) < count:
                            break  

                        offset += count
                        await asyncio.sleep(0.33)  

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СПИСКА ГРУПП ПОЛЬЗОВАТЕЛЯ С ID: {user_id}: {e}")
            return

    return all_groups

async def get_contacts_groups(session, user_id, token, proxy):
    url = "https://api.vk.com/method/groups.get"
    params = {
        "user_id": user_id,
        "extended": 1,
        "fields": "contacts",
        "access_token": token,
        "v": "5.131"
    }

    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'response' in data:
                    return data['response']['items']

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СПИСКА ГРУПП: {e}")
        return []

async def get_chat_members(session, token, chat_id, proxy):
    url = 'https://api.vk.com/method/messages.getConversationMembers'
    params = {
        'access_token': token,
        'v': '5.131',
        'peer_id': 2000000000 + chat_id
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                result = await response.json()
                return [member['member_id'] for member in result['response']['items'] if member['member_id'] > 0]

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ ПОЛУЧЕНИИ УЧАСТНИКОВ БЕСЕДЫ С ID: {chat_id}: {e}")
        return []

async def get_chat_title(session, token, chat_id, proxy):
    url = 'https://api.vk.com/method/messages.getConversationsById'
    params = {
        'access_token': token,
        'v': '5.131',
        'peer_ids': chat_id
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'error' in data:
                    logging.error(f"ОШИБОЧКА: {data['error']['error_msg']}")
                    return None
                else:
                    return data['response']['items'][0]['chat_settings']['title']

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА: {e}")
        return 

async def get_all_message_ids(session, token, peer_id, proxy):
    url = 'https://api.vk.com/method/messages.getHistory'
    message_ids = []
    offset = 0
    count = 200

    while True:
        params = {
            'access_token': token,
            'v': '5.131',
            'peer_id': peer_id,
            'count': count,
            'offset': offset
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    items = result['response']['items']
                    if not items:
                        break
                    message_ids.extend([msg['id'] for msg in items])
                    offset += count
                    await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБОЧКА ПРИ ПОЛУЧЕНИИ ИСТОРИИ СООБЩЕНИЙ: {e}")
            break

    return message_ids

async def get_all_message_ids_group(session, token, peer_id, proxy):
    url = 'https://api.vk.com/method/messages.getHistory'
    message_ids = []
    offset = 0
    count = 200

    while True:
        params = {
            'access_token': token,
            'v': '5.131',
            'peer_id': -peer_id,
            'count': count,
            'offset': offset
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    items = result['response']['items']
                    if not items:
                        break
                    message_ids.extend([msg['id'] for msg in items])
                    offset += count
                    await asyncio.sleep(0.33)
 
        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИСТОРИИ СООБЩЕНИЙ: {e}")
            break

    return message_ids
    
async def get_chat_ids(session, token, proxy):
    url = 'https://api.vk.com/method/messages.getConversations'
    params = {
        'access_token': token,
        'v': '5.131'
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                result = await response.json()
                chat_ids = []
                for item in result['response']['items']:
                    if 'chat_settings' in item['conversation']:
                        chat_ids.append({
                            'chat_id': item['conversation']['peer']['id'] - 2000000000,
                            'title': item['conversation']['chat_settings']['title']
                        })
                return chat_ids
 
    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ ПОЛУЧЕНИИ БЕСЕД: {e}")
        return []

def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        logging.error(f"НЕЖДАННАЯ ОШИБОЧКА: {e}")
        return {}

async def check_token_validity(session, token, proxy):
    url = 'https://api.vk.com/method/users.get'
    params = {
        'access_token': token,
        'v': '5.131'
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                return 'response' in data

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПРОВЕРКЕ ТОКЕНА: {e}")
        return False

async def get_token(session, login, password, proxy):
    url = "https://oauth.vk.com/token"
    params = {
        'grant_type': 'password',
        'client_id': '2274003',
        'client_secret': 'hHbZxrka2uZ6jB1inYsH',
        'username': login,
        'password': password,
        'v': '5.131'
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('access_token'), 'access_token' in data

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ТОКЕНА: {e}")
        return None, False

def read_names(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            names = []
            for line in lines:
                line = line.strip() 
                if line: 
                    parts = line.split()
                    if len(parts) >= 2:
                        first_name = parts[0]
                        last_name = parts[1]
                        names.append((first_name, last_name))
            if names:
                return random.choice(names)
            else:
                return None
    except FileNotFoundError:
        return None

def write_to_json(user_tokens, botpod_tokens, group_tokens, file_path):
    data = read_json_file(file_path)
    data.update({
        "user_tokens": user_tokens,
        "botpod_tokens": botpod_tokens,
        "group_tokens": group_tokens
    })
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def get_group_token(login, password, group_id):
    proxy = load_proxy()

    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server={proxy}")

    driver = webdriver.Chrome(options=options)
    try:
        url = f'https://oauth.vk.com/oauth/authorize?client_id=6121396&scope=134623237&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&group_ids={group_id}'
        driver.get(url)
        driver.find_element(By.NAME, 'email').send_keys(login)
        driver.find_element(By.NAME, 'pass').send_keys(password, Keys.RETURN)
        time.sleep(5)
        driver.find_element(By.XPATH, '//button[text()="Разрешить" or text()="Allow"]').click()
        time.sleep(5)
        current_url = driver.current_url
        token = current_url.split('access_token_')[1].split('=')[1].split('&')[0]
        return token
    finally:
        driver.quit()

async def download_photo(session, url, path, proxy):
    try:
        async with session.get(url, proxy=proxy) as response:
            if response.status == 200:
                async with aiofiles.open(path, mode='wb') as f:
                    await f.write(await response.read())

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ СКАЧИВАНИИ ФОТОГРАФИИ ПО URL {url}: {e}")

async def get_group_wall_posts(session, token, group_id, proxy, count=100):
    url_wall_get = 'https://api.vk.com/method/wall.get'
    all_posts = []
    offset = 0
    try:
        if isinstance(group_id, str):
            group_id = int(group_id)
        while True:
            params_wall_get = {
                'owner_id': -int(group_id),
                'access_token': token,
                'v': '5.131',
                'count': count,
                'offset': offset
            }
            async with session.get(url_wall_get, params=params_wall_get, proxy=proxy) as response:
                posts_response = await response.json()
                posts = posts_response.get('response', {}).get('items', [])
                all_posts.extend(posts)

                if len(posts) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОСТОВ ДЛЯ ГРУППЫ {group_id}: {e}")
        return

    return all_posts

async def get_group_photos(session, token, group_id, proxy, count=200):
    url_photos_get_all = 'https://api.vk.com/method/photos.getAll'
    all_photos = []
    offset = 0
    try:
        if isinstance(group_id, str):
            group_id = int(group_id)
        while True:
            params_photos_get_all = {
                'owner_id': -int(group_id),
                'access_token': token,
                'v': '5.131',
                'count': count,
                'offset': offset
            }
            async with session.get(url_photos_get_all, params=params_photos_get_all, proxy=proxy) as response:
                photos_response = await response.json()
                photos = photos_response.get('response', {}).get('items', [])
                all_photos.extend(photos)

                if len(photos) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ФОТОГРАФИЙ ДЛЯ ГРУППЫ {group_id}: {e}")

    return all_photos

async def get_group_videos(session, token, group_id, proxy, count=200):
    url_video_get = 'https://api.vk.com/method/video.get'
    all_videos = []
    offset = 0
    try:
        if isinstance(group_id, str):
            group_id = int(group_id)
        while True:
            params_video_get = {
                'owner_id': -int(group_id),
                'access_token': token,
                'v': '5.131',
                'count': count,
                'offset': offset
            }
            async with session.get(url_video_get, params=params_video_get, proxy=proxy) as response:
                videos_response = await response.json()
                videos = videos_response.get('response', {}).get('items', [])
                all_videos.extend(videos)

                if len(videos) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ВИДЕО ДЛЯ ГРУППЫ {group_id}: {e}")
        return

    return all_videos

async def get_group_contacts(session, token, group_id, proxy):
    url_groups_get_by_id = 'https://api.vk.com/method/groups.getById'
    try:
        if isinstance(group_id, str):
            group_id = int(group_id)

        params_groups_get_by_id = {
            'group_id': group_id,
            'fields': 'contacts',
            'access_token': token,
            'v': '5.131'
        }
        async with session.get(url_groups_get_by_id, params=params_groups_get_by_id, proxy=proxy) as response:
            contacts = await response.json()
            if contacts and 'response' in contacts:
                return contacts['response'][0].get('contacts', [])
            return []

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ КОНТАКТОВ ДЛЯ ГРУППЫ {group_id}: {e}")
        return []

    return all_contacts

async def get_group_discussions(session, token, group_id, proxy, count=100):
    url_board_get_topics = 'https://api.vk.com/method/board.getTopics'
    all_discussions = []
    offset = 0
    try:
        if isinstance(group_id, str):
            group_id = int(group_id)
        while True:
            params_board_get_topics = {
                'group_id': group_id,
                'access_token': token,
                'v': '5.131',
                'count': count,
                'offset': offset
            }
            async with session.get(url_board_get_topics, params=params_board_get_topics, proxy=proxy) as response:
                discussions_response = await response.json()
                discussions = discussions_response.get('response', {}).get('items', [])
                all_discussions.extend(discussions)

                if len(discussions) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ОБСУЖДЕНИЙ ГРУППЫ {group_id}: {e}")

    return all_discussions

async def get_admin_groups(session, token, proxy):
    url = 'https://api.vk.com/method/groups.get'
    params = {
        'access_token': token,
        'filter': 'admin',
        'v': '5.131'
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'response' in data:
                    return data['response']['items']

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ГРУППАХ: {e}")
        return []

async def is_admin(session, token, group_id, proxy):
    url = "https://api.vk.com/method/groups.getMembers"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        "filter": "managers"
    }
    async with session.get(url, params=params, proxy=proxy) as response:
        result = await response.json()
        if "response" in result and "items" in result["response"]:
            for member in result["response"]["items"]:
                if member.get("role") in ("administrator", "creator", "editor"):
                    return True
        return False

def read_accounts(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        accounts = []
        for line in file:
            parts = line.strip().split(":")
            if len(parts) == 2:
                accounts.append(parts)
        return accounts

def get_botpod_token(login, password):
    proxy = load_proxy()

    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server={proxy}")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get('https://oauth.vk.com/authorize?client_id=6441755&redirect_uri=https://api.vk.com/blank.html&display=page&response_type=token&revoke=1')
        driver.find_element(By.NAME, 'email').send_keys(login)
        driver.find_element(By.NAME, 'pass').send_keys(password, Keys.RETURN)
        time.sleep(5)
        driver.find_element(By.XPATH, '//button[text()="Разрешить" or text()="Allow"]').click()
        time.sleep(5)
        token = driver.current_url.split('access_token=')[1].split('&')[0]
        return token
    finally:
        driver.quit()

def read_tokens(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            if file_path.endswith(".json"):
                data = json.load(file)
                return data.get("user_tokens", {})
            elif file_path.endswith(".txt"):
                tokens = {}
                for line in file:
                    key, value = line.strip().split(':')
                    tokens[key] = value
                return tokens
    except FileNotFoundError:
        return {}

def read_botpod_tokens(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            if file_path.endswith(".json"):
                data = json.load(file)
                return data.get("botpod_tokens", {})
            elif file_path.endswith(".txt"):
                tokens = {}
                for line in file:
                    key, value = line.strip().split(':')
                    tokens[key] = value
                return tokens
    except FileNotFoundError:
        return {}

def read_group_tokens(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            if file_path.endswith(".json"):
                data = json.load(file)
                return data.get("group_tokens", {})
            elif file_path.endswith(".txt"):
                tokens = {}
                for line in file:
                    key, value = line.strip().split(':')
                    tokens[key] = value
                return tokens
    except FileNotFoundError:
        return {}

def write_group_tokens(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            tokens = {}
            for line in file:
                token_match = re.search(r'vk1\.[\w.-]+', line)
                group_id_match = re.search(r'(club|public)(\d+)', line)
                if token_match and group_id_match:
                    token = token_match.group(0)
                    group_id = group_id_match.group(2) 
                    group_type = group_id_match.group(1)  
                    tokens[f'{group_type}{group_id}'] = token 
            return tokens
    except FileNotFoundError:
        return {}

def write_tokens(file_path, tokens):
    with open(file_path, "w", encoding="utf-8") as file:
        for login, token in tokens.items():
            file.write(f"{login}:{token}\n")

async def check_accounts_validity(accounts, filename):
    headers = load_headers()
    proxy = load_proxy()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        valid_accounts = []
        for login, password in accounts:
            is_valid = await get_token(session, login, password, proxy)  
            print_white(f"АККАУНТ {login} {'ВАЛИДНЫЙ' if is_valid else 'НЕВАЛИДНЫЙ'}")
            if is_valid:
                valid_accounts.append((login, password))

        with open(filename, "w") as f:
            for login, password in valid_accounts:
                f.write(f"{login}:{password}\n")

async def check_tokens_validity(tokens, filename):
    headers = load_headers()
    proxy = load_proxy()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        valid_tokens = []
        for login, token in tokens.items():
            is_valid = await check_token_validity(session, token, proxy)  
            print_white(f"ТОКЕН ДЛЯ АККАУНТА {login} {'ВАЛИДНЫЙ' if is_valid else 'НЕВАЛИДНЫЙ'}")
            if is_valid:
                valid_tokens.append((login, token))

        with open(filename, "w") as f:
            for login, token in valid_tokens:
                f.write(f"{login}:{token}\n")

async def get_tokens_for_accounts(accounts, tokens):
    headers = load_headers()
    proxy = load_proxy()
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
        all_tokens_taken = True
        for login, password in accounts:
            if login not in tokens:
                all_tokens_taken = False
                token, is_valid = await get_token(session, login, password, proxy)  
                if is_valid:
                    tokens[login] = token
                    print_white(f"ТОКЕН {login} ПОЛУЧЕН")
                else:
                    print_white(f"ТОКЕН {login} НЕПОЛУЧЕН")

        if all_tokens_taken:
            print_white("ВСЕ ТОКЕНЫ УЖЕ ВЗЯТЫ")
        else:
            write_tokens(os.path.join(BASE_DIR, "tokens.txt"), tokens)

async def get_group_info(session, token, group_id, proxy):
  url = 'https://api.vk.com/method/groups.getById'
  params = {
      'access_token': token,
      'v': '5.131',
      'group_id': group_id,
      'fields': 'photo_max'
  }
  async with session.get(url, params=params, proxy=proxy) as response:
      if response.status == 200:
          result = await response.json()
          return result['response'][0]

async def get_album_info(session, token, group_id, album_id, proxy):
  url = 'https://api.vk.com/method/photos.getAlbums'
  params = {
      'access_token': token,
      'v': '5.131',
      'owner_id': -int(group_id), 
      'album_ids': album_id
  }
  async with session.get(url, params=params, proxy=proxy) as response:
      if response.status == 200:
          result = await response.json()
          return result['response']['items'][0]

async def get_token_info(session, token, proxy):
  url = 'https://api.vk.com/method/users.get'
  params = {
      'access_token': token,
      'v': '5.131'
  }
  async with session.get(url, params=params, proxy=proxy) as response:
      if response.status == 200:
          result = await response.json()
          return result['response'][0]

async def get_user_info(session, token, user_id, proxy):
    url = 'https://api.vk.com/method/users.get'
    all_user_infos = []
    max_ids_per_request = 100

    if isinstance(user_id, list):
        for i in range(0, len(user_id), max_ids_per_request):
            ids_chunk = user_id[i: i + max_ids_per_request]
            params = {
                'access_token': token,
                'v': '5.131',
                'user_ids': ','.join(map(str, ids_chunk)),
                'fields': 'first_name,last_name,photo_max_orig'
            }
            try:
                async with session.get(url, params=params, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'response' in data:
                            all_user_infos.extend(data['response'])
                    await asyncio.sleep(0.33)

            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЯХ: {e}")
                return []

        return all_user_infos

    else:  
        params = {
            'access_token': token,
            'v': '5.131',
            'user_ids': str(user_id), 
            'fields': 'first_name,last_name,photo_max_orig'
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data and data['response']:
                        return data['response'][0]  

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {e}")
            return 
    
async def get_group_members(session, token, group_id, proxy, count=1000):
    url = 'https://api.vk.com/method/groups.getMembers'
    all_members = []
    offset = 0

    while True:
        params = {
            'access_token': token,
            'v': '5.131',
            'group_id': group_id,
            'count': count, 
            'offset': offset  
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data:
                        members = data['response']['items']
                        all_members.extend(members)  

                        if len(members) < count:
                            break  

                        offset += count 
                    await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СПИСКА ПОДПИСЧИКОВ ГРУППЫ С ID: {group_id}: {e}")
            break

    return all_members

async def get_info(session, token, user_id, proxy):
    url_get_conversations_by_id = 'https://api.vk.com/method/messages.getConversationsById'
    url_groups_get_by_id = 'https://api.vk.com/method/groups.getById'
    url_users_get = 'https://api.vk.com/method/users.get'

    if user_id in user_cache:
        return user_cache[user_id]

    if user_id >= 2000000000:
        conversation_id = user_id - 2000000000
        if conversation_id in conversation_cache:
            return conversation_cache[conversation_id]
        try:
            params_get_conversations_by_id = { 
                'peer_ids': user_id,
                'access_token': token,
                'v': '5.131'
            }
            async with session.get(url_get_conversations_by_id, params=params_get_conversations_by_id, proxy=proxy) as conversation_info:
                conversation_info_json = await conversation_info.json()
                if conversation_info_json and 'response' in conversation_info_json:
                    title = conversation_info_json['response']['items'][0]['chat_settings']['title']
                    conversation_cache[conversation_id] = f"Беседа {title}"
                    return conversation_cache[conversation_id]
                else:
                    return f"Беседа {conversation_id}"
        except aiohttp.ClientError:
            return f"Беседа {conversation_id}"

    elif user_id < 0:
        group_id = abs(user_id)
        if group_id in group_cache:
            return group_cache[group_id]
        try:
            params_groups_get_by_id = {  
                'group_id': group_id,
                'access_token': token,
                'v': '5.131'
            }
            async with session.get(url_groups_get_by_id, params=params_groups_get_by_id, proxy=proxy) as group_info:
                group_info_json = await group_info.json()
                if group_info_json and 'response' in group_info_json:
                    name = group_info_json['response'][0]['name']
                    group_cache[group_id] = f"Группа {name} - {group_id}"
                    return group_cache[group_id]
                else:
                    return f"Группа {group_id}"
        except aiohttp.ClientError:
            return f"Группа {group_id}"
    else:
        try:
            params_users_get = {  
                'user_ids': user_id,
                'access_token': token,
                'v': '5.131'
            }
            async with session.get(url_users_get, params=params_users_get, proxy=proxy) as user_info_list:
                user_info_list_json = await user_info_list.json()
                if user_info_list_json and 'response' in user_info_list_json:
                    user_info = user_info_list_json['response'][0]
                    user_info = f"{user_info['first_name']} {user_info['last_name']}"
                else:
                    user_info = user_id

        except aiohttp.ClientError:
            user_info = user_id

    user_cache[user_id] = user_info
    return user_info

async def get_conversation_info(session, token, peer_id, proxy):
    url_get_conversations_by_id = 'https://api.vk.com/method/messages.getConversationsById'
    url_groups_get_by_id = 'https://api.vk.com/method/groups.getById'

    if peer_id >= 2000000000:
        conversation_id = peer_id - 2000000000
        if conversation_id in conversation_cache:
            return conversation_cache[conversation_id]
        try:
            params_get_conversations_by_id = {
                'peer_ids': peer_id,
                'access_token': token,
                'v': '5.131'
            }
            async with session.get(url_get_conversations_by_id, params=params_get_conversations_by_id, proxy=proxy) as conversation_info:
                conversation_info_json = await conversation_info.json()
                if conversation_info_json and 'response' in conversation_info_json:
                    title = conversation_info_json['response']['items'][0]['chat_settings']['title']
                    conversation_cache[conversation_id] = f"Беседа - {title}"
                    return conversation_cache[conversation_id]
                else:
                    return f"Беседа {conversation_id}"
        except aiohttp.ClientError:
            return f"Беседа {conversation_id}"
    elif peer_id < 0:
        group_id = abs(peer_id)
        if group_id in group_cache:
            return group_cache[group_id]
        try:
            params_groups_get_by_id = {
                'group_id': group_id,
                'access_token': vk.token['access_token'],
                'v': '5.131'
            }
            async with session.get(url_groups_get_by_id, params=params_groups_get_by_id, proxy=proxy) as group_info:
                group_info_json = await group_info.json()
                if group_info_json and 'response' in group_info_json:
                    name = group_info_json['response'][0]['name']
                    group_cache[group_id] = f"Группа {name} - {group_id}"
                    return group_cache[group_id]
                else:
                    return f"Группа {group_id}"
        except aiohttp.ClientError:
            return f"Группа {group_id}"
    else:
        return await get_info(session, token, peer_id, proxy)

async def get_dialogs(session, token, count, proxy):
    url_get_conversations = 'https://api.vk.com/method/messages.getConversations'
    all_dialogs = []
    offset = 0

    if count is None: 
        count = 200  
        while True:
            params_get_conversations = {
                "access_token": token,
                "v": "5.131",
                "count": count,
                "offset": offset
            }
            try:
                async with session.get(url_get_conversations, params=params_get_conversations, proxy=proxy) as response:
                    response_json = await response.json()
                    dialogs = response_json.get("response", {}).get("items", [])
                    all_dialogs.extend(dialogs)

                    if len(dialogs) < count:
                        break

                    offset += count
                await asyncio.sleep(0.33)

            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА: {e}")
                return
    else: 
        params_get_conversations = {
            "access_token": token,
            "v": "5.131",
            "count": count
        }
        try:
            async with session.get(url_get_conversations, params=params_get_conversations, proxy=proxy) as response:
                response_json = await response.json()
                dialogs = response_json.get("response", {}).get("items", [])
                all_dialogs.extend(dialogs)
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА: {e}")
            return

    return all_dialogs

async def get_history(session, token, peer_id, proxy, count=200):
    url_get_history = 'https://api.vk.com/method/messages.getHistory'
    all_messages = []
    offset = 0

    while True:
        params_get_history = {
            "access_token": token,
            "v": "5.131",
            "peer_id": peer_id,
            "count": count,
            "offset": offset
        }
        try:
            async with session.get(url_get_history, params=params_get_history, proxy=proxy) as response:
                response_json = await response.json()
                messages = response_json.get("response", {}).get("items", [])
                all_messages.extend(messages)

                if len(messages) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА: {e}")
            return

    return all_messages

async def get_videos(session, token, user_id, proxy, count=100):
    url_video_get = 'https://api.vk.com/method/video.get'
    all_videos = []
    offset = 0

    while True:
        params_uploaded = {
            'owner_id': user_id,
            'access_token': token,
            'v': '5.131',
            'count': count,
            'offset': offset
        }
        try:
            async with session.get(url_video_get, params=params_uploaded, proxy=proxy) as response:
                response_json = await response.json()
                videos = response_json.get('response', {}).get('items', [])
                all_videos.extend(videos)

                if len(videos) < count:
                    break 

                offset += count
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ЗАГРУЖЕННЫХ ВИДЕО ДЛЯ {user_id}: {e}")
            return

    offset = 0  

    while True:  
        params_favorites = {
            'owner_id': user_id,
            'album_id': -1,
            'access_token': token,
            'v': '5.131',
            'count': count,
            'offset': offset
        }
        try:
            async with session.get(url_video_get, params=params_favorites, proxy=proxy) as response:
                response_json = await response.json()
                videos = response_json.get('response', {}).get('items', [])
                all_videos.extend(videos)

                if len(videos) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИЗБРАННЫХ ВИДЕО ДЛЯ {user_id}: {e}")
            return

    return all_videos

async def get_subscriptions(session, token, user_id, proxy, count=200):
    url_users_get_subscriptions = 'https://api.vk.com/method/users.getSubscriptions'
    all_subscriptions = []
    offset = 0

    while True:
        params_users_get_subscriptions = {
            'user_id': user_id,
            'access_token': token,
            'v': '5.131',
            'count': count,
            'offset': offset,
            'extended': 1  
        }
        try:
            async with session.get(url_users_get_subscriptions, params=params_users_get_subscriptions, proxy=proxy) as response:
                subscriptions = await response.json()
                items = subscriptions.get('response', {}).get('items', [])
                all_subscriptions.extend(items)

                if len(items) < count:
                    break

                offset += count
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОДПИСОК ДЛЯ {user_id}: {e}")
            return

    return all_subscriptions

async def get_photos(session, token, user_id, proxy, count=200): 
    url_photos_get_all = 'https://api.vk.com/method/photos.getAll'
    all_photos = []
    offset = 0

    while True:
        params_photos_get_all = {
            'owner_id': user_id,
            'access_token': token,
            'v': '5.131',
            'count': count, 
            'offset': offset  
        }
        try:
            async with session.get(url_photos_get_all, params=params_photos_get_all, proxy=proxy) as response:
                photos_response = await response.json()
                photos = photos_response.get('response', {}).get('items', [])
                all_photos.extend(photos)

                if len(photos) < count:
                    break  

                offset += count
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ФОТОГРАФИЙ ДЛЯ {user_id}: {e}")
            return

    return all_photos

async def get_wall_posts(session, token, user_id, proxy, count=100): 
    url_wall_get = 'https://api.vk.com/method/wall.get'
    all_posts = []
    offset = 0

    while True:
        params_wall_get = {
            'owner_id': user_id,
            'access_token': token,
            'v': '5.131',
            'count': count,  
            'offset': offset 
        }
        try:
            async with session.get(url_wall_get, params=params_wall_get, proxy=proxy) as response:
                posts_response = await response.json()
                posts = posts_response.get('response', {}).get('items', [])  
                all_posts.extend(posts)  

                if len(posts) < count:
                    break  

                offset += count
            await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОСТОВ ДЛЯ {user_id}: {e}")
            return

    return all_posts
    
async def get_all_photos_album(session, token, owner_id, album_id, proxy):
    all_photos = []
    offset = 0
    url = 'https://api.vk.com/method/photos.get'
    params = {
        'access_token': token,
        'v': '5.131',
        'owner_id': owner_id,
        'album_id': album_id,
        'count': 1000,
        'offset': offset
    }

    while True:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                result = await response.json()
                photos = result['response']['items']
                if not photos:
                    break
                all_photos.extend(photos)
                offset += 1000
                params['offset'] = offset
                await asyncio.sleep(0.33)

    return all_photos