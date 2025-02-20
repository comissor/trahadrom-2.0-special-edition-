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

async def fetch_id(session, token, username, proxy):
    url_groups_getById = 'https://api.vk.com/method/groups.getById'
    url_users_get = 'https://api.vk.com/method/users.get'

    params_groups_getById = {
        'access_token': token,
        'v': '5.131',
        'group_id': username
    }

    params_users_get = {
        'access_token': token,
        'v': '5.131',
        'user_ids': username
    }

    try:
        async with session.get(url_groups_getById, params=params_groups_getById, proxy=proxy) as response:
            if response.status == 200:
                result = await response.json()
                if 'response' in result and result['response']:
                    group_id = result['response'][0]['id']
                    print_white(f"ID УСПЕШНО ИЗВЛЕЧЕН ИЗ https://vk.com/{username}, ИМ ЯВЛЯЕТСЯ {group_id}")
                    return group_id

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ ЗАПРОСЕ К API: {e}")

    try:
        async with session.get(url_users_get, params=params_users_get, proxy=proxy) as response:
            if response.status == 200:
                result = await response.json()
                if 'response' in result and result['response']:
                    user_id = result['response'][0]['id']
                    print_white(f"ID УСПЕШНО ИЗВЛЕЧЕН ИЗ https://vk.com/{username}, ИМ ЯВЛЯЕТСЯ {user_id}")
                    return user_id

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ ЗАПРОСЕ К API: {e}")

    logging.error(f"НЕ УДАЛОСЬ НАЙТИ ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППУ С ИМЕНЕМ {username}")
    return 

async def delete_messages(session, peer_id, message_ids, login, token, proxy, group, chatik, ls):
    url_delete = 'https://api.vk.com/method/messages.delete'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    for index, message_id in enumerate(message_ids, start=1):
        params_get_messages = {
            'access_token': token,
            'v': '5.131',
            'message_ids': message_id
        }
        try:
            async with session.get('https://api.vk.com/method/messages.getById', params=params_get_messages, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    if 'error' not in result:
                        message = result['response']['items'][0]
                        if message['from_id'] == user_id:
                            params_delete = {
                                'access_token': token,
                                'v': '5.131',
                                'message_ids': message_id,
                                'delete_for_all': 1
                            }
                            async with session.post(url_delete, params=params_delete, proxy=proxy) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    if 'error' not in result:
                                        if ls == 1:
                                            user_info = await reg.get_user_info(session, token, peer_id, proxy)  
                                            user_name = f"{user_info['first_name']} {user_info['last_name']}"
                                            print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ СООБЩЕНИЕ {index} В ДИАЛОГЕ С {user_name}")
                                        if chatik == 1:
                                            chat_title = await reg.get_chat_title(session, token, peer_id, proxy) 
                                            print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ СООБЩЕНИЕ {index} В БЕСЕДЕ \"{chat_title}\"")
                                        if group == 1:
                                            group_info = await reg.get_group_info(session, token, peer_id, proxy)  
                                            group_name = group_info['name']
                                            print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ СООБЩЕНИЕ {index} В ДИАЛОГЕ С ГРУППОЙ \"{group_name}\"")
                                    else:
                                        error_code = result['error']['error_code']
                                        error_msg = result['error']['error_msg']
                                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ СООБЩЕНИЯ: {error_code} - {error_msg}")
                                await asyncio.sleep(0.33)
                        else:
                            print_white(f"СООБЩЕНИЕ С ID {message_id} НЕ ЯВЛЯЕТСЯ СООБЩЕНИЕМ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ И НЕ БУДЕТ УДАЛЕНО.")
                    else:
                        error_code = result['error']['error_code']
                        error_msg = result['error']['error_msg']
                        logging.error(f"ОШИБКА VK API ПРИ ПОЛУЧЕНИИ СООБЩЕНИЯ: {error_code} - {error_msg}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ СООБЩЕНИЯ С ID: {message_id}: {e}")

async def delete_wall_posts_pol(session, owner_id, token, login, user_name, proxy):
    url_get_posts = 'https://api.vk.com/method/wall.get'
    url_delete_post = 'https://api.vk.com/method/wall.delete'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    all_post_ids = []
    offset = 0
    while True:
        params_get_posts = {
            'access_token': token,
            'v': '5.131',
            'owner_id': owner_id,
            'count': 100,
            'offset': offset
        }
        try:
            async with session.get(url_get_posts, params=params_get_posts, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    posts = result['response']['items']
                    if not posts:
                        break

                    for post in posts:
                        if post['from_id'] == user_id:
                            all_post_ids.append(post['id'])

                    offset += 100
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОСТОВ: {e}")
            break

    index = 0
    for post_id in all_post_ids:
        index += 1
        params_delete_post = {
            'access_token': token,
            'v': '5.131',
            'owner_id': owner_id,
            'post_id': post_id
        }
        try:
            async with session.post(url_delete_post, params=params_delete_post, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ ПОСТ С ID: {post_id} НА СТРАНИЦЕ ПОЛЬЗОВАТЕЛЯ {user_name} - {index}")
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ПОСТА: {error_code} - {error_msg}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ПОСТА {post_id}: {e}")

async def delete_wall_posts_group(session, owner_id, token, login, group_name, proxy):
    url_get_posts = 'https://api.vk.com/method/wall.get'
    url_delete_post = 'https://api.vk.com/method/wall.delete'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    all_post_ids = []
    offset = 0
    while True:
        params_get_posts = {
            'access_token': token,
            'v': '5.131',
            'owner_id': -int(owner_id), 
            'count': 100,
            'offset': offset
        }
        try:
            async with session.get(url_get_posts, params=params_get_posts, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    posts = result['response']['items']
                    if not posts:
                        break

                    for post in posts:
                        if post['from_id'] == user_id:
                            all_post_ids.append(post['id'])

                    offset += 100
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ПОСТОВ: {e}")
            break

    index = 0
    for post_id in all_post_ids:
        index += 1
        params_delete_post = {
            'access_token': token,
            'v': '5.131',
            'owner_id': -int(owner_id),  
            'post_id': post_id
        }
        try:
            async with session.post(url_delete_post, params=params_delete_post, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ ПОСТ С ID: {post_id} В ГРУППЕ {group_name} - {index}")
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ПОСТА: {error_code} - {error_msg}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ ПОСТА {post_id}: {e}")

async def delete_wall_post_comments_group(session, owner_id, post_id, token, login, group_name, proxy):
    url_get_comments = 'https://api.vk.com/method/wall.getComments'
    url_delete_comment = 'https://api.vk.com/method/wall.deleteComment'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    offset = 0
    while True:
        params_get_comments = {
            'access_token': token,
            'v': '5.131',
            'owner_id': -int(owner_id),  
            'post_id': post_id,
            'count': 100,
            'offset': offset
        }
        try:
            async with session.get(url_get_comments, params=params_get_comments, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result['response']['items']
                    if not comments:
                        break

                    for comment in comments:
                        if comment['from_id'] == user_id:
                            params_delete_comment = {
                                'access_token': token,
                                'v': '5.131',
                                'owner_id': -int(owner_id),  
                                'comment_id': comment['id']
                            }
                            try:
                                async with session.post(url_delete_comment, params=params_delete_comment, proxy=proxy) as response:
                                    result = await response.json()
                                    if 'error' not in result:
                                        print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ КОММЕНТАРИЙ С ID: {comment['id']} К ПОСТУ С ID: {post_id} В ГРУППЕ {group_name}")
                                    else:
                                        error_code = result['error']['error_code']
                                        error_msg = result['error']['error_msg']
                                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ КОММЕНТАРИЯ: {error_code} - {error_msg}")
                                    await asyncio.sleep(0.33)

                            except aiohttp.ClientError as e:
                                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ КОММЕНТАРИЯ {comment['id']}: {e}")

                    offset += 100
                await asyncio.sleep(0.33)
 
        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ КОММЕНТАРИЕВ: {e}")
            break

async def delete_video_comments(session, owner_id, video_id, token, login, proxy):
    url_get_comments = 'https://api.vk.com/method/video.getComments'
    url_delete_comment = 'https://api.vk.com/method/video.deleteComment'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    offset = 0
    while True:
        params_get_comments = {
            'access_token': token,
            'v': '5.131',
            'owner_id': owner_id,
            'video_id': video_id,
            'count': 100,
            'offset': offset
        }
        try:
            async with session.get(url_get_comments, params=params_get_comments, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result['response']['items']
                    if not comments:
                        break

                    for comment in comments:
                        if comment['from_id'] == user_id:
                            params_delete_comment = {
                                'access_token': token,
                                'v': '5.131',
                                'owner_id': owner_id,
                                'comment_id': comment['id']
                            }
                            try:
                                async with session.post(url_delete_comment, params=params_delete_comment, proxy=proxy) as response:
                                    result = await response.json()
                                    if 'error' not in result:
                                         print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ КОММЕНТАРИЙ С ID: {comment['id']} К ВИДЕО С ID: {video_id}")
                                    else:
                                        error_code = result['error']['error_code']
                                        error_msg = result['error']['error_msg']
                                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ КОММЕНТАРИЯ К ВИДЕО: {error_code} - {error_msg}")
                                    await asyncio.sleep(0.33)

                            except aiohttp.ClientError as e:
                                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ КОММЕНТАРИЯ {comment['id']}: {e}")

                    offset += 100
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ КОММЕНТАРИЕВ : {e}")
            break

async def delete_wall_post_comments_pol(session, owner_id, post_id, token, login, user_name, proxy):
    url_get_comments = 'https://api.vk.com/method/wall.getComments'
    url_delete_comment = 'https://api.vk.com/method/wall.deleteComment'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    offset = 0
    while True:
        params_get_comments = {
            'access_token': token,
            'v': '5.131',
            'owner_id': owner_id,
            'post_id': post_id,
            'count': 100,
            'offset': offset
        }
        try:
            async with session.get(url_get_comments, params=params_get_comments, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result['response']['items']
                    if not comments:
                        break

                    for comment in comments:
                        if comment['from_id'] == user_id:
                            params_delete_comment = {
                                'access_token': token,
                                'v': '5.131',
                                'owner_id': owner_id,
                                'comment_id': comment['id']
                            }
                            try:
                                async with session.post(url_delete_comment, params=params_delete_comment, proxy=proxy) as response:
                                    result = await response.json()
                                    if 'error' not in result:
                                        print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ КОММЕНТАРИЙ С ID: {comment['id']} К ПОСТУ С ID: {post_id} НА СТРАНИЦЕ ПОЛЬЗОВАТЕЛЯ {user_name}")
                                    else:
                                        error_code = result['error']['error_code']
                                        error_msg = result['error']['error_msg']
                                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ КОММЕНТАРИЯ К ПОСТУ: {error_code} - {error_msg}")
                                    await asyncio.sleep(0.33)

                            except aiohttp.ClientError as e:
                                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ КОММЕНТАРИЯ {comment['id']}: {e}")

                    offset += 100
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ КОММЕНТАРИЕВ: {e}")
            break

async def delete_topic_comments_group(session, group_id, topic_id, token, login, group_name, proxy):
    url_get_comments = 'https://api.vk.com/method/board.getComments'
    url_delete_comment = 'https://api.vk.com/method/board.deleteComment'
    url_get_user_info = 'https://api.vk.com/method/users.get'

    params_get_user_info = {
        'access_token': token,
        'v': '5.131'
    }

    try:
        async with session.get(url_get_user_info, params=params_get_user_info, proxy=proxy) as response:
            if response.status == 200:
                user_info = await response.json()
                user_id = user_info['response'][0]['id']
            else:
                logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ: {response.status}")
                return

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ {login}: {e}")
        return

    offset = 0
    while True:
        params_get_comments = {
            'access_token': token,
            'v': '5.131',
            'group_id': group_id,
            'topic_id': topic_id,
            'count': 100,
            'offset': offset
        }
        try:
            async with session.get(url_get_comments, params=params_get_comments, proxy=proxy) as response:
                if response.status == 200:
                    result = await response.json()
                    comments = result['response']['items']
                    if not comments:
                        break

                    for comment in comments:
                        if comment['from_id'] == user_id:
                            params_delete_comment = {
                                'access_token': token,
                                'v': '5.131',
                                'group_id': group_id,
                                'topic_id': topic_id,
                                'comment_id': comment['id']
                            }
                            try:
                                async with session.post(url_delete_comment, params=params_delete_comment, proxy=proxy) as response:
                                    result = await response.json()
                                    if 'error' not in result:
                                        print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ КОММЕНТАРИЙ С ID: {comment['id']} В ТЕМЕ С ID: {topic_id} ГРУППЫ {group_name}")
                                    else:
                                        error_code = result['error']['error_code']
                                        error_msg = result['error']['error_msg']
                                        logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ КОММЕНТАРИЯ: {error_code} - {error_msg}")
                                    await asyncio.sleep(0.33)

                            except aiohttp.ClientError as e:
                                logging.error(f"ОШИБКА ПРИ УДАЛЕНИИ КОММЕНТАРИЯ {comment['id']}: {e}")

                    offset += 100
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            logging.error(f"ОШИБКА ПРИ ПОЛУЧЕНИИ КОММЕНТАРИЕВ: {e}")
            break

async def kick_all_members(session, token, chat_id, login, chat_title, proxy):
    url_get_conversation_members = 'https://api.vk.com/method/messages.getConversationMembers'
    url_get_user = 'https://api.vk.com/method/users.get'
    url_remove_chat_user = 'https://api.vk.com/method/messages.removeChatUser'

    params_get_conversation_members = {
        'access_token': token,
        'v': '5.131',
        'peer_id': 2000000000 + chat_id
    }

    params_get_user = {
        'access_token': token,
        'v': '5.131'
    }

    async with session.get(url_get_conversation_members, params=params_get_conversation_members, proxy=proxy) as response:
        if response.status == 200:
            result = await response.json()
            admins = result['response']['items']
            admin_ids = [admin['member_id'] for admin in admins if 'is_admin' in admin and admin['is_admin']]

    async with session.get(url_get_user, params=params_get_user) as response:
        if response.status == 200:
            result = await response.json()
            current_user_id = result['response'][0]['id']

    if current_user_id not in admin_ids:
        logging.error(f"ЛОГИН {login} НЕ ИМЕЕТ ПРАВ АДМИНИСТРАТОРА В БЕСЕДЕ {chat_title}")
        return

    members = await reg.get_chat_members(session, token, chat_id, proxy)

    if current_user_id not in members:
        logging.error(f"ЛОГИНА {login} НЕТ В БЕСЕДЕ {chat_title}")
        return

    for member_id in members:
        if member_id == current_user_id:
            continue
        try:
            user_info = await reg.get_user_info(session, token, member_id, proxy)
            user_name = f"{user_info['first_name']} {user_info['last_name']}"
            params_remove_chat_user = {
                'access_token': token,
                'v': '5.131',
                'chat_id': chat_id,
                'member_id': member_id
            }
            async with session.post(url_remove_chat_user, params=params_remove_chat_user, proxy=proxy) as response:
                result = await response.json()
                if 'error' not in result:
                    print_white(f"ЛОГИН {login} КИКНУЛ УЧАСТНИКА {user_name} ИЗ БЕСЕДЫ {chat_title}")
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ КИКЕ УЧАСТНИКА ИЗ БЕСЕДЫ: {error_code} - {error_msg}")
                await asyncio.sleep(0.33)

        except aiohttp.ClientError as e:
            print_white(f"ОШИБКА ПРИ КИКЕ ПОЛЬЗОВАТЕЛЯ {user_name} ИЗ БЕСЕДЫ {chat_title}: {e}")

async def delete_photo_album(session, token, photo, login, album_name, group_name, owner_id, proxy):
    url = 'https://api.vk.com/method/photos.delete'
    params = {
        'access_token': token,
        'v': '5.131',
        'owner_id': owner_id,
        'photo_id': photo['id']
    }

    try:
        async with session.post(url, params=params, proxy=proxy) as response:
            if response.status == 200:
                result = await response.json()
                if 'error' not in result:
                    photo_name = photo['text'] if photo['text'] else f"photo_{photo['id']}"
                    print_white(f"ЛОГИН {login} УДАЛИЛ ФОТО {photo_name} ИЗ АЛЬБОМА {album_name} В ГРУППЕ {group_name}")
                else:
                    error_code = result['error']['error_code']
                    error_msg = result['error']['error_msg']
                    logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ФОТОГРАФИИ ИЗ АЛЬБОМА: {error_code} - {error_msg}")
            await asyncio.sleep(0.33)

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБОЧКА ПРИ УДАЛЕНИИ ФОТО {photo_name} ДЛЯ ЛОГИНА {login}: {e}")