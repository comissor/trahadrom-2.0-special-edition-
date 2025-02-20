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

async def upload_photo(session, token, upload_url, album_id, group_id, photo_path, login, album_name, group_name, proxy, description=None):
    url_photos_save = 'https://api.vk.com/method/photos.save'
    
    try:
        with open(photo_path, 'rb') as photo_file:
            data = aiohttp.FormData()
            data.add_field('file1', photo_file, filename=os.path.basename(photo_path))
            async with session.post(upload_url, data=data, proxy=proxy) as response:  
                response_json = await response.json()

        params_photos_save = {
            'album_id': album_id,
            'group_id': group_id,
            'server': response_json['server'],
            'photos_list': response_json['photos_list'],
            'hash': response_json['hash'],
            'caption': description or '',
            'access_token': token,  
            'v': '5.131'
        }
        async with session.post(url_photos_save, params=params_photos_save, proxy=proxy) as save_response:
            save_result = await save_response.json()
            if 'error' not in save_result:
                pass
            else:
                error_code = save_result['error']['error_code']
                error_msg = save_result['error']['error_msg']
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
                    logging.error(f"ОШИБКА VK API ПРИ ЗАГРУЗКЕ ФОТОГРАФИИ В ФОТОАЛЬБОМ: {error_code} - {error_msg}")
                    return

            if description:
                print_white(f"ЛОГИН {login} ЗАГРУЗИЛ {os.path.basename(photo_path)} В ФОТОАЛЬБОМ {album_name} В ГРУППЕ {group_name} С ОПИСАНИЕМ: {description}")
            else:
                print_white(f"ЛОГИН {login} ЗАГРУЗИЛ {os.path.basename(photo_path)} В ФОТОАЛЬБОМ {album_name} В ГРУППЕ {group_name}")

    except aiohttp.ClientError as e:
        logging.error(f"ОШИБКА СОЕДИНЕНИЯ: {e}")