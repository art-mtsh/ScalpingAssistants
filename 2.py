import telebot

TELEGRAM_TOKEN1 = '5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA'
personal_bot = telebot.TeleBot(TELEGRAM_TOKEN1)

link = "https://docs.google.com/document/d/14brzteeFj9rdpm55vImldH1pAjrUnvJMK4kpoYmDR88/edit?usp=sharing"
msg = f"<a href='{link}'>Детальний опис</a>"

personal_bot.send_message(662482931, msg, parse_mode="HTML")
