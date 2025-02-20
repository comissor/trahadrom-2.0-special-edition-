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

async def massDov(session, user_id, tokens, proxy):
    tasks = [add_friendMass(session, token, login, user_id, proxy) for login, token in tokens.items()]
    await asyncio.gather(*tasks)

async def add_friendMass(session, first_token, token, login, user_ids, proxy):
    url = "https://api.vk.com/method/friends.add"
    sent_requests = set()

    user_infos = await reg.get_user_info(session, first_token, user_ids, proxy)

    for user_info in user_infos:
        user_id = user_info['id']
        user_name = f"{user_info['first_name']} {user_info['last_name']}"

        if user_id in sent_requests:
            print_white(f"НА ЛОГИНЕ {login} УЖЕ БЫЛА ОТПРАВЛЕНА ЗАЯВКА К ПОЛЬЗОВАТЕЛЮ {user_name}")
            continue 

        is_friend = await check_friend_status_massDov(session, token, user_id, proxy)
        if is_friend:
            print_white(f"{user_name} УЖЕ ЯВЛЯЕТСЯ ДРУГОМ ЛОГИНА {login}")
        else:
            try:
                params = {
                    "access_token": token,
                    "v": "5.131",
                    "user_id": user_id
                }
                async with session.post(url, params=params, proxy=proxy) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_code = data.get('response')
                        if response_code == 1:
                            print_white(f"ЛОГИН {login} УСПЕШНО ДОБАВИЛ В ДРУЗЬЯ {user_name}")
                            sent_requests.add(user_id) 
                        elif response_code == 4:
                            print_white(f"НА ЛОГИНЕ {login} УЖЕ БЫЛА ОТПРАВЛЕНА ЗАЯВКА К ПОЛЬЗОВАТЕЛЮ {user_name}")
                            sent_requests.add(user_id) 
                        else:
                            print_white(f"ЛОГИНУ {login} НЕ УДАЛОСЬ ДОБАВИТЬ В ДРУЗЬЯ {user_name}: {data['error']['error_msg']}")
                            sent_requests.add(user_id)
                    await asyncio.sleep(0.33)

            except aiohttp.ClientError as e:
                logging.error(f"ОШИБКА ПРИ ОТПРАВКЕ ЗАЯВКИ В ДРУЗЬЯ: {e}")

async def check_friend_status_massDov(session, token, user_id, proxy):
    url = 'https://api.vk.com/method/friends.areFriends'
    params = {
        'access_token': token,
        'v': '5.131',
        'user_ids': user_id
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'response' in data and len(data['response']) > 0:
                    return data['response'][0]['friend_status'] == 3
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПРОВЕРКЕ СТАТУСА ДРУЖБЫ С ПОЛЬЗОВАТЕЛЕМ С ID: {user_id}: {e}")
        return False

async def send_friend_request_random(session, friend_id, login, token, active_friends, proxy):
    url = 'https://api.vk.com/method/friends.add'  
    friend_info = await reg.get_user_info(session, token, friend_id, proxy)
    friend_name = f"{friend_info['first_name']} {friend_info['last_name']}"

    try:
        if not await is_friend(session, token, login, friend_id, proxy):  
            params = {
                'access_token': token,
                'v': '5.131',
                'user_id': friend_id
            }
            async with session.post(url, params=params, proxy=proxy) as response:  
                result = await response.json()
                if 'error' not in result:
                    print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЗАЯВОЧКА В ДРУЗЬЯ ПОЛЬЗОВАТЕЛЮ {friend_name}")
                    return True
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ ЗАЯВКИ В ДРУЗЬЯ: {error_code} - {error_msg}")
                    return False
                await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:  
        logging.error(f"ОШИБКА ПРИ ОТПРАВКЕ ЗАЯВКИ В ДРУЗЬЯ С ЛОГИНА {login} ПОЛЬЗОВАТЕЛЮ {friend_name}: {e}")
        return False

async def friends_pol_mass_random(session, user_id, tokens, proxy):
    friends = await reg.get_friends(session, list(tokens.values())[0], user_id, proxy)
    random_friends = random.sample(friends, min(50 * len(tokens), len(friends)))
    active_friends = await filter_active_friends(session, list(tokens.values())[0], random_friends, proxy)

    tasks = []
    i = 0
    while active_friends:
        login, token = list(tokens.items())[i % len(tokens)]
        token_tasks = []  
        for _ in range(50):  
            if not active_friends:
                break
            friend_id = active_friends.pop()
            task = send_friend_request_random(session, friend_id, login, token, active_friends, proxy)
            token_tasks.append(task)
        tasks.extend(token_tasks) 
        i += 1

    results = await asyncio.gather(*tasks)
    await asyncio.sleep(1)
    return results

async def filter_active_friends(session, token, friends, proxy):
    url = 'https://api.vk.com/method/users.get'
    active_friends = []
    for friend_id in friends:
        params = {
            'access_token': token,
            'v': '5.131',
            'user_ids': friend_id,
            'fields': 'deactivated'
        }
        try:
            async with session.get(url, params=params, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'response' in data and len(data['response']) > 0 and 'deactivated' not in data['response'][0]:
                        active_friends.append(friend_id)
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПРОВЕРКЕ СТАТУСА ДРУГА С ID: {friend_id}: {e}")
    return active_friends

async def is_friend(session, token, user_id, friend_id, proxy):
    url = 'https://api.vk.com/method/friends.areFriends'
    params = {
        'access_token': token,
        'v': '5.131',
        'user_ids': friend_id
    }
    try:
        async with session.get(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                data = await response.json()
                if 'response' in data and len(data['response']) > 0:
                    return data['response'][0]['friend_status'] == 3
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПРОВЕРКЕ СТАТУСА ДРУЖБЫ С ПОЛЬЗОВАТЕЛЕМ С ID: {friend_id}: {e}")
        return False

async def group_friends_pol_mass_random(session, group_id, tokens, proxy):
    members = await reg.get_group_members(session, list(tokens.values())[0], group_id, proxy) 
    random_members = random.sample(members, min(50, len(members)))
    active_friends = await filter_active_friends(session, list(tokens.values())[0], random_members, proxy) 

    tasks = []
    i = 0
    while len(tasks) < 50 and active_friends:
        friend_id = active_friends.pop()
        login, token = list(tokens.items())[i % len(tokens)]
        task = send_friend_request_random(session, friend_id, login, token, active_friends, proxy)
        tasks.append(task)
        i += 1

    results = await asyncio.gather(*tasks)
    await asyncio.sleep(1)
    return results

async def add_friends(session, tokens, proxy):
    tasks = []
    num_tokens = len(tokens)
    all_friends = True  

    for i, (login, token) in enumerate(tokens.items()):
        user_info = await reg.get_token_info(session, token, proxy)
        user_id = user_info['id']
        if user_id is None:
            continue

        next_index = (i + 1) % num_tokens
        next_login, next_token = list(tokens.items())[next_index]
        next_user_info = await reg.get_token_info(session, next_token, proxy)
        next_user_id = next_user_info['id']
        if next_user_id is None:
            continue

        if not await is_friend(session, token, user_id, next_user_id, proxy): 
            all_friends = False
            task = add_friend(session, token, user_id, next_user_id, proxy)
            tasks.append(task)

    if all_friends:
        print_white("ВСЕ ТОКЕНЫ УЖЕ В ДРУЗЬЯХ")
    else:
        await asyncio.gather(*tasks)
        print_white("УСПЕШНО ДОБАВИЛИ ПОЛЬЗОВАТЕЛЕЙ ДРУГ К ДРУГУ В ДРУЗЬЯ")

async def add_friend(session, token, user_id, friend_id, proxy):
    url = 'https://api.vk.com/method/friends.add'
    params = {
        'access_token': token,
        'v': '5.131',
        'user_id': friend_id
    }
    try:
        async with session.post(url, params=params, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                return True
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ ЗАЯВКИ В ДРУЗЬЯ: {error_code} - {error_msg}")
                return
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА: {e}")
        return False

async def accept_friend_requests(session, token, login, proxy):
    get_requests_url = 'https://api.vk.com/method/friends.getRequests'
    add_friend_url = 'https://api.vk.com/method/friends.add'
    all_friend_requests = []
    offset = 0
    count = 1000

    while True:
        get_requests_params = {
            'access_token': token,
            'v': '5.131',
            'out': 0,
            'count': count,
            'offset': offset
        }

        try:
            async with session.get(get_requests_url, params=get_requests_params, proxy=proxy) as response:
                response_data = await response.json()
                friend_requests = response_data['response']['items']
                all_friend_requests.extend(friend_requests)

                if not friend_requests:
                    break

                total_count = response_data['response']['count']
                if offset + count >= total_count:
                    break
                offset += count
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ЗАЯВОК В ДРУЗЬЯ: {e}")
            return

    for user_id in all_friend_requests:
        add_friend_params = {
            'access_token': token,
            'v': '5.131',
            'user_id': user_id
        }
        try:
            async with session.post(add_friend_url, params=add_friend_params, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    user_info = await reg.get_user_info(session, token, [user_id], proxy=proxy)
                    if user_info:
                        user_name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
                        print_white(f"НА ЛОГИНЕ {login} ПРИНЯТА ЗАЯВКА В ДРУЗЬЯ ОТ {user_name}")
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ: {error_code} - {error_msg}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ДОБАВЛЕНИИ В ДРУЗЬЯ: {e}")
