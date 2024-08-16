import glob
import os
import time
from datetime import datetime
from threading import Thread, Event
import telebot

from modules import klines, order_book
import sys
from get_pairsV4 import get_pairs
from screenshoterV2 import screenshoter_send
from bot_handling import start_bot


PERSONAL_TELEGRAM_TOKEN = '5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA'
personal_bot = telebot.TeleBot(PERSONAL_TELEGRAM_TOKEN)

# Event to signal threads to stop
stop_event = Event()

os.environ['BINANCE_SENT'] = ""
os.environ['FILTERED'] = ""
os.environ['IN_WORK'] = ""
os.environ['RELOAD_TIMESTAMP'] = ""


def search(symbol, reload_time, time_log):
    levels_f = {}
    levels_s = {}

    levels_f_volumes = {}
    levels_s_volumes = {}

    static_f = []
    static_s = []

    c_room = 30  # кімната зліва
    d_room = 10  # вікно зверху і знизу стакану
    atr_dis = 3  # мультиплікатор відстані до сайзу в ATR

    while not stop_event.is_set():

        time1 = time.perf_counter()

        for market_type in ["f", "s"]:
            try:
                depth = order_book(symbol, 500, market_type)
            except Exception as e:
                personal_message = f"⛔️ Error in downloading depth for {symbol}({market_type}): {e}"
                print(personal_message)
                personal_bot.send_message(662482931, personal_message)

            try:
                the_klines = klines(symbol, "1m", 100, market_type)

            except Exception as e:
                personal_message = f"⛔️ Error in downloading klines for {symbol}({market_type}): {e}"
                print(personal_message)
                personal_bot.send_message(662482931, personal_message)

            market_type_verbose = 'FUTURES' if market_type == 'f' else 'SPOT'

            if depth is not None and the_klines is not None:

                c_time, c_open, c_high, c_low, c_close, avg_vol = the_klines[0], the_klines[1], the_klines[2], the_klines[3], the_klines[4], the_klines[5]
                depth = depth[1]  # [ціна, об'єм]

                avg_atr_per = [(c_high[-c] - c_low[-c]) / (c_close[-c] / 100) for c in range(30)]
                avg_atr_per = float('{:.2f}'.format(sum(avg_atr_per) / len(avg_atr_per)))

                if len(c_high) == len(c_low):

                    for i in range(110, len(depth) - 110):
                        current_vol = depth[i][1]
                        current_price = depth[i][0]
                        previous_b_values = [depth[j][1] for j in range(i - 20, i)]  # values 20 before
                        following_b_values = [depth[j][1] for j in range(i + 1, i + 21)]  # values 20 after

                        distance_to = abs(current_price - c_close[-1]) / (c_close[-1] / 100)

                        if all(current_vol > b * 2 for b in previous_b_values + following_b_values) and distance_to <= avg_atr_per * 2 and current_vol >= avg_vol * 3:

                            levels_volumes = levels_f_volumes if market_type == 'f' else levels_s_volumes

                            if current_price not in levels_volumes.keys():
                                levels_volumes.update({current_price: current_vol})
                            else:
                                personal_message = (f"🐋 {market_type_verbose} #{symbol}\n\n"
                                                    f"Size: {round(current_vol / avg_vol, 1)} x avg.vol\n"
                                                    f"On price: {current_price}\n"
                                                    f"Distance: {round(distance_to, 2)}%")
                                per_ids = [662482931, 317994467]
                                for per_id in per_ids:
                                    personal_bot.send_message(per_id, personal_message)
                                levels_volumes.pop(current_price)

                    for i in range(2, len(c_low) - c_room):
                        if c_high[-i] >= max(c_high[-1: -i - c_room: -1]):
                            for item in depth:
                                # щільність знаходиться між 9-ю спочатку, 9-ю з кінця та ціна щільності == хаю
                                if d_room - 1 < depth.index(item) < len(depth) - d_room and c_high[-i] == item[0]:
                                    # сайзи між ціною щільності -10 та ціною щільності
                                    lower_sizes = [depth[k][1] for k in range(depth.index(item) - d_room, depth.index(item))]
                                    # сайзи між ціною щільності +10 та ціною щільності
                                    higher_sizes = [depth[k][1] for k in range(depth.index(item) + 1, depth.index(item) + d_room + 1)]
                                    # дистанція до ціни
                                    distance_per = abs(c_high[-i] - c_close[-1]) / (c_close[-1] / 100)
                                    distance_per = float('{:.2f}'.format(distance_per))

                                    if item[1] >= max(lower_sizes) * 1.3 and item[1] >= max(higher_sizes) * 1.3 and distance_per <= atr_dis * avg_atr_per and item[1] >= avg_vol * 2:

                                        levels_dict = levels_f if market_type == "f" else levels_s
                                        static_dict = static_f if market_type == "f" else static_s

                                        if c_high[-i] not in levels_dict.keys():
                                            levels_dict.update({c_high[-i]: c_time[-i]})

                                        else:
                                            if levels_dict.get(c_high[-i]) == c_time[-i]:

                                                if round(item[1] / avg_vol, 1) <= 3:
                                                    size_verb = '..common size'
                                                elif round(item[1] / avg_vol, 1) <= 5:
                                                    size_verb = '..pretty big size 👌🏻'
                                                else:
                                                    size_verb = '..huge size 💪🏻'

                                                message_for_screen = f"""
{market_type_verbose} #{symbol}
{item[0]}(price) * <b>{int(item[1])}</b>(size) = ${int((item[0] * item[1]) / 1000)}K
distance to size = {distance_per}%
avg_vol/size_vol = 1/{round(item[1] / avg_vol, 1)} {size_verb}

<i>Повідомлення не є торговою рекомендацією.</i>
@UA_sizes_bot
"""
                                                screenshoter_send(symbol, market_type, item[0], message_for_screen)
                                                if c_high[-i] not in static_dict:
                                                    static_dict.append(c_high[-i])
                                    break

                        if c_low[-i] <= min(c_low[-1: -i - c_room: -1]):
                            for item in depth:
                                # щільність знаходиться між 9-ю спочатку, 9-ю з кінця та ціна щільності == хаю
                                if d_room - 1 < depth.index(item) < len(depth) - d_room and c_low[-i] == item[0]:
                                    # сайзи між ціною щільності -10 та ціною щільності
                                    lower_sizes = [depth[k][1] for k in range(depth.index(item) - d_room, depth.index(item))]
                                    # сайзи між ціною щільності +10 та ціною щільності
                                    higher_sizes = [depth[k][1] for k in range(depth.index(item) + 1, depth.index(item) + d_room + 1)]
                                    # дистанція до ціни
                                    distance_per = abs(c_low[-i] - c_close[-1]) / (c_close[-1] / 100)
                                    distance_per = float('{:.2f}'.format(distance_per))

                                    if item[1] >= max(lower_sizes) * 1.3 and item[1] >= max(higher_sizes) * 1.3 and distance_per <= atr_dis * avg_atr_per and item[1] >= avg_vol * 2:

                                        levels_dict = levels_f if market_type == "f" else levels_s
                                        static_dict = static_f if market_type == "f" else static_s

                                        if c_low[-i] not in levels_dict.keys():
                                            levels_dict.update({c_low[-i]: c_time[-i]})

                                        else:
                                            if levels_dict.get(c_low[-i]) == c_time[-i]:
                                                if round(item[1] / avg_vol, 1) <= 3:
                                                    size_verb = '..common size'
                                                elif round(item[1] / avg_vol, 1) <= 5:
                                                    size_verb = '..pretty big size 👌🏻'
                                                else:
                                                    size_verb = '..huge size 💪🏻'

                                                message_for_screen = f"""
{market_type_verbose} #{symbol}
{item[0]} (price) * <b>{int(item[1])}</b> (size) = ${int((item[0] * item[1]) / 1000)}K
distance to size = {distance_per}%
avg_vol/size_vol = 1/{round(item[1] / avg_vol, 1)} {size_verb}

<i>Повідомлення не є торговою рекомендацією.</i>
@UA_sizes_bot
"""
                                                screenshoter_send(symbol, market_type, item[0], message_for_screen)
                                                if c_low[-i] not in static_dict:
                                                    static_dict.append(c_low[-i])
                                    break

            elif market_type == "f" and (depth is None or the_klines is None):
                personal_message = f"⛔️ Main file. Error in {symbol} data. Futures is n/a!"
                print(personal_message)
                personal_bot.send_message(662482931, personal_message)

        time2 = time.perf_counter()
        time3 = time2 - time1
        time3 = float('{:.2f}'.format(time3))

        if time_log > 0:
            print(f"{datetime.now().strftime('%H:%M:%S')} {symbol}: {time3} + {float('{:.2f}'.format(reload_time))} s, levels: {len(levels_f)}/{len(levels_s)}")
            sys.stdout.flush()

        time.sleep(reload_time)


def clean_old_files(directory, prefix='FT', extension='.png'):
    pattern = os.path.join(directory, f"{prefix}*{extension}")
    files_to_remove = glob.glob(pattern)
    for file_path in files_to_remove:
        try:
            os.remove(file_path)
        except Exception as e:
            personal_message = f"⚙️ Failed to remove file {file_path}: {e}"
            personal_bot.send_message(chat_id=662482931, text=personal_message)
            print(personal_message)

    personal_message = f"⚙️ {len(files_to_remove)} images successfully removed..."
    personal_bot.send_message(chat_id=662482931, text=personal_message)
    print(personal_message)


# ---------- NEW PROCESSOR ------------ #
def monitor_time_and_control_threads():
    global stop_event
    while True:
        current_minute = int(datetime.now().strftime('%M'))
        if current_minute != 59:
            personal_message = f"⚙️ Current time is {datetime.now().strftime('%H:%M:%S')}. We starting..."
            personal_bot.send_message(chat_id=662482931, text=personal_message)
            print(personal_message)

            stop_event.clear()

            clean_old_files('.')
            reload_time = 58
            time_log = 1

            pairs = get_pairs()
            personal_message = f'⚙️ Sleep 30 seconds and starting calculation threads...'
            personal_bot.send_message(chat_id=662482931, text=personal_message)
            print(personal_message)
            time.sleep(30)

            the_threads = []
            for pair in pairs:
                thread = Thread(target=search, args=(pair, reload_time, time_log,))
                thread.start()
                the_threads.append(thread)

            personal_message = f'⚙️ Threads is running...'
            personal_bot.send_message(chat_id=662482931, text=personal_message)
            print(personal_message)
            time.sleep(30)

            # Monitor until minutes reach 58
            while not int(datetime.now().strftime('%M')) == 59:
                time.sleep(1)

            # Signal threads to stop
            personal_message = f"⚙️ Current time is {datetime.now().strftime('%H:%M:%S')}. Signal to stop threads sent..."
            personal_bot.send_message(chat_id=662482931, text=personal_message)
            print(personal_message)
            stop_event.set()

            # Wait for threads to finish
            for thread in the_threads:
                thread.join()

            personal_message = "⚙️ All thread have been stopped. Waiting to restart..."
            personal_bot.send_message(chat_id=662482931, text=personal_message)
            print(personal_message)

            time.sleep(60)

        time.sleep(1)


if __name__ == '__main__':

    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    monitor_time_and_control_threads()
