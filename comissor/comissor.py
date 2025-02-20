import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'raid_modules', 'raidGroup'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'raid_modules', 'raidPol'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'raid_modules', 'raidBeseda'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'raid_modules', 'topRaidModules'))
import asyncio
import json
import logging
import random
import re
import ssl
import subprocess
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
import raidGroup as raidGroup_module
import topRaidModules as topRaid_module
from raid_modules import besedi as besedi_module
from raid_modules import parser as parser_module
from raid_modules import reports as reports_module
from raid_utils import friends as friends_module
from raid_utils import profile as profile_module
from raid_utils import reg
from raid_utils import utils as utils_module
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

def display_skull():
    skull = [
        "                               ТРАХАДРОМ 2.0 special edition           ",
        "██░└┐░░░░░░░░░░░░░░░░░┌┘░██                                            ", 
        "██░░┌┘▄▄▄▄▄░░░░░▄▄▄▄▄└┐░░██                                            ",  
        "██▌░│██████▌░░░▐██████│░▐██                                            ",
        "███░│▐███▀▀░░▄░░▀▀███▌│░███    ЕБЕМ ВКОНТАКТЕ ВО ВСЕ ДЫРЫ              ",
        "██▀─┘░░░░░░░▐█▌░░░░░░░└─▀██    by comissor                             ",                                                                  
        "██▄░░░▄▄▄▓░░▀█▀░░▓▄▄▄░░░▄██    author TG - @vladikmakarov              ",
        "████▄─┘██▌░░░░░░░▐██└─▄████    УНИЧТОЖАЕМ ВСЕ К ХУЯМ                   ",
        "█████░░▐█─┬┬┬┬┬┬┬─█▌░░█████                                            ",
        "████▌░░░▀┬┼┼┼┼┼┼┼┬▀░░░▐████                                            ",
        "█████▄░░░└┴┴┴┴┴┴┴┘░░░▄█████                                            "
    ]
    for line in skull:
        print_white(line)

def main_menu():
    theme_state = reg.load_theme_state()
    manager_state = reg.load_manager_state()
    headers = reg.load_headers()
    proxy = reg.load_proxy()
    print_white("[РЕЙД-КОНФИГ]:")
    print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
    print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
    print_white("[БАЗА ДАННЫХ]:")
    print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
    print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
    print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
    print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
    print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
    print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
    print_white("[РЕЙД-МЕНЮ]:")
    print_white("0. КОНФИГ")
    print_white("1. РЕЙД ПОЛЬЗОВАТЕЛЯ")
    print_white("2. РЕЙД ГРУППЫ")
    print_white("3. РЕЙД БЕСЕДЫ")
    print_white("4. РЕЙД МЕДИА")
    print_white("5. СИСТЕМА РЕПОРТОВ")
    print_white("6. ПАРСЕР-ХУЯРСЕР")
    print_white("7. ЗАЛЬГО-ТЕКСТ")
    print_white("8. РАБОТА С ДРУЗЬЯМИ")
    print_white("9. РАБОТА С БЕСЕДАМИ")
    print_white("10. РАБОТА С ПРОФИЛЯМИ")
    print_white("11. ТОТАЛЬНЫЙ РАЗЪЕБ")
    print_white("12. УТИЛИТЫ")
    print_white("13. ПОЙТИ НАХУЙ")

async def trahadrom():
    display_skull()
    input_white("НАЖИМАЙ ENTER ИЛИ ПИЗДУЙ НАХУЙ")
    while True:
        main_menu()
        choice = input_white("ВЫБИРАЙ БЛЯ: ")

        if choice == "0":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. ПРОВЕРКА АККАУНТОВ НА ВАЛИДНОСТЬ")
                print_white("2. ПРОВЕРКА ТОКЕНОВ НА ВАЛИДНОСТЬ")
                print_white("3. ПОЛУЧЕНИЕ ТОКЕНОВ НА АККАУНТЫ")
                print_white("4. ПОЛУЧЕНИЕ BotPod ТОКЕНОВ ")
                print_white("5. ПОЛУЧЕНИЕ ТОКЕНОВ НА ГРУППЫ")
                print_white("6. ЗАПИСЬ ТОКЕНОВ В БАЗУ ДАННЫХ")
                print_white("7. ПРОСМОТРЕТЬ ПРАВА ТОКЕНОВ ЮЗЕРОВ")
                print_white("8. ПРОСМОТРЕТЬ ПРАВА ТОКЕНОВ СООБЩЕСТВ")
                print_white("9. ПОЙТИ НАХУЙ")
                config = input_white("ВЫБИРАЙ БЛЯ: ")

                if config == "1":
                    filename = os.path.join(BASE_DIR, "accounts.txt")
                    await reg.check_accounts_validity(reg.read_accounts(filename), filename)
                elif config == "2":
                    filename = os.path.join(BASE_DIR, "tokens.txt")
                    await reg.check_tokens_validity(reg.read_tokens(filename), filename)
                elif config == "3":
                    await reg.get_tokens_for_accounts(reg.read_accounts(os.path.join(BASE_DIR, "accounts.txt")), 
                    reg.read_tokens(os.path.join(BASE_DIR, "tokens.txt")))
                elif config == "4":
                    accounts = reg.read_accounts(os.path.join('base', 'accounts.txt'))
                    botpod_tokens = [f"{login}:{reg.get_botpod_token(login, password)}" for login, password in accounts]

                    with open(os.path.join('base', 'BotPodTokens.txt'), 'w', encoding='utf-8') as file:
                        file.write('\n'.join(botpod_tokens))

                    print_white('ТОКЕНЫ BotPod УСПЕШНО ПОЛУЧЕНЫ И ЗАПИСАНЫ В ТЕКСТОВИК BotPodTokens.txt')
                elif config == "5":
                    tokens_data = reg.read_tokens(os.path.join(BASE_DIR, "tokens.txt"))
                    accounts = reg.read_accounts(os.path.join(BASE_DIR, "accounts.txt"))
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        group_tokens = []
                        for account in accounts:
                            login, password = account
                            token = tokens_data.get(login)
                            if token:
                                admin_groups = await reg.get_admin_groups(session, token, proxy)
                                for group_id in admin_groups:
                                    group_token = reg.get_group_token(login, password, group_id)
                                    group_info = await reg.get_group_info(session, token, group_id, proxy)
                                    group_type = group_info['type']
                                    if group_type == 'group':
                                        group_url = f'https://vk.com/club{group_id}'
                                    elif group_type == 'public':
                                        group_url = f'https://vk.com/public{group_id}'
                                    group_tokens.append(f'{group_token} - {group_url}')

                    with open(os.path.join(BASE_DIR, 'GroupsTokens.txt'), 'w', encoding='utf-8') as file:
                        file.write('\n'.join(group_tokens))

                    print_white('ТОКЕНЫ НА ГРУППЫ УСПЕШНО ПОЛУЧЕНЫ И ЗАПИСАНЫ В ТЕКСТОВЫЙ ФАЙЛ GroupsTokens.txt')
                elif config == "6":
                    user_tokens = reg.read_tokens(os.path.join('base', 'tokens.txt'))
                    botpod_tokens = reg.read_tokens(os.path.join('base', 'BotPodTokens.txt'))
                    group_tokens = reg.write_group_tokens(os.path.join('base', 'GroupsTokens.txt'))
                    reg.write_to_json(user_tokens, botpod_tokens, group_tokens, os.path.join('base', 'data.json'))
                    print_white('ТОКЕНЫ УСПЕШНО ЗАПИСАНЫ В ФАЙЛ data.json')
                elif config == "7":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        for login, token in tokens.items():
                            await reg.get_token_permissions_user(session, login, token, proxy)
                elif config == "8":
                    group_tokens = reg.read_group_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        for group_id, token in group_tokens.items():
                            await reg.get_token_permissions_community(session, group_id, token, proxy)
                elif config == "9":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "1":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. РЕЙД ЛИЧКИ")
                print_white("2. РЕЙД ЛИЧКИ ИСЧЕЗАЮЩИМИ СООБЩЕНИЯМИ")
                print_white("3. РЕЙД ЛИЧКИ СТИКЕРАМИ")
                print_white("4. РЕЙД СТЕНЫ ПОЛЬЗОВАТЕЛЯ")
                print_white("5. РЕЙД КОММЕНТОВ К ЗАПИСИ ПОЛЬЗОВАТЕЛЯ")
                print_white("6. ПОЙТИ НАХУЙ")
                polRaid = input_white("ВЫБИРАЙ БЛЯ: ")

                if polRaid == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    attach_file = "message/attach.txt"
                    user_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    user_id = reg.extract_user_id(user_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        message_file = select_message_file()
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_attach = True
                                break
                            elif user_input in ['no', 'n']:
                                use_attach = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В ЛС {user_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidPol/raidPol_pol.py', user_id, token, login, str(index), str(theme_state), message_file, photo_folder, str(use_photos), user_name, str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif polRaid == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    attach_file = "message/attach.txt"
                    user_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    expire_ttl = input_white("ВВЕДИ ВРЕМЯ ЧЕРЕЗ КОТОРОЕ УДАЛИТСЯ СООБЩЕНИЕ(В СЕКУНДАХ! 86400 = 24 ЧАСА|3600 = 1 ЧАС|300 = 5 МИНУТ|60 = 1 МИНУТА|15 СЕКУНД!): ")
                    user_id = reg.extract_user_id(user_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        message_file = select_message_file()
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_attach = True
                                break
                            elif user_input in ['no', 'n']:
                                use_attach = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В ЛС {user_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidPol/raidPol_poldel.py', user_id, token, login, str(index), str(theme_state), message_file, photo_folder, str(use_photos), user_name, str(expire_ttl), str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif polRaid == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    user_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    user_id = reg.extract_user_id(user_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        theme_state = reg.load_theme_state()
                        index = 1

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ СТИКЕРАМИ В ЛС {user_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidPol/raidPol_sticker.py', token, login, user_id, user_name, str(index), str(theme_state), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif polRaid == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    user_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    user_id = reg.extract_user_id(user_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        message_file = select_message_file()
                        owner_id = user_id
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ НА СТЕНУ ПОЛЬЗОВАТЕЛЯ {user_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidPol/raidPol_wall.py', owner_id, token, login, str(index), message_file, photo_folder, str(use_photos), user_name, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)        
                elif polRaid == "5":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    user_url = input_white("ВВЕДИ ССЫЛКУ НА ПОСТ: ")
                    user_id = reg.extract_user_id(user_url)
                    post_id = reg.extract_post_id(user_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        message_file = select_message_file()
                        owner_id = user_id
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В КОММЕНТАРИИ К ПОСТУ С ID: {post_id} НА СТЕНЕ ПОЛЬЗОВАТЕЛЯ {user_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidPol/raidPol_wall_comment.py', owner_id, post_id, token, login, str(index), message_file, photo_folder, str(use_photos), user_name, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif polRaid == "6":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "2":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. РЕЙД ЛИЧКИ ГРУППЫ")
                print_white("2. РЕЙД ЛИЧКИ ГРУППЫ СТИКЕРАМИ")
                print_white("3. РЕЙД СТЕНЫ ГРУППЫ /// ПРЕДЛОЖКИ ГРУППЫ")
                print_white("4. РЕЙД ТОПИКА")
                print_white("5. РЕЙД АЛЬБОМОВ")
                print_white("6. РЕЙД КОММЕНТОВ К ЗАПИСИ ГРУППЫ")
                print_white("7. ПОЙТИ НАХУЙ")
                groupRaid = input_white("ВЫБИРАЙ БЛЯ: ")

                if groupRaid == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    attach_file = "message/attach.txt"
                    group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID НА ГРУППЫ: ")
                    group_id = reg.extract_group_id(group_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        manager_state = reg.load_manager_state()
                        message_file = select_message_file()
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_attach = True
                                break
                            elif user_input in ['no', 'n']:
                                use_attach = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В ЛС ГРУППЫ {group_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidGroup/raidGroup_LS.py', group_id, token, login, str(index), message_file, photo_folder, str(use_photos), group_name, str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif groupRaid == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    group_id = reg.extract_group_id(group_url)

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        index = 1

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ СТИКЕРАМИ В ЛС ГРУППЫ {group_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidGroup/raidGroup_sticker.py', token, login, group_id, group_name, str(index), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif groupRaid == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                    group_id = reg.extract_group_id(group_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        message_file = select_message_file()
                        owner_id = group_id
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ НА СТЕНУ ГРУППЫ {group_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidGroup/raidGroup_wall.py', owner_id, token, login, str(index), message_file, photo_folder, str(use_photos), group_name, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif groupRaid == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    group_url = input_white("ВВЕДИ ССЫЛКУ НА ТОПИК: ")
                    group_id = reg.extract_group_id(group_url)
                    topic_id = reg.extract_topic_id(group_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        message_file = select_message_file()
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ ПОД ТОПИКОМ С ID: {topic_id} НА СТЕНЕ ГРУППЫ {group_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidGroup/raidGroup_topic.py', group_id, topic_id, token, login, str(index), message_file, photo_folder, str(use_photos), group_name, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif groupRaid == "5":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    folder_path = 'raidfiles'
                    album_url = input_white("ВВЕДИ ССЫЛКУ НА ФОТОАЛЬБОМ: ")
                    num_photos = int(input_white("ВВЕДИ КОЛ-ВО ФОТОГРАФИЙ: "))
                    description = input_white("ВВЕДИ КОММЕНТАРИЙ ДЛЯ ФОТОГРАФИЙ (ENTER - ЕСЛИ НЕ НУЖЕН): ")

                    photos = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

                    num_tokens = len(tokens)
                    photos_per_token = num_photos // num_tokens 
                    remainder = num_photos % num_tokens

                    group_id, album_id = reg.extract_album_info(album_url)
                    group_id = abs(int(group_id))  
                    album_id = abs(int(album_id))
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ ЗАГРУЗКУ ФОТОГРАФИЙ В ФОТОАЛЬБОМ, ПРОЦЕСС ДОВОЛЬНО ДЛИТЕЛЬНЫЙ, ОЖИДАЙ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        url_photos_get_upload_server = 'https://api.vk.com/method/photos.getUploadServer'
                        first_token = next(iter(tokens.values()))
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        album_info = await reg.get_album_info(session, first_token, group_id, album_id, proxy)
                        album_name = album_info['title']

                        tasks = []
                        for i, (login, token) in enumerate(tokens.items()): 
                            params_get_upload_server = {
                                'album_id': album_id,
                                'group_id': group_id,
                                'access_token': token,
                                'v': '5.131'
                            }
                            async with session.get(url_photos_get_upload_server, params=params_get_upload_server, proxy=proxy) as response:
                                upload_url = (await response.json())['response']['upload_url']

                            token_photos = photos_per_token + (1 if i < remainder else 0)
                            for _ in range(token_photos):  
                                random_photo = random.choice(photos)
                                task = asyncio.create_task(
                                    raidGroup_module.upload_photo(session, token, upload_url, album_id, group_id, random_photo, login, album_name, group_name, proxy, description)
                                )
                                tasks.append(task)
                                await asyncio.sleep(0.33)

                        await asyncio.gather(*tasks)
                        print_white(f"ЗАКОНЧИЛИ ЗАГРУЗКУ ФОТОГРАФИЙ В ФОТОАЛЬБОМ {album_name} в группе {group_name}")
                elif groupRaid == "6":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    group_url = input_white("ВВЕДИ ССЫЛКУ НА ПОСТ В ГРУППЕ: ")
                    group_id = reg.extract_group_id(group_url)
                    post_id = reg.extract_post_id(group_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        message_file = select_message_file()
                        owner_id = group_id
                        index = 1

                        while True:
                            user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                            if user_input in ['yes', 'y']:
                                use_photos = True
                                break
                            elif user_input in ['no', 'n']:
                                use_photos = False
                                break
                            else:
                                print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                        print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В КОММЕНТАРИИ К ПОСТУ C ID: {post_id} НА СТЕНЕ ГРУППЫ {group_name}")
                        for login, token in tokens.items():
                            subprocess.Popen(['python', 'raid_modules/raidGroup/raidGroup_wall_comment.py', owner_id, post_id, token, login, str(index), message_file, photo_folder, str(use_photos), group_name, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif groupRaid == "7":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "3":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. РЕЙД БЕСЕДЫ")
                print_white("2. РЕЙД БЕСЕДЫ СТИКЕРАМИ")
                print_white("3. РЕЙД СМЕНОЙ ТЕМЫ ЧАТА")
                print_white("4. РЕЙД СКРИНШОТАМИ")
                print_white("5. ЗАКРЕП СООБЩЕНИЯ + НАЗВАНИЯ + АВАТАРКИ")
                print_white("6. ПОЙТИ НАХУЙ")
                besedaRaid = input_white("ВЫБИРАЙ БЛЯ: ")

                if besedaRaid == "1": 
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    attach_file = "message/attach.txt"
                    first_token = next(iter(tokens.values()))
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                            theme_state = reg.load_theme_state()
                            manager_state = reg.load_manager_state()
                            message_file = select_message_file()
                            index = 1

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_attach = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_attach = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_photos = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_photos = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В БЕСЕДУ {chat_title}")
                            for login, token in tokens.items():
                                user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                                user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                                if user_chat_id is not None:
                                    subprocess.Popen(['python', 'raid_modules/raidBeseda/raidBeseda_chat.py', str(user_chat_id), token, login, chat_title, str(index), str(theme_state), message_file, photo_folder, str(use_photos), str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ С НАЗВАНИЕМ {chat_title} ДЛЯ ЛОГИНА {login}")
                elif besedaRaid == "2": 
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                            theme_state = reg.load_theme_state()
                            index = 1

                            print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ СТИКЕРАМИ В БЕСЕДУ {chat_title}")
                            for login, token in tokens.items():
                                user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                                user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                                if user_chat_id is not None:
                                    subprocess.Popen(['python', 'raid_modules/raidBeseda/raidBeseda_sticker.py', str(user_chat_id), token, login, chat_title, str(index), str(theme_state), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ С НАЗВАНИЕМ {chat_title} ДЛЯ ЛОГИНА {login}")
                elif besedaRaid == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                            index = 1

                            print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ СМЕНОЙ ТЕМЫ ЧАТА В БЕСЕДУ {chat_title}")
                            for login, token in tokens.items():
                                user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                                user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                                if user_chat_id is not None:
                                    subprocess.Popen(['python', 'raid_modules/raidBeseda/raidBeseda_theme.py', str(user_chat_id), token, login, chat_title, str(index), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ С НАЗВАНИЕМ {chat_title} ДЛЯ ЛОГИНА {login}")
                elif besedaRaid == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                            index = 1

                            print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ СКРИНШОТАМИ В БЕСЕДУ {chat_title}")
                            for login, token in tokens.items():
                                user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                                user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                                if user_chat_id is not None:
                                    subprocess.Popen(['python', 'raid_modules/raidBeseda/raidBeseda_screenshot.py', str(user_chat_id), token, login, chat_title, str(index), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ С НАЗВАНИЕМ {chat_title} ДЛЯ ЛОГИНА {login}")
                elif besedaRaid == "5":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    token = next(iter(tokens.values()))
                    login = next(iter(tokens.keys()))
                    photo_folder = "raidfiles"
                    avatars_folder = 'avatars'
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    attach_file = "message/attach.txt"
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                            new_title = input_white("ВВОДИ НОВОЕ НАЗВАНИЕ БЕСЕДЫ (ENTER - ЕСЛИ НЕ НУЖНО): ")
                            if new_title == "":
                                new_title = "None"

                            while True:
                                user_input = input_white("НАДО ЛИ СТАВИТЬ РАНДОМНУЮ АВАТАРКУ ИЗ ПАПКИ avatars? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_avatar = "Yes"
                                    break
                                elif user_input in ['no', 'n']:
                                    use_avatar = "No"
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            new_message = input_white("ВВОДИ ЗАКРЕПЛЕННОЕ СООБЩЕНИЕ (ENTER - ЕСЛИ НЕ НУЖНО): ")
                            if new_message == "":
                                new_message = "None"
                                use_photo = False

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_attach = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_attach = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            if new_message != "None":
                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКУ ИЛИ ГИФКУ ИЗ RAIDFILES ДЛЯ ЗАКРЕПЛЕННОГО СООБЩЕНИЯ? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_photo = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_photo = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            print_white(f"ВКЛЮЧИЛИ АВТО ЗАКРЕП СООБЩЕНИЯ + АВАТАРКИ + НАЗВАНИЯ ДЛЯ БЕСЕДЫ {chat_title}")
                            if chat_id:
                                subprocess.Popen(['python', 'raid_modules/raidBeseda/raidBeseda_antichange.py', str(chat_id), token, login, chat_title, new_title, new_message, str(use_photo), use_avatar, photo_folder, avatars_folder, attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif besedaRaid == "6":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "4":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. РЕЙД СТРИМА /// ВИДЕО")
                print_white("2. ПОЙТИ НАХУЙ")
                media = input_white("ВЫБИРАЙ БЛЯ: ")

                if media == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_folder = "raidfiles"
                    user_url = input_white("ВВЕДИ ССЫЛКУ НА ВИДЕО ИЛИ ТРАНСЛЯЦИЮ: ")
                    owner_id = reg.extract_owner_id(user_url)
                    video_id = reg.extract_video_id(user_url)
                    full = video_id.index('_')
                    video_id = video_id[full + 1:]
                    message_file = select_message_file()
                    index = 1

                    while True:
                        user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                        if user_input in ['yes', 'y']:
                            use_photos = True
                            break
                        elif user_input in ['no', 'n']:
                            use_photos = False
                            break
                        else:
                            print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                    print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В КОММЕНТАРИИ К ВИДЕО ИЛИ НА ТРАНСЛЯЦИИ С ID: {video_id}")
                    for login, token in tokens.items():
                        subprocess.Popen(['python', 'raid_modules/raidMedia/raidMedia_video_stream.py', str(owner_id), str(video_id), token, login, str(index), message_file, photo_folder, str(use_photos)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                if media == "2":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "5":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. РЕПОРТ НА ПОЛЬЗОВАТЕЛЯ")
                print_white("2. РЕПОРТ НА ЗАПИСЬ")
                print_white("3. РЕПОРТ НА КОММЕНТАРИЙ")
                print_white("4. РЕПОРТ НА ВИДЕОЗАПИСЬ")
                print_white("5. РЕПОРТ НА КОММЕНТАРИЙ К ВИДЕОЗАПИСИ")
                print_white("6. РЕПОРТ НА ФОТО")
                print_white("7. РЕПОРТ НА КОММЕНТАРИЙ К ФОТО")
                print_white("8. РЕПОРТ НА ТОВАР")
                print_white("9. РЕПОРТ НА КОММЕНТАРИЙ К ТОВАРУ")
                print_white("10. ПОЙТИ НАХУЙ")
                report = input_white("ВЫБИРАЙ БЛЯ: ")

                if report == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    url = input_white("ВВЕДИ ССЫЛАЧКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    user_id = reg.extract_user_id(url)
                    complaint_type = input_white("ВВЕДИ ПРИЧИНУ ЖАЛОБЫ (porn, spam, insult, advertisement): ")
                    comment = input_white("ВВЕДИ КОММЕНТ К ЖАЛОБЕ (ENTER - НЕ НУЖЕН): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_report_pol(session, token, login, user_id, complaint_type, comment, user_name, proxy))
                        await asyncio.gather(*tasks)
                elif report == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛАЧКУ НА ПОСТ: ")
                    owner_id, post_id = reg.extract_owner_post_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ, 8 — ПРИЗЫВЫ К СУИЦИДУ): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_wall_report(session, token, login, owner_id, post_id, reason, proxy))
                        await asyncio.gather(*tasks)
                elif report == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛАЧКУ НА КОММЕНТАРИЙ: ")
                    owner_id, comment_id = reg.extract_comment_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ, 8 — ПРИЗЫВЫ К СУИЦИДУ): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_wall_comment_report(session, token, login, owner_id, comment_id, reason, proxy))
                        await asyncio.gather(*tasks)
                elif report == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛОЧКУ НА ВИДЕО: ")
                    video_id = reg.extract_video_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ): ")
                    comment = input_white("ВВЕДИ КОММЕНТ К ЖАЛОБЕ (НАЖМИ ENTER ЕСЛИ ОН НЕ НУЖЕН): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_video_report(session, token, login, video_id, reason, comment, proxy))
                        await asyncio.gather(*tasks)
                elif report == "5":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛОЧКУ НА КОММЕНТАРИЙ К ВИДЕО: ")
                    owner_id, comment_id = reg.extract_video_comment_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ): ")
                    comment = input_white("ВВЕДИ КОММЕНТ К ЖАЛОБЕ (ОБЯЗАТЕЛЕН!): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_video_comment_report(session, token, login, owner_id, comment_id, reason, comment, proxy))
                        await asyncio.gather(*tasks)
                elif report == "6":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛОЧКУ НА ФОТО: ")
                    photo_id = reg.extract_photo_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_photo_report(session, token, login, photo_id, reason, proxy))
                        await asyncio.gather(*tasks)
                elif report == "7":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛОЧКУ НА КОММЕНТАРИЙ К ФОТО: ")
                    owner_id, comment_id = reg.extract_photo_comment_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_photo_comment_report(session, token, login, owner_id, comment_id, reason, proxy))
                        await asyncio.gather(*tasks)
                elif report == "8":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    url = input_white("ВВЕДИ ССЫЛОЧКУ НА ТОВАР: ")
                    item_id, owner_id = reg.extract_market_item_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_market_report(session, token, login, item_id, owner_id, reason, proxy))
                        await asyncio.gather(*tasks)
                elif report == "9":
                    url = input_white("ВВЕДИ ССЫЛОЧКУ НА КОММЕНТАРИЙ К ТОВАРУ: ")
                    owner_id, comment_id = reg.extract_market_comment_id(url)
                    reason = input_white("ВЫБЕРИ ПРИЧИНУ ЖАЛОБЫ (0 — СПАМ, 1 — ДЕТСКАЯ ПОРНОГРАФИЯ, 2 — ЭКСТРЕМИЗМ, 3 — НАСИЛИЕ, 4 — ПРОПАГАНДА НАРКОТИКОВ, 5 — МАТЕРИАЛ ДЛЯ ВЗРОСЛЫХ, 6 — ОСКОРБЛЕНИЕ): ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(reports_module.send_market_comment_report(session, token, login, owner_id, comment_id, reason, proxy))
                        await asyncio.gather(*tasks)
                elif report == "10":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "6":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. ПАРСЕР ЛЕНТЫ НА ССЫЛКИ БЕСЕД")
                print_white("2. ПАРСЕР СТРАНИЦЫ")
                print_white("3. ПАРСЕР ГРУППЫ")
                print_white("4. ПАРСЕР МЕССЕНДЖЕРА")
                print_white("5. ПОЙТИ НАХУЙ")
                parser = input_white("ВЫБИРАЙ БЛЯ: ")

                if parser == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    keyword = input_white("ВВОДИ КЛЮЧЕВОЕ СЛОВО ДЛЯ ПОИСКА БЕСЕД (ENTER - ЕСЛИ ОНО НЕ НУЖНО): ")
                    post_count = int(input_white("ВВЕДИ КОЛ-ВО ПОСТОВ ДЛЯ СКАНИРОВАНИЯ: "))
                    minutes = int(input_white("ВВЕДИ ПОСЛЕДНИЙ ВРЕМЕННОЙ ИНТЕРВАЛ НАЧИНАЯ С КОТОРОГО БУДЕМ ИСКАТЬ ПОСТЫ (МИНУТЫ!): "))
                    end_time = int(time.time())
                    start_time = int(time.time() - minutes * 60)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ОЖИДАЙ ОКОНЧАНИЯ СКАНИРОВАНИЯ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_links = await parser_module.find_group_chats_links(session, first_token, start_time, end_time, post_count, proxy, keyword if keyword else None)

                        existing_links = set()
                        vk_link_pattern = r"vk\.me/join/[A-Za-z0-9/=_-]+"
                        if os.path.getsize('base/chat_links.txt') > 0:
                            with open('base/chat_links.txt', 'r') as file:
                                for line in file:
                                    links = re.findall(vk_link_pattern, line)
                                    existing_links.update(links)

                        with open('base/chat_links.txt', 'a') as file:
                            for link in chat_links:
                                if link not in existing_links:
                                    if keyword:
                                        file.write(f"ССЫЛКА НА БЕСЕДУ: {link} (КЛЮЧЕВОЕ СЛОВО: {keyword})\n")
                                    else:
                                        file.write(f"ССЫЛКА НА БЕСЕДУ: {link}\n")
                        print_white("ССЫЛАЧКИ НА БЕСЕДЫ УСПЕШНО ЗАПИСАНЫ В chat_links.txt")
                elif parser == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    input_str = input_white("ВВЕДИ ССЫЛОЧКУ НА ПРОФИЛЬ ИЛИ ID: ")
                    user_id = reg.extract_group_id(input_str)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ОЖИДАЙ ЗАВЕРШЕНИЕ ПАРСИНГА ПРОФИЛЯ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = [parser_module.parser_profile(session, first_token, user_id, proxy)]
                        await asyncio.gather(*tasks)
                        print_white("ПАРСИНГ ПРОФИЛЯ УСПЕШНО ЗАВЕРШЕН")
                elif parser == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    group_input = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                    group_id = reg.extract_user_id(group_input)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ОЖИДАЙ ЗАВЕРШЕНИЕ ПАРСИНГА ГРУППЫ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = [parser_module.parser_group(session, first_token, group_id, proxy)]
                        await asyncio.gather(*tasks)
                        print_white("ПАРСИНГ ГРУППЫ УСПЕШНО ЗАВЕРШЕН!")
                elif parser == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    count_input = input_white("ВВЕДИ КОЛ-ВО ДИАЛОГОВ ДЛЯ ПАРСИНГА (или нажмите ENTER для всех): ")
                    count = int(count_input) if count_input else None
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ОЖИДАЙ ЗАВЕРШЕНИЕ ПАРСИНГА ДИАЛОГОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = [parser_module.parser_messenger(session, login, token, count, proxy) for login, token in tokens.items()]
                        await asyncio.gather(*tasks)
                        print_white(f"ПАРСИНГ МЕССЕНДЖЕРА ЗАВЕРШЕН ДЛЯ ВСЕХ ТОКЕНОВ!")
                elif parser == "5":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "7":
            user_text = input_white("ВВЕДИ ТЕКСТ: ")
            intensity = int(input_white("ВЫБЕРИ УРОВЕНЬ НАГРУЖЕННОСТИ (1 - МАЛО БЛЯТЬ, 2 - ДОХУЯ, 3 - ДАХУИЩА): "))
            file_path = "message/zalgo.txt"
            with open(file_path, "a", encoding="utf-8") as file:
                file.write(zalgo_text(user_text, intensity) + "\n")
            print_white(f"ТВОЙ ТЕКСТ УСПЕШНО СОХРАНЕН В ПАПКУ message - ТЕКСТОВИК zalgo.txt")
        elif choice == "8":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. МАССОВОЕ ДОБАВЛЕНИЕ В ДРУЗЬЯ")
                print_white("2. БОТЫ - ДРУЗЬЯ")
                print_white("3. ПРИНЯТЬ ВСЕ ЗАЯВКИ В ДРУЗЬЯ")
                print_white("4. АВТОПРИЕМ В ДРУЗЬЯ")
                print_white("5. ПОЙТИ НАХУЙ")
                friends = input_white("ВЫБИРАЙ БЛЯ: ")

                if friends == "1":
                    while True:
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        headers = reg.load_headers()
                        proxy = reg.load_proxy()
                        print_white("[РЕЙД-КОНФИГ]:")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                        print_white("[БАЗА ДАННЫХ]:")
                        print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                        print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                        print_white("[РЕЙД-МЕНЮ]:")
                        print_white("1. МАССОВОЕ ДОБАВЛЕНИЕ В ДРУЗЬЯ К ПОЛЬЗОВАТЕЛЮ")
                        print_white("2. МАССОВОЕ ДОБАВЛЕНИЕ В ДРУЗЬЯ К ДРУЗЬЯМ ПОЛЬЗОВАТЕЛЯ")
                        print_white("3. МАССОВОЕ ДОБАВЛЕНИЕ В ДРУЗЬЯ УЧАСТНИКОВ ГРУППЫ")
                        print_white("4. МАССОВОЕ ДОБАВЛЕНИЕ В ДРУЗЬЯ ИЗ БЕСЕДЫ")
                        print_white("5. ПОЙТИ НАХУЙ")
                        friendsMass = input_white("ВЫБИРАЙ БЛЯ: ")

                        if friendsMass == "1":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            url = input_white("ВВОДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                            user_id = extract_user_id(url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                await friends_module.massDov(session, user_id, tokens, proxy)
                        if friendsMass == "2":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            url = input_white("ВВОДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                            user_id = extract_user_id(url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                await friends_module.friends_pol_mass_random(session, user_id, tokens, proxy)
                        if friendsMass == "3":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            group_url = input_white("ВВОДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                await friends_module.group_friends_pol_mass_random(session, group_id, tokens, proxy)
                        if friendsMass == "4":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            first_token = next(iter(tokens.values()))
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                                if chat_ids:
                                    print_white("СПИСОК БЕСЕД:")
                                    for chat in chat_ids:
                                        print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                                    chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                                    chat_title = next(chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id)
                                    user_ids = await reg.get_chat_members(session, first_token, chat_id, proxy)
                                    tasks = []
                                    for login, token in tokens.items():
                                        task = friends_module.add_friendMass(session, first_token, token, login, user_ids, proxy)
                                        tasks.append(task)
                                    await asyncio.gather(*tasks)
                        if friendsMass == "5":
                            print_white("НУ И ПИЗДУЙ")
                            break
                        else:
                            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
                elif friends == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    if len(tokens) < 2:
                        print_white("НЕДОСТАТОЧНО ТОКЕНОВ ДЛЯ РАБОТЫ!")
                    else:
                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            await friends_module.add_friends(session, tokens, proxy)
                elif friends == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ ПРИНИМАТЬ ВСЕ ЗАЯВКИ В ДРУЗЬЯ")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        for login, token in tokens.items():
                            await friends_module.accept_friend_requests(session, token, login, proxy)
                elif friends == "4": 
                    tokens = reg.read_tokens(TOKENS_FILE)
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    print_white("СКРИПТ ЗАПУЩЕН! АВТОПРИЕМ ВКЛЮЧЕН ДЛЯ ВСЕХ ТОКЕНОВ!")

                    for login, token in tokens.items():
                        subprocess.Popen(['python', 'raid_modules/auto_friends.py', token, login, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif friends == "5":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "9":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. МАССОВЫЙ ЗАХОД В БЕСЕДЫ ПО ССЫЛКАМ ИЗ ТЕКСТОВИКА")
                print_white("2. МАССОВЫЙ ЗАХОД В БЕСЕДУ ПО ССЫЛКЕ")
                print_white("3. МАССОВОЕ ПРИГЛАШЕНИЕ ДРУЗЕЙ В БЕСЕДУ")
                print_white("4. ПОЙТИ НАХУЙ")
                rb = input_white("ВЫБИРАЙ БЛЯ: ")

                if rb == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧИНАЕМ ЕБЕЙШИЙ ЗАХОД В БЕСЕДЫ СО ВСЕХ ТОКЕНОВ!")

                    chat_links = []
                    vk_link_pattern = r"vk\.me/join/[A-Za-z0-9/=_-]+"
                    with open('base/chat_links.txt', 'r') as file:
                        for line in file:
                            links = re.findall(vk_link_pattern, line)
                            chat_links.extend(links)

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = [besedi_module.join_chat(session, login, token, chat_link, proxy) for chat_link in chat_links for login, token in tokens.items()]
                        await asyncio.gather(*tasks)
                    print_white(f"ЗАКОНЧИЛИ ЕБЕЙШИЙ ЗАХОД В БЕСЕДЫ СО ВСЕХ ТОКЕНОВ!")
                elif rb == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    chat_link = input_white("ВВЕДИ ССЫЛКУ НА БЕСЕДУ: ")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white(f"НАЧАЛИ ЛЮТЫЙ ЗАХОД В БЕСЕДУ {chat_link} СО ВСЕХ ТОКЕНОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = [besedi_module.join_chat(session, login, token, chat_link, proxy) for login, token in tokens.items()]
                        await asyncio.gather(*tasks)
                    print_white(f"ЗАКОНЧИЛИ ЛЮТЫЙ ЗАХОД В БЕСЕДУ {chat_link} СО ВСЕХ ТОКЕНОВ!")
                elif rb == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None) 
                            for login, token in tokens.items():
                                user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                                user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                                if user_chat_id is not None:
                                    await besedi_module.invite_friends_to_chat(session, login, token, user_chat_id, chat_title, proxy)  
                                else:
                                    print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ {chat_title} ДЛЯ ЛОГИНА {login}")
                        else:
                            print_white("НЕ УДАЛОСЬ ПОЛУЧИТЬ СПИСОК БЕСЕД")
                elif rb == "4":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "10":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. СМЕНА ИМЕНИ И ФАМИЛИИ")
                print_white("2. ОТКРЫТЬ/ЗАКРЫТЬ ПРОФИЛИ")
                print_white("3. ПОСТАВИТЬ СТАТУС")
                print_white("4. СМЕНА АВАТАРОК")
                print_white("5. МАССОВАЯ СМЕНА ПАРОЛЕЙ")
                print_white("6. МАССОВЫЙ ЛАЙК")
                print_white("7. МАССОВЫЙ РЕПОСТ")
                print_white("8. МАССОВЫЙ ГОЛОС В ОПРОСЕ")
                print_white("9. МАССОВЫЕ ПОДПИСКИ")
                print_white("10. МАССОВО ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ В ЧЕРНЫЙ СПИСОК")
                print_white("11. МАССОВО УДАЛИТЬ ПОЛЬЗОВАТЕЛЯ ИЗ ЧЕРНОГО СПИСКА")
                print_white("12. МАССОВО ДОБАВИТЬ ГРУППУ В ЧЕРНЫЙ СПИСОК")
                print_white("13. МАССОВО УДАЛИТЬ ГРУППУ ИЗ ЧЕРНОГО СПИСКА")
                print_white("14. ОЧИСТИТЬ СТЕНУ СТРАНИЦ")
                print_white("15. ОЧИСТИТЬ ДРУЗЕЙ СТРАНИЦ")
                print_white("16. ОЧИСТИТЬ ФОТОГРАФИИ СТРАНИЦ")
                print_white("17. ОЧИСТИТЬ ПОДПИСКИ НА ГРУППЫ И ПОЛЬЗОВАТЕЛЕЙ СТРАНИЦ")
                print_white("18. ОЧИСТИТЬ МЕССЕНДЖЕР СТРАНИЦ")
                print_white("19. КЛОН ПРОФИЛЯ")
                print_white("20. ПОЙТИ НАХУЙ")
                profil = input_white("ВЫБИРАЙ БЛЯ: ")

                if profil == "1":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    name_file = "base/names.txt"
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        for login, token in tokens.items():
                            await profile_module.set_name(session, login, token, name_file, proxy)
                elif profil == "2":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    action = input_white("ВВЕДИ ЧЕ БУДЕМ ДЕЛАТЬ С ПРОФИЛЕМ (open/close): ").strip().lower()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        if action in ["open", "close"]:
                            for login, token in tokens.items():
                                await (profile_module.change_profiles(session, tokens, action, proxy))
                        else:
                            print_white("АЛО ЕБЛАН СКАЗАНО ЖЕ 'open' ИЛИ 'close'")
                elif profil == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    status = input_white("ВВЕДИ НОВЫЙ СТАТУС: ").strip()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        for login, token in tokens.items():
                            await profile_module.set_status(session, login, token, status, proxy)
                elif profil == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    photo_path = os.path.abspath("avatars")
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ЖДИ КАРОЧИ ЗАГРУЖАЕМ АВАТАРОЧКИ")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        for login, token in tokens.items():
                            await profile_module.set_profile_photo(session, token, login, photo_path, proxy)
                elif profil == "5":
                    accounts = reg.read_accounts("base/accounts.txt")
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    new_password = input_white("ВВЕДИ НОВЫЙ ПАРОЛЬ: ")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, old_password in accounts:
                            if login in tokens:
                                token = tokens[login]
                                task = asyncio.create_task(
                                    profile_module.change_password(session, login, old_password, new_password, token, proxy)
                                )
                                tasks.append(task)

                        results = await asyncio.gather(*tasks)

                    with open("base/accounts.txt", "w", encoding="utf-8") as file:
                        for (login, old_password), success in zip(accounts, results):
                            file.write(f"{login}:{new_password if success else old_password}\n")

                    print_white("ПАРОЛИ НА ВСЕХ АККАУНТАХ УСПЕШНО ИЗМЕНЕНЫ! ФАЙЛ ОБНОВЛЕН!")
                elif profil == "6": 
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    url = input_white("ССЫЛОЧКУ НА ОБЪЕКТ ПОЖАЛУЙСТА: ")
                    action = input_white("ВВОДИ ЧЕ ДЕЛАТЬ (add/delete): ")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        await profile_module.parsing_objects(session, url, action, proxy)
                elif profil == "7":
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    url = input_white("ССЫЛАЧКУ НА ПОСТ ПЖ: ")
                    message = input_white("СООБЩЕНИЕ ВВОДИ (ENTER - ПРОПУСТИТЬ): ")
                    group_id = input_white("ВВОДИ group_id (ENTER - ПРОПУСТИТЬ): ")
                    group_id = group_id if group_id else None

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        await profile_module.parsing_objectsReposts(session, url, message, group_id, proxy)
                elif profil == "8":
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    url = input_white("ССЫЛОЧКУ НА ОПРОС ПОЖАЛУЙСТА: ")
                    action = input_white("ВВОДИ ЧЕ ДЕЛАТЬ (add/delete): ")
                    answer_index = input_white("ВВОДИ НОМЕР ВАРИАНТА ДЛЯ ГОЛОСОВАНИЯ: ") if action == "add" else ''
                    is_board = input_white("ВВОДИ is_board (1 - в топике, 0 - на стене): ")
                    owner_id, poll_id = reg.extract_poll_owner_ids(url)

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        await profile_module.parsing_objectsPolls(session, owner_id, poll_id, action, url, answer_index, is_board, proxy)
                elif profil == "9":
                    url = input_white("ВВЕДИ ССЫЛКУ НА ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППУ: ")
                    action = input_white("ВЫБЕРИТЕ ДЕЙСТВИЕ (subscribe/unsubscribe): ")
                    await profile_module.mass_action(url, action)
                elif profil == "10":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    user_id = reg.extract_user_id(url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        for login, token in tokens.items():
                            await profile_module.ban_user(session, user_id, token, login, user_name, proxy)
                elif profil == "11":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                    user_id = reg.extract_user_id(url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        for login, token in tokens.items():
                            await profile_module.unban_user(session, user_id, token, login, user_name, proxy)
                elif profil == "12":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                    group_id = reg.extract_group_id(url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        for login, token in tokens.items():
                            await profile_module.ban_group(session, group_id, token, login, user_name, proxy)
                elif profil == "13":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                    group_id = reg.extract_group_id(url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        for login, token in tokens.items():
                            await profile_module.unban_group(session, group_id, token, login, user_name, proxy)
                elif profil == "14":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ УДАЛЕНИЕ ПОСТОВ НА СТРАНИЦАХ ВСЕХ ТОКЕНОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            task = asyncio.create_task(profile_module.delete_wall_posts(session, login, token, proxy))  
                            tasks.append(task)
                        await asyncio.gather(*tasks)
                elif profil == "15":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ УДАЛЕНИЕ ДРУЗЕЙ НА СТРАНИЦАХ ВСЕХ ТОКЕНОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            task = asyncio.create_task(profile_module.delete_all_friends(session, login, token, proxy))
                            tasks.append(task)
                        await asyncio.gather(*tasks)
                elif profil == "16":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ УДАЛЕНИЕ ФОТОГРАФИЙ НА СТРАНИЦАХ ВСЕХ ТОКЕНОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            task = asyncio.create_task(profile_module.delete_all_photos(session, login, token, proxy))
                            tasks.append(task)
                        await asyncio.gather(*tasks)
                elif profil == "17":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ УДАЛЕНИЕ ПОДПИСОК НА ГРУППЫ И ПОЛЬЗОВАТЕЛЕЙ НА СТРАНИЦАХ ВСЕХ ТОКЕНОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            task = asyncio.create_task(profile_module.delete_all_groups_and_subscriptions(session, login, token, proxy))
                            tasks.append(task)
                        await asyncio.gather(*tasks)
                elif profil == "18":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ УДАЛЕНИЕ ВСЕГО МЕССЕНДЖЕРА НА СТРАНИЦАХ ВСЕХ ТОКЕНОВ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            task = asyncio.create_task(profile_module.delete_all_messenger(session, login, token, proxy))
                            tasks.append(task)
                        await asyncio.gather(*tasks)
                elif profil == "19":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    user_name = input_white("ВВЕДИ ИМЯ ПОЛЬЗОВАТЕЛЯ: ")
                    print_white("ЗАПУСТИЛИ КЛОН ПРОФИЛЯ! ПРОЦЕСС ДОВОЛЬНО ДЛИТЕЛЬНЫЙ, ОЖИДАЙ!")

                    tasks = []
                    for token in tokens.values():
                        tasks.append(profile_module.clon(user_name, token))
                    await asyncio.gather(*tasks)
                    print_white("УСПЕШНО УСТАНОВИЛИ КЛОН ПРОФИЛЯ ДЛЯ ВСЕХ ТОКЕНОВ!")
                elif profil == "20":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "11":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. УПРАВЛЕНИЕ ГРУППАМИ")
                print_white("2. УПРАВЛЕНИЕ РЕЙД-ГРУППАМИ")
                print_white("3. УПРАВЛЕНИЕ НЕЙРОСЕТЬЮ")
                print_white("4. АВТО-ЧС - ЕБЕМ И ДОБАВЛЯЕМ В ЧС")
                print_white("5. НАСЕР - БОТ ТРОЛЛЬ")
                print_white("6. ПОЙТИ НАХУЙ")
                pizdec = input_white("ВЫБИРАЙ БЛЯ: ")

                if pizdec == "1":
                    while True:
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        headers = reg.load_headers()
                        proxy = reg.load_proxy()
                        print_white("[РЕЙД-КОНФИГ]:")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                        print_white("[БАЗА ДАННЫХ]:")
                        print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                        print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                        print_white("[РЕЙД-МЕНЮ]:")
                        print_white("1. ИЗМЕНИТЬ ПАРАМЕТРЫ ГРУППЫ")
                        print_white("2. ИЗМЕНИТЬ АВАТАРКУ ГРУППЫ")
                        print_white("3. ИЗМЕНИТЬ ОБЛОЖКУ ГРУППЫ")
                        print_white("4. УДАЛИТЬ ВСЕ ПОСТЫ ГРУППЫ")
                        print_white("5. УДАЛИТЬ ВСЕ КОММЕНТАРИИ ПОД ПОСТОМ ГРУППЫ")
                        print_white("6. УДАЛИТЬ ВСЕ ФОТОГРАФИИ ГРУППЫ")
                        print_white("7. УДАЛИТЬ ВСЕ ТОПИКИ ГРУППЫ")
                        print_white("8. ЗАБАНИТЬ ВСЕХ ПОДПИСЧИКОВ ГРУППЫ")
                        print_white("9. ПОЙТИ НАХУЙ")
                        group_control = input_white("ВЫБИРАЙ БЛЯ: ")

                        if group_control == "1":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            params = {}
                            while True:
                                param_name = input_white("ВВЕДИ НАЗВАНИЕ ПАРАМЕТРА (ENTER - ЗАКОНЧИТЬ ВВОД): ")
                                if not param_name:  
                                    break
                                param_value = input_white(f"ВВЕДИ ЗНАЧЕНИЕ ДЛЯ {param_name}: ")
                                params[param_name] = param_value

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        await topRaid_module.edit_group(session, token, login, group_name, group_id, proxy, **params)
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")
                        elif group_control == "2":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()
                            avatar_folder = "avatars" 

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        avatar_name = random.choice(os.listdir(avatar_folder))
                                        avatar_path = os.path.join(avatar_folder, avatar_name)
                                        await topRaid_module.upload_group_avatar(session, token, login, group_id, group_name, avatar_name, avatar_path, proxy)
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")
                        elif group_control == "3":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()
                            cover_folder = "avatars"

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id):
                                        cover_name = random.choice(os.listdir(cover_folder))
                                        cover_path = os.path.join(cover_folder, cover_name)
                                        await topRaid_module.edit_group_cover(session, token, login, group_id, group_name, cover_name, cover_path, proxy)
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")
                        elif group_control == "4":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']
                                owner_id = group_id

                                tasks = []
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        tasks.append(utils_module.delete_wall_posts_group(session, owner_id, token, login, group_name, proxy))
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")

                                await asyncio.gather(*tasks)
                                print_white(f"ВСЕ ПОСТЫ УСПЕШНО БЫЛИ УДАЛЕНЫ В ГРУППЕ {group_name}")
                        elif group_control == "5":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ НА ПОСТ В ГРУППЕ: ")
                            group_id = reg.extract_group_id(group_url)
                            post_id = reg.extract_post_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']
                                owner_id = group_id

                                tasks = []
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        tasks.append(utils_module.delete_wall_post_comments_group(session, owner_id, post_id, token, login, group_name, proxy))
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")

                                await asyncio.gather(*tasks)
                                print_white(f"ВСЕ КОММЕНТАРИИ БЫЛИ УСПЕШНО УДАЛЕНЫ С ПОСТА С ID: {post_id} В ГРУППЕ {group_name}")
                        elif group_control == "6":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']

                                tasks = []
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        tasks.append(topRaid_module.delete_all_photos_group(session, token, login, group_id, group_name, proxy))
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")

                                await asyncio.gather(*tasks)
                                print_white(f"ВСЕ ФОТОГРАФИ БЫЛИ УСПЕШНО УДАЛЕНЫ В ГРУППЕ {group_name}")
                        elif group_control == "7":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']

                                tasks = []
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        tasks.append(topRaid_module.delete_all_discussions_group(session, token, login, group_id, group_name, proxy))
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")

                                await asyncio.gather(*tasks)
                                print_white(f"ВСЕ ТОПИКИ БЫЛИ УСПЕШНО УДАЛЕНЫ В ГРУППЕ {group_name}")
                        elif group_control == "8":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            reason = input_white("ВЫБЕРИ ПРИЧИНУ БАНА (1-СПАМ, 2-ОСКОРБЛЕНИЕ УЧАСТНИКОВ, 3-НЕЦЕНЗУРНЫЕ ВЫРАЖЕНИЯ, 4-СООБЩЕНИЯ НЕ ПО ТЕМЕ, 0-ДРУГОЕ): ")
                            comment = input_white("ВВЕДИ КОММЕНТАРИЙ К БАНУ (ENTER - НЕ НУЖЕН): ")
                            if comment:
                                comment_visible = input_white("ВЫБЕРИ ТИП ОТОБРАЖЕНИЯ КОММЕНТАРИЯ (0 - НЕ ОТОБРАЖАЕТСЯ ПОЛЬЗОВАТЕЛЮ, 1-ОТОБРАЖАЕТСЯ ПОЛЬЗОВАТЕЛЮ): ")
                            print(comment_visible)
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']

                                tasks = []
                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        if comment:
                                            tasks.append(topRaid_module.ban_all_members_group_comment(session, token, login, group_id, group_name, reason, comment, comment_visible, proxy))
                                        else:
                                            tasks.append(topRaid_module.ban_all_members_group(session, token, login, group_id, group_name, reason, proxy))

                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")

                                await asyncio.gather(*tasks)
                                print_white(f"ВСЕ УЧАСТНИКИ БЫЛИ УСПЕШНО ЗАБАНЕНЫ В ГРУППЕ {group_name}")
                        elif group_control == "9":
                            print_white("НУ И ПИЗДУЙ")
                            break
                        else:
                            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
                elif pizdec == "2":
                    while True:
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        headers = reg.load_headers()
                        proxy = reg.load_proxy()
                        print_white("[РЕЙД-КОНФИГ]:")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                        print_white("[БАЗА ДАННЫХ]:")
                        print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                        print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                        print_white("[РЕЙД-МЕНЮ]:")
                        print_white("|ВНИМАНИЕ! GroupTokens И BotPodTokens НА ГРУППЫ МОЖНО ПОЛУЧИТЬ ЧЕРЕЗ КОНФИГ!|")
                        print_white("1. СОЗДАТЬ ГРУППУ НА ВСЕХ ТОКЕНАХ")
                        print_white("2. НАСТРОИТЬ ГРУППУ ПОД РЕЙД-ГРУППУ")
                        print_white("3. НАСТРОИТЬ КОНФИГ РЕЙД-ГРУПП")
                        print_white("4. ДОБАВИТЬ РЕЙД-ГРУППЫ В БЕСЕДУ")
                        print_white("5. ВКЛЮЧИТЬ РЕЙД-ГРУППЫ")
                        print_white("6. ОТПРАВИТЬ РЕЙД-ЗОВ В БЕСЕДУ")
                        print_white("7. ПОЙТИ НАХУЙ")
                        group_pizdec = input_white("ВЫБИРАЙ БЛЯ: ")

                        if group_pizdec == "1":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            title = input_white("ВВЕДИ НАЗВАНИЕ ГРУППЫ: ")
                            type_group = input_white("ВВЕДИ ТИП ГРУППЫ (group, event, public): ")
                            description = input_white("ВВЕДИ ОПИСАНИЕ СООБЩЕСТВА (ENTER - ПРОПУСТИТЬ): ")
                            subtype = ''
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()
                            if type_group == "public":
                                print_white("ТИПЫ ПАБЛИКОВ:")
                                print_white("1 - МЕСТО ИЛИ НЕБОЛЬШАЯ КОМПАНИЯ")
                                print_white("2 - КОМПАНИЯ, ОРГАНИЗАЦИЯ ИЛИ ВЕБ-САЙТ")
                                print_white("3 - ИЗВЕСТНАЯ ЛИЧНОСТЬ ИЛИ КОЛЛЕКТИВ")
                                print_white("4 - ПРОИЗВЕДЕНИЕ ИЛИ ПРОДУКЦИЯ")
                                subtype = input_white("ВЫБЕРИ ТИП ПАБЛИКА: ")

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                for login, token in tokens.items():
                                    await topRaid_module.groups_create(session, token, login, title, type_group, description, subtype, proxy)
                        elif group_pizdec == "2":
                            tokens = reg.read_tokens(TOKENS_FILE) 
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            server_id = input_white("ВВЕДИ server_id ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']

                                for login, token in tokens.items():
                                    if await reg.is_admin(session, token, group_id, proxy):
                                        await topRaid_module.group_edit_callback(session, token, login, group_id, group_name, server_id, proxy)
                                        await topRaid_module.group_edit_longpoll(session, token, login, group_id, group_name, proxy)
                                        await topRaid_module.group_edit_raid_settings(session, token, login, group_id, group_name, proxy)
                                    else:
                                        print_white(f"ЛОГИН {login} НЕ ЯВЛЯЕТСЯ АДМИНОМ ГРУППЫ {group_name} ID: {group_id} ")
                        elif group_pizdec == "3":
                            subprocess.Popen(["notepad", "raid_modules/topRaidModules/raidbot_cfg/config.py"])
                        elif group_pizdec == "4":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            botpod_tokens = reg.read_botpod_tokens(TOKENS_FILE)
                            first_token = next(iter(tokens.values()))
                            first_botpod_login = next(iter(botpod_tokens.keys())) 
                            first_botpod_token = next(iter(botpod_tokens.values())) 
                            groups_id = input_white("ВВЕДИ ID РЕЙД-ГРУПП ЧЕРЕЗ ЗАПЯТУЮ: ")
                            groups_id_list = groups_id.split(',')
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                                if chat_ids:
                                    print_white("СПИСОК БЕСЕД:")
                                    for chat in chat_ids:
                                        print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                                    chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                                    chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                                    for group_id in groups_id_list:
                                        group_id = group_id.strip()
                                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                        group_name = group_info['name']
                                        if chat_id:
                                            await topRaid_module.groups_invite(session, first_botpod_token, first_botpod_login, chat_id, chat_title, group_id, group_name, proxy)
                        elif group_pizdec == "5":
                            group_tokens = reg.read_group_tokens(TOKENS_FILE)
                            for group_id, token in group_tokens.items():
                                subprocess.Popen(['python', 'raid_modules/topRaidModules/group_raidbot.py', token], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                print_white(f"ЗАПУЩЕНА РЕЙД-ГРУППА С ID: {group_id}")
                        elif group_pizdec == "6":
                            photo_folder = "raidfiles"
                            attach_file = "message/attach.txt"
                            tokens = reg.read_tokens(TOKENS_FILE)
                            first_token = next(iter(tokens.values()))
                            first_login = next(iter(tokens.keys())) 
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()
                            zov = input_white("ВВЕДИ ЗОВ: ")

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_attach = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_attach = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_photos = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_photos = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                                if chat_ids:
                                    print_white("СПИСОК БЕСЕД:")
                                    for chat in chat_ids:
                                        print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                                    chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                                    chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                                    if chat_id:
                                        await topRaid_module.beseda_zov(session, first_token, first_login, zov, chat_id, chat_title, photo_folder, attach_file, use_attach, use_photos, proxy)
                        elif group_pizdec == "7":
                            print_white("НУ И ПИЗДУЙ")
                            break
                        else:
                            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
                elif pizdec == "3":
                    while True:
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        headers = reg.load_headers()
                        proxy = reg.load_proxy()
                        print_white("[РЕЙД-КОНФИГ]:")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                        print_white("[БАЗА ДАННЫХ]:")
                        print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                        print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                        print_white("[РЕЙД-МЕНЮ]:")
                        print_white("|ВНИМАНИЕ! ОБЯЗАТЕЛЬНО ЗАДАЙТЕ СТИЛЬ ОБЩЕНИЯ!|")
                        print_white("1. НАСТРОИТЬ КОНФИГ НЕЙРОСЕТИ")
                        print_white("2. ФРЕНДЛИСТ НЕЙРОСЕТИ")
                        print_white("3. ВКЛЮЧИТЬ НЕЙРОСЕТЬ ВО ВСЕМ МЕССЕНДЖЕРЕ")
                        print_white("4. ВКЛЮЧИТЬ ТАРГЕТ-НЕЙРОСЕТЬ НА ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППУ")
                        print_white("5. ПОЙТИ НАХУЙ")
                        neuro = input_white("ВЫБИРАЙ БЛЯ: ")

                        if neuro == "1":
                            subprocess.Popen(["notepad", "raid_modules/topRaidModules/neuro_cfg/config.py"])
                        elif neuro == "2":
                            file_path = "base/friendlist_neuro.txt"  
                            friend_id = input_white("ВВЕДИ ID ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППЫ: ")  
                            with open(file_path, "a") as f:  
                                f.write(f"id{friend_id}\n")  
                            print_white(f"ID: {friend_id} УСПЕШНО ДОБАВЛЕН В ФРЕНДЛИСТ НЕЙРОСЕТИ")
                        elif neuro == "3":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"

                            with open('base/friendlist_neuro.txt', 'r') as f:
                                friend_ids = [
                                    int(line.strip().replace('id', '')) 
                                    for line in f 
                                    if line.strip() and line.strip().replace('id', '')
                                ]
                                friend_ids_str = ','.join(str(id) for id in friend_ids)


                            print_white(f"ВКЛЮЧИЛИ НЕЙРОСЕТЬ ВО ВСЕМ МЕССЕНДЖЕРЕ НА ВСЕХ ТОКЕНАХ!")
                            for login, token in tokens.items():
                                subprocess.Popen(['python', 'raid_modules/topRaidModules/neuro_all.py', token, login, friend_ids_str, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif neuro == "4":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            target_id = input_white("ВВЕДИ ID ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППЫ: ")
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"

                            print_white(f"ВКЛЮЧИЛИ ТАРГЕТ-НЕЙРОСЕТЬ НА ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППУ С ID: {target_id} НА ВСЕХ ТОКЕНАХ ВО ВСЕМ МЕССЕНДЖЕРЕ!")
                            for login, token in tokens.items():
                                subprocess.Popen(['python', 'raid_modules/topRaidModules/neuro_target.py', token, login, target_id, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif neuro == "5":
                            print_white("НУ И ПИЗДУЙ")
                            break
                        else:
                            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
                elif pizdec == "4":
                    while True:
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        headers = reg.load_headers()
                        proxy = reg.load_proxy()
                        print_white("[РЕЙД-КОНФИГ]:")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                        print_white("[БАЗА ДАННЫХ]:")
                        print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                        print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                        print_white("[РЕЙД-МЕНЮ]:")
                        print_white("1. АВТО-ЧС ПОЛЬЗОВАТЕЛЯ")
                        print_white("2. АВТО-ЧС ПОЛЬЗОВАТЕЛЯ С ИСЧЕЗАЮЩИМИ СООБЩЕНИЯМИ")
                        print_white("3. АВТО-ЧС ГРУППЫ")
                        print_white("4. ПОЙТИ НАХУЙ")
                        blacklist = input_white("ВЫБИРАЙ БЛЯ: ")

                        if blacklist == "1":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            photo_folder = "raidfiles"
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"
                            attach_file = "message/attach.txt"
                            user_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                            user_id = reg.extract_user_id(user_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                                user_name = f"{user_info['first_name']} {user_info['last_name']}"
                                theme_state = reg.load_theme_state()
                                manager_state = reg.load_manager_state()
                                message_file = select_message_file()
                                index = 1

                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_attach = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_attach = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_photos = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_photos = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                                print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В ЛС {user_name} С ФУНКЦИЕЙ АВТО-ЧС")
                                for login, token in tokens.items():
                                    subprocess.Popen(['python', 'raid_modules/topRaidModules/raidPol_pol_blacklist.py', user_id, token, login, str(index), str(theme_state), message_file, photo_folder, str(use_photos), user_name, str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif blacklist == "2":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            photo_folder = "raidfiles"
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"
                            attach_file = "message/attach.txt"
                            user_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                            expire_ttl = input_white("ВВЕДИ ВРЕМЯ ЧЕРЕЗ КОТОРОЕ УДАЛИТСЯ СООБЩЕНИЕ(В СЕКУНДАХ! 86400 = 24 ЧАСА|3600 = 1 ЧАС|300 = 5 МИНУТ|60 = 1 МИНУТА|15 СЕКУНД!): ")
                            user_id = reg.extract_user_id(user_url)
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                                user_name = f"{user_info['first_name']} {user_info['last_name']}"
                                theme_state = reg.load_theme_state()
                                manager_state = reg.load_manager_state()
                                message_file = select_message_file()
                                index = 1

                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_attach = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_attach = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_photos = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_photos = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                                print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В ЛС {user_name} С ФУНКЦИЕЙ АВТО-ЧС")
                                for login, token in tokens.items():
                                    subprocess.Popen(['python', 'raid_modules/topRaidModules/raidPol_poldel_blacklist.py', user_id, token, login, str(index), str(theme_state), message_file, photo_folder, str(use_photos), user_name, str(expire_ttl), str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif blacklist == "3":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            group_url = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                            group_id = reg.extract_group_id(group_url)
                            photo_folder = "raidfiles"
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"
                            attach_file = "message/attach.txt"
                            headers = reg.load_headers()
                            proxy = reg.load_proxy()

                            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                                first_token = next(iter(tokens.values()))
                                group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                                group_name = group_info['name']
                                manager_state = reg.load_manager_state()
                                message_file = select_message_file()
                                index = 1

                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_attach = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_attach = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                                while True:
                                    user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                    if user_input in ['yes', 'y']:
                                        use_photos = True
                                        break
                                    elif user_input in ['no', 'n']:
                                        use_photos = False
                                        break
                                    else:
                                        print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                                print_white(f"НАЧАЛИ ЛЮТО ДРИСТАТЬ В ЛС ГРУППЫ {group_name} С ФУНКЦИЕЙ АВТО-ЧС")
                                for login, token in tokens.items():
                                    subprocess.Popen(['python', 'raid_modules/topRaidModules/raidGroup_LS_blacklist.py', group_id, token, login, str(index), message_file, photo_folder, str(use_photos), group_name, str(manager_state), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif blacklist == "4":
                            print_white("НУ И ПИЗДУЙ")
                            break
                        else:
                            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
                elif pizdec == "5":
                    while True:
                        theme_state = reg.load_theme_state()
                        manager_state = reg.load_manager_state()
                        headers = reg.load_headers()
                        proxy = reg.load_proxy()
                        print_white("[РЕЙД-КОНФИГ]:")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                        print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                        print_white("[БАЗА ДАННЫХ]:")
                        print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                        print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                        print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                        print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                        print_white("[РЕЙД-МЕНЮ]:")
                        print_white("1. ФРЕНДЛИСТ НАСЕРА")
                        print_white("2. ВКЛЮЧИТЬ НАСЕР ВО ВСЕМ МЕССЕНДЖЕРЕ")
                        print_white("3. ВКЛЮЧИТЬ ТАРГЕТ-НАСЕР НА ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППУ")
                        print_white("4. ПОЙТИ НАХУЙ")
                        naser = input_white("ВЫБИРАЙ БЛЯ: ")

                        if naser == "1":
                            file_path = "base/friendlist_nasera.txt"  
                            friend_id = input_white("ВВЕДИ ID ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППЫ: ")  
                            with open(file_path, "a") as f:
                                f.write(f"id{friend_id}\n")  
                            print_white(f"ID: {friend_id} УСПЕШНО ДОБАВЛЕН В ФРЕНДЛИСТ НАСЕРА")
                        elif naser == "2":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            photo_folder = "raidfiles"
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"
                            attach_file = "message/attach.txt"
                            message_file = select_message_file()

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_attach = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_attach = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            with open('base/friendlist_nasera.txt', 'r') as f:
                                friend_ids = [
                                    int(line.strip().replace('id', '')) 
                                    for line in f 
                                    if line.strip() and line.strip().replace('id', '')
                                ]
                                friend_ids_str = ','.join(str(id) for id in friend_ids)

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_photos = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_photos = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            print_white(f"ВКЛЮЧИЛИ НАСЕР ВО ВСЕМ МЕССЕНДЖЕРЕ НА ВСЕХ ТОКЕНАХ!")
                            for login, token in tokens.items():
                                subprocess.Popen(['python', 'raid_modules/topRaidModules/naser_all.py', token, login, message_file, photo_folder, str(use_photos), friend_ids_str, attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif naser == "3":
                            tokens = reg.read_tokens(TOKENS_FILE)
                            target_id = input_white("ВВЕДИ ID ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППЫ: ")
                            photo_folder = "raidfiles"
                            proxy_path = "base/proxy.txt"
                            headers_path = "base/headers.txt"
                            attach_file = "message/attach.txt"
                            message_file = select_message_file()

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ВЛОЖЕНИЯ? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_attach = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_attach = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            while True:
                                user_input = input_white("НАДО ЛИ ИСПОЛЬЗОВАТЬ ФОТКИ ИЛИ ГИФКИ ИЗ RAIDFILES? (yes/no): ").strip().lower()
                                if user_input in ['yes', 'y']:
                                    use_photos = True
                                    break
                                elif user_input in ['no', 'n']:
                                    use_photos = False
                                    break
                                else:
                                    print_white("АЛО БЛЯТЬ РУССКИМ ЯЗЫКОМ СКАЗАНО ЖЕ БЛЯТЬ yes ИЛИ no")

                            print_white(f"ВКЛЮЧИЛИ ТАРГЕТ-НАСЕР НА ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППУ С ID: {target_id} НА ВСЕХ ТОКЕНАХ ВО ВСЕМ МЕССЕНДЖЕРЕ!")
                            for login, token in tokens.items():
                                subprocess.Popen(['python', 'raid_modules/topRaidModules/naser_target.py', target_id, token, login, message_file, photo_folder, str(use_photos), attach_file, str(use_attach), proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        elif naser == "4":
                            print_white("НУ И ПИЗДУЙ")
                            break
                        else:
                            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
                elif pizdec == "6":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "12":
            while True:
                theme_state = reg.load_theme_state()
                manager_state = reg.load_manager_state()
                headers = reg.load_headers()
                proxy = reg.load_proxy()
                print_white("[РЕЙД-КОНФИГ]:")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ HEADERS: {headers}")
                print_white(f"• ИСПОЛЬЗУЕМЫЙ PROXY: {proxy}")
                print_white("[БАЗА ДАННЫХ]:")
                print_white(f"• АККАУНТОВ: {len(reg.read_accounts('base/accounts.txt'))}")
                print_white(f"• ТОКЕНОВ: {len(reg.read_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ BotPod: {len(reg.read_botpod_tokens(TOKENS_FILE))}")
                print_white(f"• ТОКЕНОВ ГРУПП: {len(reg.read_group_tokens(TOKENS_FILE))}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ СМЕНЫ ТЕМЫ ПРИ РЕЙДЕ: {theme_state}")
                print_white(f"• ТЕКУЩЕЕ СОСТОЯНИЕ ОБХОДА МЕНЕДЖЕРОВ ПРИ РЕЙДЕ: {manager_state}")
                print_white("[РЕЙД-МЕНЮ]:")
                print_white("1. ИЗМЕНЕНИЕ ТЕМЫ ЧАТА ПРИ РЕЙДЕ")
                print_white("2. ОБХОД ЧАТ-МЕНЕДЖЕРОВ")
                print_white("3. АНТИКИК")
                print_white("4. ПОЛУЧЕНИЕ ЦИФРОВОГО АЙДИ ПОЛЬЗОВАТЕЛЯ /// ГРУППЫ")
                print_white("5. ПОЛУЧЕНИЕ ГРУПП ПОЛЬЗОВАТЕЛЯ ГДЕ ОН ЗАПИСАН КАК КОНТАКТ")
                print_white("6. УДАЛИТЬ СПАМ В БЕСЕДЕ /// ЛИЧКЕ /// ДИАЛОГЕ С ГРУППОЙ")
                print_white("7. УДАЛИТЬ СПАМ НА СТЕНЕ")
                print_white("8. УДАЛИТЬ СПАМ ПОД ПОСТОМ")
                print_white("9. УДАЛИТЬ СПАМ ПОД ВИДЕО")
                print_white("10. УДАЛИТЬ СПАМ В ТОПИКЕ")
                print_white("11. УДАЛИТЬ ФОТОГРАФИИ В АЛЬБОМАХ ГРУППЫ")
                print_white("12. КИКНУТЬ ВСЕХ УЧАСТНИКОВ БЕСЕДЫ")
                print_white("13. ПОЙТИ НАХУЙ")
                utils = input_white("ВЫБИРАЙ БЛЯ: ")

                if utils == "1":
                    file_path = 'base/data.json'
                    theme = input_white("ВВЕДИ НОВОЕ СОСТОЯНИЕ Theme (вкл/выкл): ").strip().lower()
                    if theme == 'вкл':
                        new_state = 'True'
                    elif theme == 'выкл':
                        new_state = 'False'
                    else:
                        print_white("СКАЗАНО ЖЕ БЛЯТЬ вкл ИЛИ выкл ЕБЛО ТЫ ТУПОЕ")
                        return

                    reg.update_state_theme(file_path, new_state)
                    print_white(f"СОСТОЯНИЕ Theme ОБНОВЛЕНО НА {new_state}")
                elif utils == "2":
                    file_path = 'base/data.json'
                    theme = input_white("ВВЕДИ НОВОЕ СОСТОЯНИЕ Manager (вкл/выкл): ").strip().lower()
                    if theme == 'вкл':
                        new_state = 'True'
                    elif theme == 'выкл':
                        new_state = 'False'
                    else:
                        print_white("СКАЗАНО ЖЕ БЛЯТЬ вкл ИЛИ выкл ЕБЛО ТЫ ТУПОЕ")
                        return

                    reg.update_state_manager(file_path, new_state)
                    print_white(f"СОСТОЯНИЕ Manager ОБНОВЛЕНО НА {new_state}")
                elif utils == "3":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    proxy_path = "base/proxy.txt"
                    headers_path = "base/headers.txt"
                    print_white(f"АНТИКИК ВКЛЮЧЕН ДЛЯ ВСЕХ ТОКЕНОВ!")
                    for login, token in tokens.items():
                        subprocess.Popen(['python', 'raid_modules/AntiKick.py', token, login, proxy_path, headers_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                elif utils == "4":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    input_value = input_white("ВВЕДИ ССЫЛАЧКУ ИЛИ БУКВЕННЫЙ ID ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППЫ: ").strip()
                    username = input_value.split("/")[-1] if "vk.com" in input_value else input_value
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        result = await utils_module.fetch_id(session, first_token, username, proxy)
                elif utils == "5":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    user_input = input_white("ВВЕДИ ССЫЛАЧКУ ИЛИ ЦИФРОВОЙ ID ПОЛЬЗОВАТЕЛЯ: ")
                    user_id = reg.extract_user_id(user_input)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                        user_name = f"{user_info['first_name']} {user_info['last_name']}"
                        groups = await reg.get_contacts_groups(session, user_id, first_token, proxy)

                        found = False
                        for group in groups:
                            if 'contacts' in group:
                                contacts = group['contacts']
                                contact_ids = [contact['user_id'] for contact in contacts if 'user_id' in contact]
                                if int(user_id) in contact_ids:
                                    print_white(f"{user_name} ЗАПИСАН В КОНТАКТАХ {group['name']} - {group['id']}")
                                    found = True
                        if not found:
                            print_white(f"ГРУППЫ ГДЕ {user_name} ЗАПИСАН В КОНТАКТАХ НЕ НАЙДЕНЫ!")
                elif utils == "6":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ВЫБЕРИ ГДЕ УДАЛЯТЬ СООБЩЕНИЯ")
                    print_white("1. ЛИЧКА")
                    print_white("2. БЕСЕДА")
                    print_white("3. ДИАЛОГ С ГРУППОЙ")
                    choice = input_white("ВЫБИРАЙ БЛЯ: ")

                    if choice == '1':
                        group = 0
                        chatik = 0
                        ls = 1
                        user_input = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ ИЛИ ГРУППЫ: ")
                        peer_id = int(reg.extract_user_id(user_input))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            tasks = []
                            for login, token in tokens.items():
                                message_ids = await reg.get_all_message_ids(session, token, peer_id, proxy)
                                tasks.append(utils_module.delete_messages(session, peer_id, message_ids, login, token, proxy, group, chatik, ls))
                            await asyncio.gather(*tasks)
                    elif choice == '2':
                        group = 0
                        chatik = 1
                        ls = 0
                        first_token = next(iter(tokens.values()))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                            if chat_ids:
                                print_white("СПИСОК БЕСЕД:")
                                for chat in chat_ids:
                                    print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)

                            tasks = []
                            for login, token in tokens.items():
                                user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                                user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                                if user_chat_id:
                                    peer_id = 2000000000 + user_chat_id
                                    message_ids = await reg.get_all_message_ids(session, token, peer_id, proxy)
                                    tasks.append(utils_module.delete_messages(session, peer_id, message_ids, login, token, proxy, group, chatik, ls))
                                    await asyncio.gather(*tasks)
                                else:
                                    print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ С НАЗВАНИЕМ {chat_title} ДЛЯ ЛОГИНА {login}")
                    elif choice == '3':
                        group = 1
                        chatik = 0
                        ls = 0 
                        user_input = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                        peer_id = int(reg.extract_group_id(user_input))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            tasks = []
                            for login, token in tokens.items():
                                message_ids = await reg.get_all_message_ids_group(session, token, peer_id, proxy)
                                tasks.append(utils_module.delete_messages(session, peer_id, message_ids, login, token, proxy, group, chatik, ls))
                            await asyncio.gather(*tasks)
                elif utils == "7":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ВЫБЕРИ ГДЕ БУДЕМ УДАЛЯТЬ ПОСТЫ")
                    print_white("1. СТРАНИЦА ПОЛЬЗОВАТЕЛЯ")
                    print_white("2. ГРУППА")
                    choice = input_white("ВЫБИРАЙ БЛЯ: ")

                    if choice == '1':
                        user_input = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ПОЛЬЗОВАТЕЛЯ: ")
                        user_id = int(reg.extract_user_id(user_input))
                        first_token = next(iter(tokens.values()))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                            user_name = f"{user_info['first_name']} {user_info['last_name']}"
                            owner_id = user_id

                            tasks = []
                            for login, token in tokens.items():
                                tasks.append(utils_module.delete_wall_posts_pol(session, owner_id, token, login, user_name, proxy))
                            await asyncio.gather(*tasks)
                            print_white(f"ВСЕ ПОСТЫ УСПЕШНО БЫЛИ УДАЛЕНЫ НА СТРАНИЦЕ {user_name}")
                    elif choice == '2':
                        user_input = input_white("ВВЕДИ ССЫЛКУ ИЛИ ID ГРУППЫ: ")
                        group_id = int(reg.extract_group_id(user_input))
                        first_token = next(iter(tokens.values()))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                            group_name = group_info['name']
                            owner_id = group_id

                            tasks = []
                            for login, token in tokens.items():
                                tasks.append(utils_module.delete_wall_posts_group(session, owner_id, token, login, group_name, proxy))
                            await asyncio.gather(*tasks)
                            print_white(f"ВСЕ ПОСТЫ УСПЕШНО БЫЛИ УДАЛЕНЫ В ГРУППЕ {group_name}")
                elif utils == "8":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("ВЫБЕРИ ГДЕ БУДЕМ УДАЛЯТЬ КОММЕНТАРИИ К ПОСТУ")
                    print_white("1. СТРАНИЦА ПОЛЬЗОВАТЕЛЯ")
                    print_white("2. ГРУППА")
                    choice = input_white("ВЫБИРАЙ БЛЯ: ")

                    if choice == '1':
                        user_input = input_white("ВВЕДИ ССЫЛКУ НА ПОСТ НА СТРАНИЦЕ ПОЛЬЗОВАТЕЛЯ: ")
                        user_id = int(reg.extract_user_id(user_input))
                        post_id = reg.extract_post_id(user_input)
                        first_token = next(iter(tokens.values()))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            user_info = await reg.get_user_info(session, first_token, user_id, proxy)
                            user_name = f"{user_info['first_name']} {user_info['last_name']}"
                            owner_id = user_id

                            tasks = []
                            for login, token in tokens.items():
                                tasks.append(utils_module.delete_wall_post_comments_pol(session, owner_id, post_id, token, login, user_name, proxy))
                            await asyncio.gather(*tasks)
                            print_white(f"ВЕСЬ СРАЧ БЫЛ УСПЕШНО УДАЛЕН С КОММЕНТОВ ПОСТА С ID: {post_id} НА СТРАНИЦЕ {user_name}")
                    elif choice == '2':
                        user_input = input_white("ВВЕДИ ССЫЛКУ НА ПОСТ В ГРУППЕ: ")
                        group_id = int(reg.extract_group_id(user_input))
                        post_id = reg.extract_post_id(user_input)
                        first_token = next(iter(tokens.values()))

                        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                            group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                            group_name = group_info['name']
                            owner_id = group_id

                            tasks = []
                            for login, token in tokens.items():
                                tasks.append(utils_module.delete_wall_post_comments_group(session, owner_id, post_id, token, login, group_name, proxy))
                            await asyncio.gather(*tasks)
                            print_white(f"ВЕСЬ СРАЧ БЫЛ УСПЕШНО УДАЛЕН С КОММЕНТОВ ПОСТА С ID: {post_id} В ГРУППЕ {group_name}")
                elif utils == "9":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    user_url = input_white("ВВЕДИ ССЫЛКУ НА ВИДЕО: ")
                    owner_id = reg.extract_owner_id(user_url)
                    video_id = reg.extract_video_id(user_url)
                    full = video_id.index('_')
                    video_id = video_id[full + 1:]
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(utils_module.delete_video_comments(session, owner_id, video_id, token, login, proxy))
                        await asyncio.gather(*tasks)
                        print_white(f"ВЕСЬ СРАЧ БЫЛ УСПЕШНО УДАЛЕН С КОММЕНТОВ ВИДЕО С ID: {video_id}")
                elif utils == "10":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    topic_url = input_white("ВВЕДИ ССЫЛКУ НА ТОПИК: ")
                    group_id = reg.extract_group_id(topic_url)
                    topic_id = reg.extract_topic_id(topic_url)
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    first_token = next(iter(tokens.values()))

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']

                        tasks = []
                        for login, token in tokens.items():
                            tasks.append(utils_module.delete_topic_comments_group(session, group_id, topic_id, token, login, group_name, proxy))
                        await asyncio.gather(*tasks)
                        print_white(f"ВЕСЬ СРАЧ БЫЛ УСПЕШНО УДАЛЕН С ТОПИКА С ID: {topic_id} В ГРУППЕ {group_name}")
                elif utils == "11":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    album_url = input_white("ВВЕДИ ССЫЛКУ НА ФОТОАЛЬБОМ: ")
                    num_photos = int(input_white("ВВЕДИ КОЛ-ВО ФОТОГРАФИЙ ДЛЯ УДАЛЕНИЯ: "))
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()
                    print_white("НАЧАЛИ УДАЛЕНИЕ ФОТОГРАФИЙ ИЗ ФОТОАЛЬБОМА, ПРОЦЕСС ДОВОЛЬНО ДЛИТЕЛЬНЫЙ, ОЖИДАЙ!")

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        first_token = next(iter(tokens.values()))
                        group_id, album_id = reg.extract_album_info(album_url)
                        group_id = abs(int(group_id))  
                        album_id = abs(int(album_id))
                        owner_id = -group_id

                        group_info = await reg.get_group_info(session, first_token, group_id, proxy)
                        group_name = group_info['name']
                        album_info = await reg.get_album_info(session, first_token, group_id, album_id, proxy)
                        album_name = album_info['title']

                        tasks = []
                        for login, token in tokens.items():
                            user_info = await reg.get_token_info(session, token, proxy)
                            user_id = user_info['id']
                            all_photos = await reg.get_all_photos_album(session, token, owner_id, album_id, proxy)
                            user_photos = [photo for photo in all_photos if photo['user_id'] == user_id]
                            for photo in user_photos[:num_photos]:
                                await utils_module.delete_photo_album(session, token, photo, login, album_name, group_name, owner_id, proxy)

                        print_white(f"ЗАКОНЧИЛИ УДАЛЕНИЕ ФОТОГРАФИЙ ИЗ ФОТОАЛЬБОМА {album_name} В ГРУППЕ {group_name}")
                elif utils == "12":
                    tokens = reg.read_tokens(TOKENS_FILE)
                    first_token = next(iter(tokens.values()))
                    headers = reg.load_headers()
                    proxy = reg.load_proxy()

                    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), headers=headers) as session:
                        chat_ids = await reg.get_chat_ids(session, first_token, proxy)
                        if chat_ids:
                            print_white("СПИСОК БЕСЕД:")
                            for chat in chat_ids:
                                print_white(f"ID: {chat['chat_id']}, НАЗВАНИЕ: {chat['title']}")
                            chat_id = int(input_white("ВВОДИ ID БЕСЕДЫ: "))
                            chat_title = next((chat['title'] for chat in chat_ids if chat['chat_id'] == chat_id), None)
                        print_white(f"НАЧАЛИ КИКАТЬ ЕБЛАНЧИКОВ ИЗ БЕСЕДЫ {chat_title}")

                        tasks = []
                        for login, token in tokens.items():
                            user_chat_ids = await reg.get_chat_ids(session, token, proxy)
                            user_chat_id = next((chat['chat_id'] for chat in user_chat_ids if chat['title'] == chat_title), None)
                            if user_chat_id is not None:
                                tasks.append(utils_module.kick_all_members(session, token, user_chat_id, login, chat_title, proxy))
                            else:
                                print_white(f"НЕ УДАЛОСЬ НАЙТИ БЕСЕДУ С НАЗВАНИЕМ {chat_title} ДЛЯ ЛОГИНА {login}")

                        await asyncio.gather(*tasks)
                        print_white(f"КИКНУЛИ ВСЕХ ЕБЛАНЧИКОВ ИЗ БЕСЕДЫ {chat_title}")
                elif utils == "13":
                    print_white("НУ И ПИЗДУЙ")
                    break
                else:
                    print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 
        elif choice == "13":
            print_white("ДО СВЯЗИ")
            break
        else:
            print_white("НЕВЕРНО ВЫБРАЛ ЕБЛАН ПРОБУЙ СНОВА") 

def select_message_file():
    print_white("ОТКУДА БУДЕМ СРАТЬ:")
    message_files = [
        "args.txt",
        "message_1.txt",
        "message_2.txt",
        "message_3.txt",
        "smile.txt",
        "zalgo.txt"
    ]
    for i, file in enumerate(message_files, 1):
        print_white(f"{i}. {file}")
    
    selected_index = int(input_white("ВЫБИРАЙ БЛЯ: ")) - 1
    return f"message/{message_files[selected_index]}"

def zalgo_text(text, intensity):
    zalgo_chars = [chr(i) for i in range(0x0300, 0x036F + 1)]
    levels = {1: (3, 6), 2: (6, 12), 3: (12, 20)}
    return ''.join(char + ''.join(random.choice(zalgo_chars) for _ in range(random.randint(*levels[intensity]))) for char in text)

asyncio.run(trahadrom())