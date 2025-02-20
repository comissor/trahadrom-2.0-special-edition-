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

async def send_report_pol(session, token, login, user_id, complaint_type, comment, user_name, proxy):
    params = {
        'user_id': user_id,
        'type': complaint_type,
        'comment': comment,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/users.report', params=params, proxy=proxy) as response:
        result = await response.json()
        if comment:
            print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {complaint_type} НА ПОЛЬЗОВАТЕЛЯ {user_name} С КОММЕНТАРИЕМ: {comment}")
        else:
            print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {complaint_type} НА ПОЛЬЗОВАТЕЛЯ {user_name}")
        print_white(result)

async def send_wall_report(session, token, login, owner_id, post_id, reason, proxy):
    params = {
        'owner_id': owner_id,
        'post_id': post_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/wall.reportPost', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление',
            '8': 'призывы к суициду'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА ПОСТ С ID: {post_id}")
        print_white(result)

async def send_wall_comment_report(session, token, login, owner_id, comment_id, reason, proxy):
    params = {
        'owner_id': owner_id,
        'comment_id': comment_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/wall.reportComment', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление',
            '8': 'призывы к суициду'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА КОММЕНТАРИЙ С ID: {comment_id}")
        print_white(result)

async def send_video_report(session, token, login, video_id, reason, comment, proxy):
    owner_id, video_id = video_id.split('_')
    params = {
        'owner_id': owner_id,
        'video_id': video_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    if comment:
        params['comment'] = comment
    async with session.post('https://api.vk.com/method/video.report', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление'
        }.get(reason, 'неизвестная причина')
        if comment:
            print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА ВИДЕО С ID: {video_id} С КОММЕНТАРИЕМ: {comment}")
        else:
            print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА ВИДЕО С ID: {video_id}")
        print_white(result)

async def send_video_comment_report(session, token, login, owner_id, comment_id, reason, comment, proxy):
    params = {
        'owner_id': owner_id,
        'comment_id': comment_id,
        'reason': reason,
        'comment': comment,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/video.reportComment', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА КОММЕНТАРИЙ К ВИДЕО С ID: {comment_id} С КОММЕНТАРИЕМ: {comment}")
        print_white(result)

async def send_photo_report(session, token, login, photo_id, reason, proxy):
    owner_id, photo_id = photo_id.split('_')
    params = {
        'owner_id': owner_id,
        'photo_id': photo_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/photos.report', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА ФОТО С ID: {photo_id}")
        print_white(result)

async def send_photo_comment_report(session, token, login, owner_id, comment_id, reason, proxy):
    params = {
        'owner_id': owner_id,
        'comment_id': comment_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/photos.reportComment', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА КОММЕНТАРИЙ К ФОТО С ID: {comment_id}")
        print_white(result)

async def send_market_report(session, token, login, item_id, owner_id, reason, proxy):
    params = {
        'owner_id': owner_id,
        'item_id': item_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/market.report', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА ТОВАР С ID: {item_id}")
        print_white(result)

async def send_market_comment_report(session, token, login, owner_id, comment_id, reason, proxy):
    params = {
        'owner_id': owner_id,
        'comment_id': comment_id,
        'reason': reason,
        'access_token': token,
        'v': '5.131'
    }
    async with session.post('https://api.vk.com/method/market.reportComment', params=params, proxy=proxy) as response:
        result = await response.json()
        reason_text = {
            '0': 'спам',
            '1': 'детская порнография',
            '2': 'экстремизм',
            '3': 'насилие',
            '4': 'пропаганда наркотиков',
            '5': 'материал для взрослых',
            '6': 'оскорбление'
        }.get(reason, 'неизвестная причина')
        print_white(f"С ЛОГИНА {login} ОТПРАВЛЕНА ЖАЛОБА С ПРИЧИНОЙ {reason_text} НА КОММЕНТАРИЙ К ТОВАРУ С ID: {comment_id}")
        print_white(result)