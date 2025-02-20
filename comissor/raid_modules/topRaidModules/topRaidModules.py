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

async def groups_create(session, token, login, title, type_group, description, subtype, proxy):
    url = "https://api.vk.com/method/groups.create"
    params = {
        "access_token": token,
        "v": "5.131",
        "title": title,
        "type": type_group,
        'subtype': subtype,
        "description": description
    }

    try:
        async with session.post(url, data=params, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                group_id = result['response']['id']
                print_white(f"ГРУППА С ID: {group_id} УСПЕШНО СОЗДАНА НА ЛОГИНЕ {login}")
            else:
                error_code = result['error']['error_code']
                error_msg = result['error']['error_msg']
                logging.error(f"ОШИБКА VK API ПРИ СОЗДАНИИ ГРУППЫ: {error_code} - {error_msg}")

    except aiohttp.ClientError as e:
        print_white(f"ОШИБКА: {e}")

async def edit_group(session, token, login, group_name, group_id, proxy, **kwargs):
    url = "https://api.vk.com/method/groups.edit"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        **kwargs  
    }

    async with session.post(url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО ИЗМЕНИЛ ЗАДАННЫЕ ПАРАМЕТРЫ ГРУППЫ {group_name} ID: {group_id}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ РЕДАКТИРОВАНИИ ПАРАМЕТРОВ ГРУППЫ: {error_code} - {error_msg}")

async def upload_group_avatar(session, token, login, group_id, group_name, avatar_name, image_path, proxy):
    url = "https://api.vk.com/method/photos.getOwnerPhotoUploadServer"
    params = {
        "access_token": token,
        "v": "5.131",
        "owner_id": -int(group_id)
    }
    async with session.get(url, params=params, proxy=proxy) as response:
        result = await response.json()
        upload_url = result["response"]["upload_url"]

    with open(image_path, "rb") as image_file:
        data = aiohttp.FormData()
        data.add_field("photo", image_file, filename="avatar.jpg")
        async with session.post(upload_url, data=data) as response:
            result = await response.json()
            photo_data = result["photo"]
            server = result["server"]
            hash = result["hash"]

    url = "https://api.vk.com/method/photos.saveOwnerPhoto"
    params = {
        "access_token": token,
        "v": "5.131",
        "photo": photo_data,
        "server": server,
        "hash": hash
    }
    async with session.post(url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО УСТАНОВИЛ АВАТАРКУ {avatar_name} В ГРУППЕ {group_name} ID: {group_id}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ РЕДАКТИРОВАНИИ АВАТАРКИ ГРУППЫ: {error_code} - {error_msg}")

async def edit_group_cover(session, token, login, group_id, group_name, cover_name, image_path, proxy):
    url = "https://api.vk.com/method/photos.getOwnerCoverPhotoUploadServer"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        "crop_x": 0,  
        "crop_y": 0,
        "crop_x2": 1590,  
        "crop_y2": 400   
    }
    async with session.get(url, params=params, proxy=proxy) as response:
        result = await response.json()
        upload_url = result["response"]["upload_url"]

    with open(image_path, "rb") as image_file:
        data = aiohttp.FormData()
        data.add_field("photo", image_file, filename="cover.jpg")
        async with session.post(upload_url, data=data) as response:
            result = await response.json()
            cover_data = result

    url = "https://api.vk.com/method/groups.edit"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        "cover": cover_data  
    }
    async with session.post(url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО УСТАНОВИЛ ОБЛОЖКУ {cover_name} В ГРУППЕ {group_name} ID: {group_id}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ РЕДАКТИРОВАНИИ ОБЛОЖКИ ГРУППЫ: {error_code} - {error_msg}")

async def delete_all_photos_group(session, token, login, group_id, group_name, proxy):
    offset = 0
    count = 200

    while True:
        url = "https://api.vk.com/method/photos.getAll"
        params = {
            "access_token": token,
            "v": "5.131",
            "owner_id": -int(group_id), 
            "count": count,
            "offset": offset,
            "no_service_albums": 0  
        }
        async with session.get(url, params=params, proxy=proxy) as response:
            result = await response.json()
            if "response" in result and "items" in result["response"]:
                photos = result["response"]["items"]

                for photo in photos:
                    photo_id = photo["id"]
                    url = "https://api.vk.com/method/photos.delete"
                    params = {
                        "access_token": token,
                        "v": "5.131",
                        "owner_id": -int(group_id),  
                        "photo_id": photo_id
                    }
                    async with session.post(url, data=params, proxy=proxy) as response:
                        result = await response.json()
                        if 'error' not in result:
                            print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ ФОТОГРАФИЮ photo_{photo_id} В ГРУППЕ {group_name}")
                        else:
                            error_code = result['error']['error_code']
                            error_msg = result['error']['error_msg']
                            logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ФОТОГРАФИИ В ГРУППЕ: {error_code} - {error_msg}")

                if len(photos) < count:
                    break 
                offset += count

async def delete_all_discussions_group(session, token, login, group_id, group_name, proxy):
    offset = 0
    count = 100

    while True:
        url = "https://api.vk.com/method/board.getTopics"
        params = {
            "access_token": token,
            "v": "5.131",
            "group_id": group_id,
            "count": count,
            "offset": offset,
            "extended": 0  
        }
        async with session.get(url, params=params, proxy=proxy) as response:
            result = await response.json()
            if "response" in result and "items" in result["response"]:
                topics = result["response"]["items"]

                for topic in topics:
                    topic_id = topic["id"]
                    url = "https://api.vk.com/method/board.deleteTopic"
                    params = {
                        "access_token": token,
                        "v": "5.131",
                        "group_id": group_id,
                        "topic_id": topic_id
                    }
                    async with session.post(url, data=params, proxy=proxy) as response:
                        result = await response.json()
                        if 'error' not in result:
                            print_white(f"ЛОГИН {login} УСПЕШНО УДАЛИЛ ТОПИК С ID: {topic_id} В ГРУППЕ {group_name}")
                        else:
                            error_code = result['error']['error_code']
                            error_msg = result['error']['error_msg']
                            logging.error(f"ОШИБКА VK API ПРИ УДАЛЕНИИ ТОПИКА В ГРУППЕ: {error_code} - {error_msg}")
                        
                if len(topics) < count:
                    break 
                offset += count

async def ban_all_members_group_comment(session, token, login, group_id, group_name, reason, comment, comment_visible, proxy):
    offset = 0
    count = 1000 

    while True:
        url = "https://api.vk.com/method/groups.getMembers"
        params = {
            "access_token": token,
            "v": "5.131",
            "group_id": group_id,
            "count": count,
            "offset": offset
        }
        async with session.get(url, params=params, proxy=proxy) as response:
            result = await response.json()
            if "response" in result and "items" in result["response"]:
                members = result["response"]["items"]

                for member in members:
                    member_id = member
                    url = "https://api.vk.com/method/groups.ban"
                    params = {
                        "access_token": token,
                        "v": "5.131",
                        "group_id": group_id,
                        "owner_id": member_id,
                        "reason": reason,  
                        "comment": comment or '',
                        "comment_visible": comment_visible 
                    }
                    async with session.post(url, data=params, proxy=proxy) as response:
                        result = await response.json()
                        if 'error' not in result:
                            print_white(f"ЛОГИН {login} УСПЕШНО ЗАБАНИЛ УЧАСТНИКА С ID: {member_id} В ГРУППЕ {group_name}")
                        else:
                            error_code = result['error']['error_code']
                            error_msg = result['error']['error_msg']
                            logging.error(f"ОШИБКА VK API ПРИ БАНЕ УЧАСТНИКА В ГРУППЕ: {error_code} - {error_msg}")

                if len(members) < count:
                    break  
                offset += count

async def ban_all_members_group(session, token, login, group_id, group_name, reason, proxy):
    offset = 0
    count = 1000 

    while True:
        url = "https://api.vk.com/method/groups.getMembers"
        params = {
            "access_token": token,
            "v": "5.131",
            "group_id": group_id,
            "count": count,
            "offset": offset
        }
        async with session.get(url, params=params, proxy=proxy) as response:
            result = await response.json()
            if "response" in result and "items" in result["response"]:
                members = result["response"]["items"]

                for member in members:
                    member_id = member
                    url = "https://api.vk.com/method/groups.ban"
                    params = {
                        "access_token": token,
                        "v": "5.131",
                        "group_id": group_id,
                        "owner_id": member_id,
                        "reason": reason
                    }
                    async with session.post(url, data=params, proxy=proxy) as response:
                        result = await response.json()
                        if 'error' not in result:
                            print_white(f"ЛОГИН {login} УСПЕШНО ЗАБАНИЛ УЧАСТНИКА С ID: {member_id} В ГРУППЕ {group_name}")
                        else:
                            error_code = result['error']['error_code']
                            error_msg = result['error']['error_msg']
                            logging.error(f"ОШИБКА VK API ПРИ БАНЕ УЧАСТНИКА В ГРУППЕ: {error_code} - {error_msg}")

                if len(members) < count:
                    break  
                offset += count

async def group_edit_callback(session, token, login, group_id, group_name, server_id, proxy):
    api_url = "https://api.vk.com/method/groups.setCallbackSettings"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        "server_id": server_id,
        "api_version": "5.131",
        "message_new": 1, 
        "message_reply": 1,
        "message_allow": 1,
        "message_edit": 1,
        "message_deny": 1,
        "message_typing_state,": 1,
        "photo_new": 1,
        "audio_new": 1,
        "video_new": 1,
        "wall_reply_new": 1,
        "wall_reply_edit": 1,
        "wall_reply_delete": 1,
        "wall_reply_restore": 1,
        "wall_post_new": 1,
        "wall_repost": 1,
        "board_post_new": 1,
        "board_post_edit": 1,
        "board_post_restore": 1,
        "board_post_delete": 1,
        "photo_comment_new": 1,
        "photo_comment_edit": 1,
        "photo_comment_delete": 1,
        "photo_comment_restore": 1,
        "video_comment_new": 1,
        "video_comment_edit": 1,
        "video_comment_delete": 1,
        "video_comment_restore": 1,
        "market_comment_new": 1,
        "market_comment_edit": 1,
        "market_comment_delete": 1,
        "market_comment_restore": 1,
        "poll_vote_new": 1,
        "group_join": 1,
        "group_leave": 1,
        "group_change_settings": 1,
        "group_change_photo": 1,
        "group_officers_edit": 1,
        "user_block": 1,
        "user_unblock": 1,
        "like_add": 1,
        "like_remove": 1,
        "message_read": 1,
        "market_order_new": 1,
        "market_order_edit": 1,
        "message_event": 1,
        "message_reaction_event": 1,
        "message_typing_state": 1
    }
    async with session.post(api_url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО ИЗМЕНИЛ CALLBACK API НАСТРОЙКИ ГРУППЫ {group_name}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ CALLBACK API НАСТРОЕК ГРУППЫ: {error_code} - {error_msg}")

async def group_edit_longpoll(session, token, login, group_id, group_name, proxy):
    api_url = "https://api.vk.com/method/groups.setLongPollSettings"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        "enabled": 1,
        "api_version": "5.131",
        "message_new": 1, 
        "message_reply": 1,
        "message_allow": 1,
        "message_edit": 1,
        "message_deny": 1,
        "message_typing_state,": 1,
        "photo_new": 1,
        "audio_new": 1,
        "video_new": 1,
        "wall_reply_new": 1,
        "wall_reply_edit": 1,
        "wall_reply_delete": 1,
        "wall_reply_restore": 1,
        "wall_post_new": 1,
        "wall_repost": 1,
        "board_post_new": 1,
        "board_post_edit": 1,
        "board_post_restore": 1,
        "board_post_delete": 1,
        "photo_comment_new": 1,
        "photo_comment_edit": 1,
        "photo_comment_delete": 1,
        "photo_comment_restore": 1,
        "video_comment_new": 1,
        "video_comment_edit": 1,
        "video_comment_delete": 1,
        "video_comment_restore": 1,
        "market_comment_new": 1,
        "market_comment_edit": 1,
        "market_comment_delete": 1,
        "market_comment_restore": 1,
        "poll_vote_new": 1,
        "group_join": 1,
        "group_leave": 1,
        "group_change_settings": 1,
        "group_change_photo": 1,
        "group_officers_edit": 1,
        "user_block": 1,
        "user_unblock": 1,
        "like_add": 1,
        "like_remove": 1,
        "message_read": 1,
        "market_order_new": 1,
        "market_order_edit": 1,
        "message_event": 1,
        "message_reaction_event": 1,
        "message_typing_state": 1
    }
    async with session.post(api_url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО ИЗМЕНИЛ LONGPOLL API НАСТРОЙКИ ГРУППЫ {group_name}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ LONGPOLL API НАСТРОЕК ГРУППЫ: {error_code} - {error_msg}")

async def group_edit_raid_settings(session, token, login, group_id, group_name, proxy):
    api_url = "https://api.vk.com/method/groups.setSettings"
    params = {
        "access_token": token,
        "v": "5.131",
        "group_id": group_id,
        "messages": 1,
        "bots_capabilities": 1,
        "bots_add_to_chat": 1
    }
    async with session.post(api_url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО ИЗМЕНИЛ РЕЙД-НАСТРОЙКИ ГРУППЫ {group_name}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ ИЗМЕНЕНИИ РЕЙД-НАСТРОЕК ГРУППЫ: {error_code} - {error_msg}")

async def groups_invite(session, token, login, chat_id, chat_title, group_id, group_name, proxy):
    url = 'https://api.vk.com/method/bot.addBotToChat'
    params = {
        'v': '5.131',
        'access_token': token,
        'peer_id': 2000000000 + chat_id,
        'bot_id': -int(group_id)
    }
    async with session.post(url, data=params, proxy=proxy) as response:
        result = await response.json()
        if 'error' not in result:
            print_white(f"ЛОГИН {login} УСПЕШНО ДОБАВИЛ РЕЙД-ГРУППУ {group_name} В БЕСЕДУ {chat_title}")
        else:
            error_code = result['error']['error_code']
            error_msg = result['error']['error_msg']
            logging.error(f"ОШИБКА VK API ПРИ ДОБАВЛЕНИИ РЕЙД-ГРУППЫ В БЕСЕДУ: {error_code} - {error_msg}")

async def beseda_zov(session, token, login, zov, chat_id, chat_title, photo_folder, attach_file, use_attach, use_photos, proxy):
    url_messages_send = 'https://api.vk.com/method/messages.send'
    url_photos_get_messages_upload_server = 'https://api.vk.com/method/photos.getMessagesUploadServer'
    url_photos_save_messages_photo = 'https://api.vk.com/method/photos.saveMessagesPhoto'
    url_docs_get_messages_upload_server = 'https://api.vk.com/method/docs.getMessagesUploadServer'
    url_docs_save = 'https://api.vk.com/method/docs.save'

    try:
        if use_attach:
            attach = read_messages(attach_file)
        else:
            attach = ''

        attachment = attach or ''
        photo_name = ''
        if use_photos:
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
                params_get_upload_server = {'access_token': token, 'v': '5.131', 'peer_id': 2000000000 + chat_id}
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
            'message': zov or '',
            'attachment': attachment,
            'random_id': random.randint(1, 999999),
            'access_token': token,
            'v': '5.131'
        }
        async with session.post(url_messages_send, params=params_send, proxy=proxy) as response:
            result = await response.json()
            if 'error' not in result:
                pass
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
                    logging.error(f"ОШИБКА VK API ПРИ ОТПРАВКЕ СООБЩЕНИЯ: {error_code} - {error_msg}")

        if zov and use_photos and attach:
            print_white(f"ЛОГИН {login} ОТПРАВИЛ ЗОВ {zov}, ФОТОГРАФИЮ ИЛИ ГИФКУ - {photo_name}, ВЛОЖЕНИЕМ - {attach} В БЕСЕДЕ {chat_title}")
        elif zov and use_photos:
            print_white(f"ЛОГИН {login} ОТПРАВИЛ ЗОВ {zov}, ФОТОГРАФИЮ ИЛИ ГИФКУ - {photo_name} В БЕСЕДЕ {chat_title}")
        elif zov and attach:
            print_white(f"ЛОГИН {login} ОТПРАВИЛ ЗОВ {zov}, ВЛОЖЕНИЕМ - {attach} В БЕСЕДЕ {chat_title}")
        elif zov:
            print_white(f"ЛОГИН {login} ОТПРАВИЛ ЗОВ {zov} В БЕСЕДЕ {chat_title}")

    except Exception as e:
        logging.error(f"ОШИБОЧКА: {e}")

