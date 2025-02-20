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
user_cache = {}
group_cache = {}
conversation_cache = {}
subscription_cache = {}
video_cache = {}

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def input_white(prompt):
    print("\033[97m" + prompt + "\033[1m", end="")
    return input()

def print_white(text):
    print(f"{WHITE}{BOLD}{text}{RESET}")

async def find_group_chats_links(session, token, start_time, end_time, post_count, proxy, keyword=None):
    url_newsfeed_search = 'https://api.vk.com/method/newsfeed.search'
    unique_links = set()
    num_requests = (post_count - 1) // 200 + 1

    try:
        for _ in range(num_requests):
            batch_count = min(post_count, 200)
            search_query = f"vk.me/join {keyword}" if keyword else "vk.me/join"
            params = {
                'q': search_query,
                'count': batch_count,
                'access_token': token,
                'v': '5.131',
                'start_time': start_time,
                'end_time': end_time
            }
            async with session.get(url_newsfeed_search, params=params, proxy=proxy) as response:
                if response.status == 200:
                    search_results = await response.json()
                    for item in search_results.get('response', {}).get('items', []):
                        if 'text' in item:
                            text = item['text']
                            chat_links = re.findall(r'vk\.me/join/[A-Za-z0-9/=_-]+', text)
                            unique_links.update(chat_links)

                await asyncio.sleep(0.33)
            post_count -= batch_count

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА: {e}")

    return list(unique_links)

async def parser_messenger(session, login, token, count, proxy):
    dialogs = await reg.get_dialogs(session, token, count, proxy)
    base_path = os.path.join("parser", login)
    os.makedirs(base_path, exist_ok=True)
    picture_path = os.path.join(base_path, "pictures")
    os.makedirs(picture_path, exist_ok=True)

    for dialog in dialogs:
        peer_id = dialog["conversation"]["peer"]["id"]
        user_name = await reg.get_conversation_info(session, token, peer_id, proxy)
        dialog_file_path = os.path.join(base_path, f"{login} диалог в или с {user_name}.txt")
        picture_file_path = os.path.join(picture_path, f"{login} прикрепленные картинки в или с {user_name}.txt")

        async with aiofiles.open(dialog_file_path, "w", encoding="utf-8") as dialog_file, \
                aiofiles.open(picture_file_path, "w", encoding="utf-8") as picture_file:
            offset = 0
            while True:
                history = await reg.get_history(session, token, peer_id, proxy, count=200) 
                messages = history
                if not messages:
                    break

                for message in messages:
                    timestamp = datetime.fromtimestamp(message["date"]).strftime('%d.%m.%Y %H:%M')
                    text = message.get("text", "")
                    user_id = message["from_id"]
                    user_name = await reg.get_info(session, token, user_id, proxy) 
                    await dialog_file.write(f"{timestamp} | {user_name}: {text}\n")

                    attachments = message.get("attachments", [])
                    for attachment in attachments:
                        if attachment["type"] == "photo":
                            photo_url = attachment["photo"]["sizes"][-1]["url"]
                            await picture_file.write(f"{photo_url}\n")
                            await dialog_file.write(f"{timestamp} | {user_name} прикрепил фото: {photo_url}\n")

                if len(messages) < 200:
                    break
                offset += 200

async def parser_profile(session, token, user_id, proxy):
    user_info = await reg.get_user_info(session, token, user_id, proxy)
    user_name = f"{user_info['first_name']} {user_info['last_name']}"
    base_path = os.path.join("parser/users", sanitize_filename(user_name))
    os.makedirs(base_path, exist_ok=True)

    paths = {
        "friends": os.path.join(base_path, "friends"),
        "groups": os.path.join(base_path, "groups"),
        "videos": os.path.join(base_path, "videos"),
        "subscriptions": os.path.join(base_path, "subscriptions"),
        "photos": os.path.join(base_path, "photos"),
        "posts": os.path.join(base_path, "posts")
    }
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    friends = await reg.get_friends(session, token, user_id, proxy)
    async with aiofiles.open(os.path.join(paths["friends"], "friends.txt"), "w", encoding="utf-8") as f:
        for friend in friends:
            await f.write(f"{friend['first_name']} {friend['last_name']} - https://vk.com/id{friend['id']}\n")

    groups = await reg.get_user_groups(session, user_id, token, proxy)
    async with aiofiles.open(os.path.join(paths["groups"], "groups.txt"), "w", encoding="utf-8") as f:
        for group_data in groups:
            group_id = group_data['id']
            await f.write(f"https://vk.com/club{group_id}\n")

    videos = await reg.get_videos(session, token, user_id, proxy)
    async with aiofiles.open(os.path.join(paths["videos"], "videos.txt"), "w", encoding="utf-8") as f:
        for video in videos:
            await f.write(f"https://vk.com/video{video['owner_id']}_{video['id']}\n")

    subscriptions = await reg.get_subscriptions(session, token, user_id, proxy)
    async with aiofiles.open(os.path.join(paths["subscriptions"], "subscriptions.txt"), "w", encoding="utf-8") as f:
        for subscription in subscriptions:
            if subscription.get('type') == 'page':  
                await f.write(f"https://vk.com/{subscription['screen_name']}\n")
            elif subscription.get('type') == 'group':
                await f.write(f"https://vk.com/club{subscription['id']}\n")
            elif subscription.get('type') == 'user':
                await f.write(f"https://vk.com/id{subscription['id']}\n")

    photos = await reg.get_photos(session, token, user_id, proxy)
    for photo in photos:
        photo_url = photo['sizes'][-1]['url']
        photo_name = os.path.join(paths["photos"], f"{photo['id']}.jpg")
        await reg.download_photo(session, photo_url, photo_name, proxy)

    avatar_url = user_info['photo_max_orig']
    avatar_path = os.path.join(base_path, "avatar.jpg")
    await reg.download_photo(session, avatar_url, avatar_path, proxy)

    posts = await reg.get_wall_posts(session, token, user_id, proxy)
    async with aiofiles.open(os.path.join(paths["posts"], "posts.txt"), "w", encoding="utf-8") as f:
        for post in posts:
            await f.write(f"https://vk.com/wall{post['owner_id']}_{post['id']}\n")

async def parser_group(session, token, group_id, proxy):
    group_info = await reg.get_group_info(session, token, group_id, proxy)
    group_name = group_info['name']
    base_path = os.path.join("parser/groups", sanitize_filename(group_name))
    os.makedirs(base_path, exist_ok=True)

    paths = {
        "members": os.path.join(base_path, "members"),
        "wall_posts": os.path.join(base_path, "wall_posts"),
        "photos": os.path.join(base_path, "photos"),
        "videos": os.path.join(base_path, "videos"),
        "contacts": os.path.join(base_path, "contacts"),
        "discussions": os.path.join(base_path, "discussions")
    }
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    members = await reg.get_group_members(session, token, group_id, proxy)
    async with aiofiles.open(os.path.join(paths["members"], "members.txt"), "w", encoding="utf-8") as f:
        for member in members:
            await f.write(f"https://vk.com/id{member}\n")

    wall_posts = await reg.get_group_wall_posts(session, token, group_id, proxy)
    async with aiofiles.open(os.path.join(paths["wall_posts"], "wall_posts.txt"), "w", encoding="utf-8") as f:
        for post in wall_posts:
            await f.write(f"https://vk.com/wall-{group_id}_{post['id']}\n")

    photos = await reg.get_group_photos(session, token, group_id, proxy)
    for photo in photos:
        photo_url = photo['sizes'][-1]['url']
        photo_name = os.path.join(paths["photos"], f"{photo['id']}.jpg")
        await reg.download_photo(session, photo_url, photo_name, proxy)

    avatar_url = group_info['photo_max']
    avatar_path = os.path.join(base_path, "avatar.jpg")
    await reg.download_photo(session, avatar_url, avatar_path, proxy)

    videos = await reg.get_group_videos(session, token, group_id, proxy)
    async with aiofiles.open(os.path.join(paths["videos"], "videos.txt"), "w", encoding="utf-8") as f:
        for video in videos:
            await f.write(f"https://vk.com/video{video['owner_id']}_{video['id']}\n")

    contacts = await reg.get_group_contacts(session, token, group_id, proxy)
    async with aiofiles.open(os.path.join(paths["contacts"], "contacts.txt"), "w", encoding="utf-8") as f:
        for contact in contacts:
            await f.write(f"{contact['user_id']} - {contact['desc']}\n")

    discussions = await reg.get_group_discussions(session, token, group_id, proxy)
    async with aiofiles.open(os.path.join(paths["discussions"], "discussions.txt"), "w", encoding="utf-8") as f:
        for discussion in discussions:
            await f.write(f"https://vk.com/topic-{group_id}_{discussion['id']}\n")