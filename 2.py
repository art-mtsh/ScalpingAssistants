import threading
import time
from datetime import datetime
import telebot

# Your bot token
bot = telebot.TeleBot("5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(662482931, f'Got!')

# Event to signal threads to stop
stop_event = threading.Event()


def start_polling():
    """Starts the bot's infinity polling."""
    bot.infinity_polling()


def example_function(name):
    """Example function that prints a statement every second."""
    while not stop_event.is_set():
        print(f"Thread {name} is running...")
        time.sleep(1)
    print(f"Thread {name} is stopping...")


def monitor_time_and_control_threads():
    """Monitor time and control the starting and stopping of example threads."""
    global stop_event
    while True:
        current_seconds = int(datetime.now().strftime('%S'))

        if current_seconds <= 50:
            print("Starting example threads...")
            stop_event.clear()

            # Start example threads
            example_threads = []
            for i in range(2, 5):  # Threads 2, 3, and 4
                thread = threading.Thread(target=example_function, args=(i,))
                thread.start()
                example_threads.append(thread)

            # Monitor until seconds reach 51
            while int(datetime.now().strftime('%S')) <= 50:
                time.sleep(1)

            # Signal threads to stop
            print("Stopping example threads...")
            stop_event.set()

            # Wait for threads to finish
            for thread in example_threads:
                thread.join()

            print("All example threads have been stopped. Waiting to restart...")

        # Wait for the next cycle (to avoid busy-waiting)
        time.sleep(1)


# Start the bot's polling in its own thread immediately
polling_thread = threading.Thread(target=start_polling)
polling_thread.start()
#
# # Start the monitoring function for other threads
monitor_time_and_control_threads()