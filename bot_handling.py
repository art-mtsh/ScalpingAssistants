# telegram_bot.py
import logging
import time

import telebot
import os
import chat_ids


TELEGRAM_TOKEN = '7458821979:AAEzkL3X-U6BVKwoS1Vnh5bNqMZYizivTIw'
bot4 = telebot.TeleBot(TELEGRAM_TOKEN)

# File to store user chat IDs
chat_ids_file = "user_chat_ids.txt"

# Load existing chat IDs
existed_chat_ids = set(chat_ids.get_existed_chat_ids())

@bot4.message_handler(commands=['start'])
def send_welcome(message):
    print(f"Received start command")
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)
    msg = (
"""🇺🇦 Слава Україні!

Отож ти приєднався(-лась) до розсилки.
Поточна сесія аналізу вже активна, тому просто очікуй на повідомлення.

Щоб дізнатись як функціонує бот - тицяй /how_it_works.
Щоб дізнатись як користуватись - тицяй /how_to_use
Щоб отримати вихідний код - зв'яжись зі мною.
Переключиться на русский - жми /switch_to_ru

<i>Усі повідомлення тут - безкоштовна інформація. Ніяких рекомендацій чи закликів до дій на фінансових ринках!</i>
""")

    bot4.send_message(chat_id, msg, parse_mode="HTML")

@bot4.message_handler(commands=['switch_to_ru'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

#     bot4.send_message(message.chat.id,
# """
# Ти шо на приколі? Яка російська 😂
# Русскіє і русскагаварящіє ідуть нахуй!
# """)
    pic = open(f'funnyhaha.gif', 'rb')
    bot4.send_animation(chat_id, pic)

@bot4.message_handler(commands=['how_to_use'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    msg = """
Якщо є зайві кошти - краще відправ їх на допомогу Сил Оборони України 🇺🇦 

Задонатив? Щось залишилось? Знач слухай:

1. Отримавши сигнал, поглянь уважно на скрін.
2. Якщо на скріні ти бачиш червону пунктирну лінію - це сайз, його розмір вказаний в описі.
3. Те, що бот прислав тобі картинку - НЕ значить, що сайз досі там стоїть.
4. Те, що відкривши термінал, ти бачиш сайз - НЕ значить що він монолітний і не зніметься!
5. Щоб перевірити довговічність і вагу сайзу (для ринку) треба відкрити термінал і поспостерігати за щільністю. 
6. Якщо вона стоїть, не знімається навіть коли ціна в парі тіків від неї або навіть вдаряється об неї - це твій шанс.

Торгувати відбій, пробій, хибний пробій - на твій розсуд. Зважай на загальну кон'юнктуру ринку м1, м5, Н1, на тренди і лінії S/R.
Не лови ножі, не торгуй ПРОТИ ринку.

Вдалого полювання 💵

<i>Усі повідомлення тут - безкоштовна інформація. Ніяких рекомендацій чи закликів до дій на фінансових ринках!</i>
"""
    pic = open(f'exam1.jpg', 'rb')
    bot4.send_photo(chat_id, pic, msg, parse_mode="HTML")

@bot4.message_handler(commands=['no_size'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    bot4.send_message(message.chat.id,
"""
Якшо червоної лінії на скріншоті нема - значить сайз знаходиться критично близько до рамки. Це графічний баг, просто там лінія не малюється, я хз, колись поправлю. В такому разі дивись просто на ціну в описі.

<i>Усі повідомлення тут - безкоштовна інформація. Ніяких рекомендацій чи закликів до дій на фінансових ринках!</i>
""", parse_mode="HTML")

@bot4.message_handler(commands=['how_it_works'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    msg = '''
Отже, як це працює...

Бот опрацьовує 200+ інструментів. 
Аналізує і SPOT і FUTURES. 
Увесь аналіз проводиться на m1.

Частина 1. Пошук інструментів:
1. Отримує перелік інструментів з ендпоінта
<i>fapi binance com/fapi/v1/exchangeInfo</i>
2. Фільтрує за розміром тіка(%) та середньому ATR(%) на м1:
- менший розмір тіка дає можливість більш точного маневрування в стакані
- більший розмір середнього ATR(%) на м1 дає розуміння скільки відсотків пролетить ціна за 1,2,3.. хв твоєї позиції
3. Формує список інструментів.
4. Чекає 20 секунд.
5. По кожному інструменту починається перевірка.

Частина 2. Пошук екстремумів і сайзів НА них.
1. ЩОХВИЛИНИ завантажуємо бари і стакан по споту і фючу для кожного інструмента з ендпоінтів:
<i>fapi binance com/fapi/v1/depth?symbol=...</i>
<i>api binance com/api/v3/depth?symbol=...</i>
<i>fapi binance com/fapi/v1/klines?symbol=...</i>
<i>api binance com/api/v3/klines?symbol=...</i>
2. Пошук екстремумів і сайзів на них.
3. Перевірка знайденого сайзу.

Частина 3. Перевірка сайзу НАД ціною (для ask):
✅ Ціна сайзу вища поточної.
✅ Сайз на екстремумі з кімнатою зліва в 10-30 хвилин.
✅ Сайз максимальний на 200 askів.
✅ Сайз ВДВІЧІ більший за наступний по розміру (виділяється в стакані).
✅ Сайз більший за середній обєм останніх 100 хвилин (m1).
✅ Сайз знаходиться в 3х ATRах від поточної ціни.

для сайзів ПІД ціною (для bid) - той самий принцип

Важливо!
- Перевірка відбувається і для спота і для фючерсів.
- Вперше знайдений сайз - не публікується. Тільки якщо через хвилину він і досі на тому ж місці - формується скрін і відправляється сюди. Якщо він продовжує там стояти - скріни надходитимуть щохвилини.

<i>Усі повідомлення тут - безкоштовна інформація. Ніяких рекомендацій чи закликів до дій на фінансових ринках!</i>
'''
    bot4.send_message(chat_id, msg, parse_mode="HTML")

@bot4.message_handler(func=lambda message: True)
def handle_message(message):
    bot4.send_message(message.chat.id, "Повідомлень я не розумію, сорян 🤷🏻‍♂️")
    chat_id = message.chat.id
    pic = open(f'sticker.webm', 'rb')
    bot4.send_sticker(chat_id, pic)

# Function to send a photo to all users
def send_photo_to_all_users(pic, msg):
    for chat_id in existed_chat_ids:
        try:
            bot4.send_photo(chat_id, pic, msg)
        except Exception as e:
            print(f"Failed to send photo to {chat_id}: {e}")


# def start_bot():
#     print("Bot polling started.")
#
#     while True:
#         try:
#             bot4.polling(none_stop=True, timeout=10)  # Polling with a timeout
#             print("Polling is running...")
#             time.sleep(1)
#         except Exception as e:
#             print(f"Polling encountered an error: {e}")
#             time.sleep(5)  # Wait a bit before retrying in case of erro

def start_bot():
    bot4.polling(none_stop=True)
    while True:
        print('still polling')
        time.sleep(5)

# if __name__ == "__main__":
#     start_bot()