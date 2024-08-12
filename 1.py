import telebot

TELEGRAM_TOKEN = '5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA'
bot1 = telebot.TeleBot(TELEGRAM_TOKEN)

# bot1.send_message(chat_id=662482931, text='test')
bot1.send_message(chat_id=662482931, text="Технічні роботи на сервері.")
pic = open(f'tech.webm', 'rb')
bot1.send_sticker(chat_id=662482931, sticker=pic)
