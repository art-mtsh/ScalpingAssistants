import glob
import os
import time
from datetime import datetime
from multiprocessing import Process, Manager
from threading import Thread, Event
import telebot

import chat_ids
from modules import klines, order_book
import sys
from get_pairsV4 import get_pairs
from screenshoterV2 import screenshoter_send
from bot_handling import start_bot


TELEGRAM_TOKEN1 = '5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA'
bot1 = telebot.TeleBot(TELEGRAM_TOKEN1)

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

    c_room = 30 # кімната зліва
    d_room = 10 # вікно зверху і знизу стакану
    atr_dis = 3 # мультиплікатор відстані до сайзу в ATR

    while not stop_event.is_set():

        time1 = time.perf_counter()

        for market_type in ["f", "s"]:
            try:
                depth = order_book(symbol, 500, market_type)
            except Exception as e:
                msg = (f"⛔️ Error in downloading depth for {symbol}({market_type}): {e}")
                print(msg)
                bot1.send_message(662482931, msg)

            try:
                the_klines = klines(symbol, "1m", 100, market_type)

            except Exception as e:
                msg = (f"⛔️ Error in downloading klines for {symbol}({market_type}): {e}")
                print(msg)
                bot1.send_message(662482931, msg)

            market_type_verbose = 'FUTURES' if market_type == 'f' else 'SPOT'

            if depth != None and the_klines != None:

                c_time, c_open, c_high, c_low, c_close, avg_vol = the_klines[0], the_klines[1], the_klines[2], the_klines[3], the_klines[4], the_klines[5]
                depth = depth[1] # [ціна, об'єм]

                avg_atr_per = [(c_high[-c] - c_low[-c]) / (c_close[-c] / 100) for c in range(30)]
                avg_atr_per = float('{:.2f}'.format(sum(avg_atr_per) / len(avg_atr_per)))

                if len(c_high) == len(c_low):

                    for i in range(110, len(depth) - 110):
                        current_vol = depth[i][1]
                        current_price = depth[i][0]
                        previous_b_values = [depth[j][1] for j in range(i - 20, i)]  # values 20 before
                        following_b_values = [depth[j][1] for j in range(i + 1, i + 21)]  # values 20 after

                        distance = abs(current_price - c_close[-1]) / (c_close[-1] / 100)

                        # Check if current b is greater than all preceding and following 20 b-values
                        if all(current_vol > b * 2 for b in previous_b_values + following_b_values) and distance <= 0.6 and current_vol >= avg_vol * 3:

                            levels_volumes = levels_f_volumes if market_type == 'f' else levels_s_volumes

                            if current_price not in levels_volumes.keys():
                                levels_volumes.update({current_price: current_vol})
                            else:
                                msg = (f"🤚🏻 {market_type_verbose} {symbol} found size x{round(current_vol / avg_vol, 1)} of avg.volumes on price {current_price}")
                                print(msg)
                                bot1.send_message(662482931, msg)
                                levels_volumes.pop(current_price)

                    for i in range(2, len(c_low) - c_room):
                        now_stamp = c_time[-i]

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
                                    # if item[1] >= sorted(higher_sizes)[-2] * 2 and distance_per <= atr_dis * avg_atr_per and item[1] >= avg_vol:

                                        levels_dict = levels_f if market_type == "f" else levels_s
                                        static_dict = static_f if market_type == "f" else static_s

                                        if c_high[-i] not in levels_dict.keys():
                                            levels_dict.update({c_high[-i]: c_time[-i]})

                                        else:
                                            if levels_dict.get(c_high[-i]) == c_time[-i]:
                                                # msg = f"{market_type.capitalize()} #{symbol}: {item[0]} * {item[1]} = ${int((item[0] * item[1]) / 1000)}K ({distance_per}%)"
                                                msg = f"""
{market_type_verbose} #{symbol}: {item[0]} * {item[1]} = ${int((item[0] * item[1]) / 1000)}K ({distance_per}%)
avg_vol/size_vol = 1/{round(item[1] / avg_vol, 1)}

<i>Повідомлення не є торговою рекомендацією.</i>
@UA_sizes_bot
"""
                                                screenshoter_send(symbol, market_type, item[0], msg)

                                                if c_high[-i] not in static_dict:
                                                    # bot2.send_message(662482931, msg)
                                                    static_dict.append(c_high[-i])
                                        # else:
                                        # 	print(f"{symbol} level {c_high[-i]} duplicate")

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
                                    # if item[1] >= sorted(lower_sizes)[-2] * 2 and distance_per <= atr_dis * avg_atr_per and item[1] >= avg_vol:

                                        levels_dict = levels_f if market_type == "f" else levels_s
                                        static_dict = static_f if market_type == "f" else static_s

                                        if c_low[-i] not in levels_dict.keys():
                                            levels_dict.update({c_low[-i]: c_time[-i]})

                                        else:
                                            if levels_dict.get(c_low[-i]) == c_time[-i]:
                                                # msg = f"{market_type.capitalize()} #{symbol}: {item[0]} * {item[1]} = ${int((item[0] * item[1]) / 1000)}K ({distance_per}%)"
                                                msg = f"""
{market_type_verbose} #{symbol}: {item[0]} * {item[1]} = ${int((item[0] * item[1]) / 1000)}K ({distance_per}%)
avg_vol/size_vol = 1/{round(item[1] / avg_vol, 1)}

<i>Повідомлення не є торговою рекомендацією.</i>
@UA_sizes_bot
"""
                                                screenshoter_send(symbol, market_type, item[0], msg)
                                                if c_low[-i] not in static_dict:
                                                    # bot2.send_message(662482931, msg)
                                                    static_dict.append(c_low[-i])
                                        # else:
                                        # 	print(f"{symbol} level {c_low[-i]} duplicate")

                                    break

            elif market_type == "f" and (depth == None or the_klines == None):
                msg = (f"⛔️ Main file. Error in {symbol} data. Futures is n/a!")
                print(msg)
                bot1.send_message(662482931, msg)


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
            msg = f"⚙️ Failed to remove file {file_path}: {e}"
            bot1.send_message(chat_id=662482931, text=msg)
            print(msg)

    msg = f"⚙️ {len(files_to_remove)} images successfully removed..."
    bot1.send_message(chat_id=662482931, text=msg)
    print(msg)


# ---------- NEW PROCESSOR ------------ #
def monitor_time_and_control_threads():
    global stop_event
    while True:
        current_minute = int(datetime.now().strftime('%M'))
        if current_minute != 59:
            msg = f"⚙️ Current time is {datetime.now().strftime('%H:%M:%S')}. We starting..."
            bot1.send_message(chat_id=662482931, text=msg)
            print(msg)

            stop_event.clear()

            clean_old_files('.')
            reload_time = 58
            time_log = 1

            pairs = get_pairs()
            msg = f'⚙️ Sleep 30 seconds and starting calculation threads...'
            bot1.send_message(chat_id=662482931, text=msg)
            print(msg)
            time.sleep(30)

            the_threads = []
            for pair in pairs:
                thread = Thread(target=search, args=(pair, reload_time, time_log,))
                thread.start()
                the_threads.append(thread)

            msg = f'⚙️ Threads is running...'
            bot1.send_message(chat_id=662482931, text=msg)
            print(msg)
            time.sleep(30)

            # Monitor until minutes reach 58
            while not int(datetime.now().strftime('%M')) == 59:
                time.sleep(1)

            # Signal threads to stop
            msg = f"⚙️ Current time is {datetime.now().strftime('%H:%M:%S')}. Signal to stop threads sent..."
            bot1.send_message(chat_id=662482931, text=msg)
            print(msg)
            stop_event.set()

            # Wait for threads to finish
            for thread in the_threads:
                thread.join()

            msg = "⚙️ All thread have been stopped. Waiting to restart..."
            bot1.send_message(chat_id=662482931, text=msg)
            print(msg)

            time.sleep(60)

        time.sleep(1)


if __name__ == '__main__':

    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    monitor_time_and_control_threads()