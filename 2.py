import threading
import time
from datetime import datetime
import telebot

# Your bot token
bot = telebot.TeleBot("5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA")

# @bot.message_handler(commands=['start'])
# def send_welcome(message):
#     ch_id = [662482931, 317994467]
#     for id in ch_id:
#         bot.send_message(id, f'Прийшло?')
#
# bot.infinity_polling()

ch_id = [662482931, 317994467]
for id in ch_id:
    bot.send_message(id, f'Прийшло?')