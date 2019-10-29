#!/usr/bin/env python3

from telegram.ext import Updater, CommandHandler
from SonarrAPI.sonarr.sonarr_api import SonarrAPI
from datetime import datetime, timedelta
from requests.exceptions import ConnectionError
from wakeonlan import send_magic_packet
from keys import TELEGRAM_TOKEN, SONARR_TOKEN
import subprocess

import logging
import time
import requests
import threading
import time
import random
import string

MAC_ADDRESS = '1C-87-2C-B7-DE-09'
IP_ADDRESS = '192.168.0.38'

SONARR_API_URL = 'http://{}:8989/api'.format(IP_ADDRESS)
snr = SonarrAPI(SONARR_API_URL, SONARR_TOKEN)

days = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']
dst = time.localtime().tm_isdst


def randomString(stringLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def get_time(date):
    s_time = date[11:][:-4]
    time = list(map(int, s_time.split(":")))
    time[0] += dst
    return ("{:02d}:{:02d}".format(time[0], time[1]))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_day(date):
    year, month, day = map(int, date.split("-"))
    return days[datetime(year, month, day).weekday()]

def get_ep(res, print_day = True):
    ret = ""
    msg_format = "{} - S{}E{} - {}\n"
    if(not print_day):
        msg_format = msg_format[:-6] + "\n"
    for item in res:
        airs = ''
        if(print_day):
            if(item['hasFile'] == True):
                airs = 'AIRED AT: '
            else:
                airs = 'AIRS AT: '
            airs += get_time(item['airDateUtc'])
        ret += (msg_format.format(item['series']['title'], item['seasonNumber'], item['episodeNumber'], airs))
    return ret[:-1]

def send_greeting(update):
    greeting = "Ohayou"
    name = "Senpai"
    update.message.reply_text('{} {} :)'.format(greeting, name))

def sleepy(update):
    update.message.reply_text("Onii-chan I'm sleepy, try /wakiewakie")
    update.message.reply_sticker(sticker='CAADBQADJAEAAgYDlgFSb-kXX51LbQI')

def schedule(update, day_name, days_start=0, days_end=None, greeting=False):
    if(days_end == None):
        days_end = days_start + 1
    start = (datetime.today() + timedelta(days=days_start)).strftime('%Y-%m-%d')
    end = (datetime.today() + timedelta(days=days_end)).strftime('%Y-%m-%d')

    try:
        res = snr.get_calendar_by_date(start, end)
        if(greeting):
            send_greeting(update)

        if(len(res) == 0):
            update.message.reply_text('Nothing on show {}.'.format(day_name))
        else:
            update.message.reply_text("This is how {} schedule looks like: {}\n".format(day_name, get_ep(res, days_end - days_start)))
    except ConnectionError:
        sleepy(update)


def hello(update, context):
    schedule(update, "Today", 0, greeting=True)

def today_calendar(update, context):
    schedule(update, "Today", 0)

def tomorrow_calendar(update, context):
    schedule(update, "Tomorrow", 1)

def week_calendar(update, context):
    days_start = 0
    days_end = 7

    try:
        while(days_start < days_end):
            start = (datetime.today() + timedelta(days=days_start)).strftime('%Y-%m-%d')
            end = (datetime.today() + timedelta(days=days_start + 1)).strftime('%Y-%m-%d')
            res = snr.get_calendar_by_date(start, end)
            DAY = get_day(start)
            if(len(res) == 0):
                update.message.reply_text('Nothing on show on {}.'.format(DAY))
            else:
                update.message.reply_text("Schedule for {}:\n{}".format(DAY, get_ep(res, False)))
            days_start += 1
    except ConnectionError:
        sleepy(update)


def download_queue(update, context):
    try:
        res = snr.get_queue()
        if(res):
            dls = 'Onii-chan here is your download Queue:\n'
            for item in res:
                dls += "{} - S{}E{} - {:.2f}%\n".format(item['series']['title'], item['episode']['seasonNumber'], item['episode']['episodeNumber'], 100 - ((item['sizeleft'] / item['size']) * 100))
            dls = dls[:-1]
            update.message.reply_text(dls)
        else:
            update.message.reply_text('Onii-chan,\nyou have no downloads Queued.')

    except ConnectionError:
        sleepy(update)

def wakiewakie(update, context):
    send_magic_packet(MAC_ADDRESS)
    update.message.reply_sticker(sticker='CAADBQADIAEAAgYDlgEvPT4smrSbTQI')

threads = {}

def async_ping(url, name, update):
    i = 1
    while i < 65:
        requests.get(url, timeout=10)
        time.sleep(6 * i)
        i += 1

    update.message.reply_text('Onii-chan,\n I\'m Sleepy.')
    update.message.reply_sticker(sticker='CAADBQADJAEAAgYDlgFSb-kXX51LbQI')

    del threads[name]

def ping_plex(update, context):
    name = randomString()
    url = "http://{}:32400/web/index.html".format(IP_ADDRESS)
    x = threading.Thread(target=async_ping, args=(url,name,update,))
    threads[name] = x
    x.start()

def git_update(update, context):
    with subprocess.Popen(["git", "pull", "origin", "master"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as child:
        stdout = "\n".join(child.communicate()[0].decode("utf-8").split("\\n"))
        ret = child.returncode
        if ret == 0:
            update.message.reply_text("Update Successful, Please Restart Bot.")
        update.message.reply_text(stdout)


updater = Updater(TELEGRAM_TOKEN, use_context=True)

updater.dispatcher.add_handler(CommandHandler(['ohayou' ,'hello', 'hi', 'hey', 'morning', 'goodmorning'], hello))
updater.dispatcher.add_handler(CommandHandler('today', today_calendar))
updater.dispatcher.add_handler(CommandHandler('tomorrow', tomorrow_calendar))
updater.dispatcher.add_handler(CommandHandler('week', week_calendar))
updater.dispatcher.add_handler(CommandHandler(['queue', 'download', 'downloads'], download_queue))
updater.dispatcher.add_handler(CommandHandler('wakiewakie', wakiewakie))
updater.dispatcher.add_handler(CommandHandler('ping', ping_plex))
updater.dispatcher.add_handler(CommandHandler('update', git_update))

updater.start_polling()
updater.idle()
