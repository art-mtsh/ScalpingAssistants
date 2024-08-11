# telegram_bot.py
import logging
import time

import telebot
import os
import chat_ids


TELEGRAM_TOKEN = '7458821979:AAEzkL3X-U6BVKwoS1Vnh5bNqMZYizivTIw'
bot4 = telebot.TeleBot(TELEGRAM_TOKEN)
disclaimer = '<i>Торгівля криптовалютами має високі ризики та може призвести до значних фінансових втрат! Уся відповідальність лежить на користувачеві бота.</i>'

# File to store user chat IDs
chat_ids_file = "user_chat_ids.txt"

# Load existing chat IDs
existed_chat_ids = set(chat_ids.get_existed_chat_ids())


# Function to send a photo to all users
for chat_id in existed_chat_ids:
    try:
        msg = 'На сьогодні робота завершена.'
        bot4.send_message(chat_id, msg)
    except Exception as e:
        print(f"Failed to send photo to {chat_id}: {e}")


