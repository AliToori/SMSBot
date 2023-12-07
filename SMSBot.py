#!/usr/bin/env python3
"""
    *******************************************************************************************
    SMSBot: A bot for sending SMS and Voice Calls to phone numbers.
    Author: Ali Toori, Python Developer
    Client: Tomer Daniel
    *******************************************************************************************
"""
import json
import logging.config
import os
import random
from datetime import datetime
from multiprocessing import freeze_support
from pathlib import Path
from time import sleep
import concurrent.futures

import pandas as pd
import pyfiglet
import requests
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class SMSBot:
    def __init__(self):
        self.PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
        self.file_settings = str(self.PROJECT_ROOT / 'SMSRes/Settings.json')
        self.file_phone_numbers = self.PROJECT_ROOT / 'SMSRes/PhoneNumbers.csv'
        self.settings = self.get_settings()
        self.LOGGER = self.get_logger()
        self.driver = None

    # Get self.LOGGER
    @staticmethod
    def get_logger():
        """
        Get logger file handler
        :return: LOGGER
        """
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            'formatters': {
                'colored': {
                    '()': 'colorlog.ColoredFormatter',  # colored output
                    # --> %(log_color)s is very important, that's what colors the line
                    'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
                    'log_colors': {
                        'DEBUG': 'green',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                    },
                },
                'simple': {
                    'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
                },
            },
            "handlers": {
                "console": {
                    "class": "colorlog.StreamHandler",
                    "level": "INFO",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "filename": "SMSBot.log",
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 3
                },
            },
            "root": {"level": "INFO",
                     "handlers": ["console", "file"]
                     }
        })
        return logging.getLogger()

    @staticmethod
    def enable_cmd_colors():
        # Enables Windows New ANSI Support for Colored Printing on CMD
        from sys import platform
        if platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    @staticmethod
    def banner():
        pyfiglet.print_figlet(text='____________ SMSBot\n', colors='RED')
        print('Author: Ali Toori\n'
              'Website: https://instagram.com/botflocks/\n'
              '************************************************************************')

    def get_settings(self):
        """
        Creates default or loads existing settings file.
        :return: settings
        """
        if os.path.isfile(self.file_settings):
            with open(self.file_settings, 'r') as f:
                settings = json.load(f)
            return settings
        settings = {"Settings": {
            "WaitForMsg": 5
        }}
        with open(self.file_settings, 'w') as f:
            json.dump(settings, f, indent=4)
        with open(self.file_settings, 'r') as f:
            settings = json.load(f)
        return settings

    # Get random user-agent
    def get_user_agent(self):
        file_uagents = self.PROJECT_ROOT / 'SMSRes/user_agents.txt'
        with open(file_uagents) as f:
            content = f.readlines()
        u_agents_list = [x.strip() for x in content]
        return random.choice(u_agents_list)

    # Get random user-agent
    def get_proxy(self):
        file_proxies = self.PROJECT_ROOT / 'SMSRes/proxies.txt'
        with open(file_proxies) as f:
            content = f.readlines()
        proxy_list = [x.strip() for x in content]
        proxy = random.choice(proxy_list)
        self.LOGGER.info(f'Proxy selected: {proxy}')
        return proxy

    # Get web driver
    def get_driver(self, proxy=False, headless=False):
        # For absolute chromedriver path
        DRIVER_BIN = str(self.PROJECT_ROOT / "SMSRes/bin/chromedriver.exe")
        service = Service(executable_path=DRIVER_BIN)
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-blink-features")
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument(F'--user-agent={self.get_user_agent()}')
        if proxy:
            options.add_argument(f"--proxy-server={self.get_proxy()}")
        if headless:
            options.add_argument('--headless')
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def send_telegram_msg(self, msg):
        bot_token = self.settings["Settings"]["BotToken"]
        chat_id = self.settings["Settings"]["ChatID"]
        self.LOGGER.info(f"Sending message to Telegram ChatBot: {msg}")
        send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={msg}'
        response = requests.get(url=str(send_text))
        return response.json()

    def get_telegram_msg(self, bot_token):
        # bot_token = '5684091804:AAFovNuL9EIthkdLWw3HS-ZJbuw8ELPfnh8'
        # chat_id = '1442986099'
        # proxy = self.get_proxy()
        # proxy = "154.30.136.43:8000"
        # http_proxy = f"http://{proxy}"
        # https_proxy = f"http://{proxy}"
        # ftp_proxy = f"ftp://{proxy}"
        # proxies = {"http": http_proxy, "https": https_proxy}
        chat_url = f'https://api.telegram.org/bot{bot_token}/getUpdates'
        response = requests.get(url=str(chat_url))
        # response = requests.get(url=str('https://fileautomator.herokuapp.com/get_msg/'))
        # print(response)
        return response.json()

    # Finish and quit browser
    def finish(self, driver):
        try:
            self.LOGGER.info(f'Closing browser session')
            driver.close()
            driver.quit()
        except WebDriverException as exc:
            self.LOGGER.info(f'Issue while closing browser: {exc.args}')

    @staticmethod
    def wait_until_visible(driver, css_selector=None, element_id=None, name=None, class_name=None, tag_name=None, duration=10000, frequency=0.01):
        if css_selector:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        elif element_id:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.ID, element_id)))
        elif name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.NAME, name)))
        elif class_name:
            WebDriverWait(driver, duration, frequency).until(
                EC.visibility_of_element_located((By.CLASS_NAME, class_name)))
        elif tag_name:
            WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.TAG_NAME, tag_name)))

    def get_sms_airbnb(self, phone_number):
        country_code = phone_number.split(' ')[0]
        phone_number = phone_number.split(' ')[1]
        url = "https://www.airbnb.com/signup_login"
        driver = self.get_driver(proxy=False, headless=False)
        driver.get(url=url)
        self.LOGGER.info(f"Waiting for AirBnB to load")
        collection, collection_name, best_offer, premium = '', '', '', ''
        # key = input(f'Enter a Key')
        # if key == 'n':
        #     continue
        # Wait for country code dropdown Menu
        try:
            self.wait_until_visible(driver=driver, css_selector='[id="country"]', duration=10)
            sleep(3)
            selector = Select(webelement=driver.find_element(By.CSS_SELECTOR, '[id="country"]'))
            # options = [option for option in selector.options if option.text.startswith(country_code)]
            options = [option.text for option in selector.options if country_code in option.text]
            # selected_option = options[0]
            # if not selected_option.is_selected():
            #     selected_option.click()
            # Select Israel
            selector.select_by_visible_text(text=options[0])
            # Enter phone number
            driver.find_element(By.CSS_SELECTOR, '[id="phoneInputphoneNumber"]').send_keys(phone_number)
            sleep(3)
            # Click Continue button
            driver.find_element(By.CSS_SELECTOR, '[class="_kaq6tx"]').click()
        except:
            pass
        try:
            # Wait for the CODE input box
            self.LOGGER.info(f'Waiting for Code input box')
            self.wait_until_visible(driver=driver, css_selector='[id="phone-verification-code-form__code-input"]', duration=25000)
            msg = f'SMS code has been sent: {country_code} {phone_number}'
            self.send_telegram_msg(msg=msg)
            self.LOGGER.info(msg)
        except:
            pass
        try:
            # Wait for the More Options button to send voice call
            self.LOGGER.info(f'Waiting for More Options button')
            self.wait_until_visible(driver=driver, css_selector='[class="_za4ekfm"]', duration=25)
            driver.find_element(By.CSS_SELECTOR, '[class="_za4ekfm"]').click()
            self.LOGGER.info(f'Waiting for Phone call button')
            self.wait_until_visible(driver=driver, css_selector='[id="phone_call-row-radio-button"]', duration=25)
            driver.find_element(By.CSS_SELECTOR, '[id="phone_call-row-radio-button"]').click()
            self.wait_until_visible(driver=driver, css_selector='[type="submit"]', duration=25)
            driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
        except:
            pass
        try:
            # Wait for the CODE input box
            self.LOGGER.info(f'Waiting for Code input box')
            self.wait_until_visible(driver=driver, css_selector='[id="phone-verification-code-form__code-input"]', duration=5)
            msg = f'Voice call code has been sent: {country_code} {phone_number}'
            self.send_telegram_msg(msg=msg)
            self.LOGGER.info(msg)
        except:
            try:
                # Wait for the confirmation or error
                self.LOGGER.info(f'Waiting for More Options button')
                self.wait_until_visible(driver=driver, css_selector='[class="_121z06r2"]', duration=5)
                popup_msg = driver.find_element(By.CSS_SELECTOR, '[class="_121z06r2"]').text
                if "We don't support this verification method in your country" in popup_msg:
                    msg = f'Voice call code cannot be sent: {country_code} {phone_number}, {popup_msg}'
                    self.send_telegram_msg(msg=msg)
                    self.LOGGER.info(msg)
            except:
                pass
        self.finish(driver=driver)

    def main(self):
        freeze_support()
        self.enable_cmd_colors()
        self.banner()
        self.LOGGER.info(f'SMSBot launched')
        bot_token = self.settings["Settings"]["BotToken"]
        chat_id = self.settings["Settings"]["ChatID"]
        wait_for_msg = self.settings["Settings"]["WaitForMsg"]
        # phone_numbers = pd.read_csv(self.file_phone_numbers, index_col=None)
        # phone_numbers = [address["PhoneNumber"] for address in phone_numbers.iloc]
        # self.get_sms_airbnb(phone_number="")
        old_msg_id = 14
        while True:
            self.LOGGER.info(f"Checking new phone number in {wait_for_msg} secs")
            sleep(wait_for_msg)
            msg = self.get_telegram_msg(bot_token=bot_token)
            msg_id = msg["result"][-1]["message"]["message_id"]
            self.LOGGER.info(f"Message: {msg_id}")
            self.LOGGER.info(f"New Message: {msg_id != old_msg_id}")
            if msg_id != old_msg_id:
                old_msg_id = msg_id
                phone_number = str(msg["result"][-1]["message"]["text"])
                if '/start' in phone_number:
                    continue
                if not phone_number.startswith('+') and not phone_number.find(' '):
                    self.LOGGER.info(f"Wrong phone number format: {phone_number}")
                    continue
                self.LOGGER.info(f"Processing Phone Number: {phone_number}")
                self.get_sms_airbnb(phone_number=phone_number)
        # chunk = round(len(phone_numbers) / thread_counts)
        # address_chunks = [phone_numbers[x:x + chunk] for x in range(len(phone_numbers))]
        # with concurrent.futures.ThreadPoolExecutor(max_workers=thread_counts) as executor:
        #     executor.map(self.get_address_details, address_chunks)
        # self.LOGGER.info(f'Process completed successfully!')


if __name__ == '__main__':
    SMSBot().main()
