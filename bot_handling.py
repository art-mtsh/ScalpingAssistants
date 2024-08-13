# telegram_bot.py
import logging
import time

import telebot
import os
import chat_ids

TELEGRAM_TOKEN1 = '5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA'
bot1 = telebot.TeleBot(TELEGRAM_TOKEN1)

TELEGRAM_TOKEN = '7458821979:AAEzkL3X-U6BVKwoS1Vnh5bNqMZYizivTIw'
bot4 = telebot.TeleBot(TELEGRAM_TOKEN)
disclaimer = '<i>Торгівля криптовалютами має високі ризики та може призвести до значних фінансових втрат! Уся відповідальність лежить на користувачеві бота.</i>'

# File to store user chat IDs
chat_ids_file = "user_chat_ids.txt"

# Load existing chat IDs
existed_chat_ids = set(chat_ids.get_existed_chat_ids())

@bot4.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)
    msg = (
f"""🇺🇦 Слава Україні!

Отож ти приєднався(-лась) до розсилки.
Поточна сесія аналізу вже активна, тому просто очікуй на повідомлення.

Щоб дізнатись як функціонує бот - тицяй /how_it_works.
Щоб дізнатись як користуватись - тицяй /how_to_use
Щоб отримати вихідний код - зв'яжись зі мною.
Переключиться на русский - жми /switch_to_ru

{disclaimer}
""")
    bot4.send_message(chat_id, msg, parse_mode="HTML")
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} натиснув на start')


@bot4.message_handler(commands=['switch_to_ru'])
def send_switch(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    pic = open(f'funnyhaha.gif', 'rb')
    bot4.send_animation(chat_id, pic)
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} натиснув на switch_to_ru')


@bot4.message_handler(commands=['how_to_use'])
def send_htu(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    msg = f"""
Бот створено для трейдерів-скальперів, які працюють зі стаканом ордерів та графіком м1/м5 і торгують пробій щільності/рівня, відскок, хибний пробій тощо.

На скріні ти бачитимеш червону пунктирну лінію яка відображає значний об'єм (сайз) на рівні (на ОДНОМУ екстремумі!).

Характеристики цієї червоної лінії (сайз в стакані + екстремум):
- Екстремум має кімнату зліва 30 барів.
- Сайз максимальний на 20 найближчих об'ємів в стакані (по 10 вверх і вниз).
- Сайз на х1.3 більший за наступний по розміру серед цих 20.
- Сайз більший за середній обєм останніх 100 хвилин (m1).
- Сайз знаходиться в 3х ATRах від поточної ціни.

{disclaimer}
"""
    pic = open(f'exam1.jpg', 'rb')
    bot4.send_photo(chat_id, pic, msg, parse_mode="HTML")
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} натиснув на how_to_use')


@bot4.message_handler(commands=['no_size'])
def send_nosize(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    bot4.send_message(message.chat.id,
f"""
Якшо червоної лінії на скріншоті нема - значить знайдений великий сайз знаходиться критично близько до рамки. Це графічний баг, просто там лінія не малюється, я хз, колись поправлю. В такому разі дивись просто на ціну в описі.

{disclaimer}
""", parse_mode="HTML")
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} натиснув на no_size')


@bot4.message_handler(commands=['how_it_works'])
def send_hit(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)

    msg = f'''
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

Частина 2. Пошук екстремумів і значних сайзів НА них.
1. ЩОХВИЛИНИ завантажуємо бари і стакан по споту і фючу для кожного інструмента з ендпоінтів:
<i>fapi binance com/fapi/v1/depth?symbol=...</i>
<i>api binance com/api/v3/depth?symbol=...</i>
<i>fapi binance com/fapi/v1/klines?symbol=...</i>
<i>api binance com/api/v3/klines?symbol=...</i>
2. Пошук екстремумів і значних сайзів на них.
3. Перевірка знайденого сайзу.

Частина 3. Перевірка знайденого сайзу НАД ціною (для ask):
✅ Ціна сайзу вища поточної.
✅ Сайз на екстремумі з кімнатою зліва в 30 хвилин.
✅ Сайз максимальний на 20 найближчих об'ємів (по 10 вверх і вниз).
✅ Сайз на х1.3 більший за наступний по розміру серед цих 20.
✅ Сайз більший за середній обєм останніх 100 хвилин (m1).
✅ Сайз знаходиться в 3х ATRах від поточної ціни.

для сайзів ПІД ціною (для bid) - той самий принцип

Важливо!
- Перевірка відбувається і для спота і для фючерсів.
- Вперше знайдений великий сайз - не публікується. Тільки якщо через хвилину він і досі на тому ж місці - формується скрін і відправляється сюди. Якщо він продовжує там стояти - скріни надходитимуть щохвилини.

{disclaimer}
'''
    bot4.send_message(chat_id, msg, parse_mode="HTML")
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} натиснув на how_it_works')


@bot4.message_handler(commands=['status'])
def send_status(message):
    chat_id = message.chat.id
    if chat_id not in existed_chat_ids:
        chat_ids.save_new_chat_id(chat_id)
    bot4.send_message(message.chat.id, "Сервер запущено. Бот працює.", parse_mode="HTML")
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} натиснув на status')


@bot4.message_handler(func=lambda message: True)
def handle_message(message):
    bot4.send_message(message.chat.id, "Повідомлень я не розумію, сорян 🤷🏻‍♂️")
    chat_id = message.chat.id
    pic = open(f'pig.webm', 'rb')
    bot4.send_sticker(chat_id, pic)
    bot1.send_message(662482931, f'🙂 Користувач {chat_id} шось написав і отримав свиню')


def start_bot():
    bot4.infinity_polling()

