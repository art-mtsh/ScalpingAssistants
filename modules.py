from datetime import datetime

import requests
import telebot

TELEGRAM_TOKEN1 = '5657267406:AAExhEvjG3tjb0KL6mTM9otoFiL6YJ_1aSA'
personal_bot = telebot.TeleBot(TELEGRAM_TOKEN1)

def klines(symbol, frame, request_limit_length, market_type: str):
	
	futures_klines = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={frame}&limit={request_limit_length}'
	spot_klines = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={frame}&limit={request_limit_length}'
	
	url = futures_klines if market_type == "f" else spot_klines
	response = requests.get(url)
	
	if response.status_code == 200:
		
		response_length = len(response.json()) if response.json() != None else 0

		if response_length == request_limit_length:
			binance_candle_data = response.json()
			c_time = list(float(i[0]) for i in binance_candle_data)
			c_open = list(float(i[1]) for i in binance_candle_data)
			c_high = list(float(i[2]) for i in binance_candle_data)
			c_low = list(float(i[3]) for i in binance_candle_data)
			c_close = list(float(i[4]) for i in binance_candle_data)
			c_volume = list(float(i[5]) for i in binance_candle_data)
			buy_volume = list(float(i[9]) for i in binance_candle_data)
			sell_volume = [c_volume[0] - buy_volume[0]]

			avg_vol = sum(c_volume) / len(c_volume)
			avg_vol = avg_vol

			if len(c_open) != len(c_high) != len(c_low) != len(c_close) != len(c_volume):
				msg = (f"⛔️ Length error for klines data for {symbol} ({market_type}), status code {response.status_code}\n"
					   f"{url}")
				if market_type == 'f': personal_bot.send_message(662482931, msg)
				if market_type == 'f': print(msg)
			else:
				return [c_time, c_open, c_high, c_low, c_close, avg_vol, buy_volume, sell_volume]
		
		else:
			msg = (f"⛔️ Empty klines data for {symbol} ({market_type}) on 1m, status code {response.status_code}\n"
				   f"{url}")
			if market_type == 'f': personal_bot.send_message(662482931, msg)
			if market_type == 'f': print(msg)
			
	elif response.status_code == 429:
		msg = f"⛔️ {symbol} ({market_type}) LIMITS REACHED !!!! 429 CODE !!!!"
		personal_bot.send_message(662482931, msg)
		print(msg)
	
	else:
		msg = (f"⛔️ No klines data for {symbol} ({market_type}), status code {response.status_code}\n"
			   f"{url}")
		if market_type == 'f': personal_bot.send_message(662482931, msg)
		if market_type == 'f': print(msg)


def order_book(symbol, request_limit_length, market_type: str):

	futures_order_book = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit={request_limit_length}"
	spot_order_book = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit={request_limit_length}"

	url = futures_order_book if market_type == "f" else spot_order_book
	response = requests.get(url)
	
	if response.status_code == 200:

		response_data = response.json()
		if len(response_data['bids']) == request_limit_length:

			bids = response_data.get('bids')
			asks = response_data.get('asks')
			close = float(asks[0][0])

			combined_list = [[float(item[0]), float(item[1])] for item in reversed(asks)]
			for item in bids: combined_list.append([float(item[0]), float(item[1])])
			combined_list_sorted = sorted(combined_list, key=lambda x: x[1])

			decimal_1 = len(str(combined_list[12][0]).split('.')[-1].rstrip('0'))
			decimal_2 = len(str(combined_list[34][0]).split('.')[-1].rstrip('0'))
			decimal_3 = len(str(combined_list[23][0]).split('.')[-1].rstrip('0'))
			max_decimal = max([decimal_1, decimal_2, decimal_3])


			if len(bids) == 0 or len(asks) == 0:
				msg = (f"⛔️ bids=0 or asks=0 for depth data for {symbol} ({market_type}), status code {response.status_code}\n"
					   f"{url}")
				if market_type == 'f': personal_bot.send_message(662482931, msg)
				if market_type == 'f': print(msg)
			else:
				return [close, combined_list, combined_list_sorted, max_decimal]

		else:
			msg = (f"⛔️ Empty depth data for {symbol} ({market_type}), status code {response.status_code}\n"
					   f"{url}")
			if market_type == 'f': personal_bot.send_message(662482931, msg)
			if market_type == 'f': print(msg)

	elif response.status_code == 429:

		msg = f"⛔️ {symbol} ({market_type}) LIMITS REACHED !!!! 429 CODE !!!!"
		personal_bot.send_message(662482931, msg)
		print(msg)

	else:
		msg = (f"⛔️ No depth data for {symbol} ({market_type}), status code {response.status_code}\n"
			   f"{url}")
		if market_type == 'f': personal_bot.send_message(662482931, msg)
		if market_type == 'f': print(msg)

# print(klines("1000RATSUSDT", "1m", 100, "s"))
# print(order_book("RIFUSDT", 500, "s"))


def three_distances(symbol, close, combined_list, max_avg_size, search_distance, market_type: str):
	
	klines_data = klines(symbol, '1m', 186, market_type)
	high = klines_data[1]
	low = klines_data[2]
	avg_vol_60 = klines_data[4] / 1000
	# cumulative_delta = klines_data[5]
	buy_vol = klines_data[5]
	sell_vol = klines_data[6]
	
	price_1 = combined_list[-1][0]
	size_1 = combined_list[-1][1]
	size_1_dollars = (price_1 * size_1) / 1000
	distance_1 = abs(close - price_1) / (close / 100)
	distance_1 = float('{:.2f}'.format(distance_1))
	
	price_2 = combined_list[-2][0]
	size_2 = combined_list[-2][1]
	size_2_dollars = (price_2 * size_2) / 1000
	distance_2 = abs(close - price_2) / (close / 100)
	distance_2 = float('{:.2f}'.format(distance_2))
	
	price_3 = combined_list[-3][0]
	size_3 = combined_list[-3][1]
	size_3_dollars = (price_3 * size_3) / 1000
	distance_3 = abs(close - price_3) / (close / 100)
	distance_3 = float('{:.2f}'.format(distance_3))
	
	res = []

	if size_1 >= max_avg_size and size_1_dollars >= avg_vol_60 and distance_1 <= search_distance:

		for i in range(2, len(high)-6):

			if high[-i] > price_1:
				break
			elif high[-i] == price_1 and high[-i] >= max(high[-1:-i-6:-1]):
				bigger_than = int(combined_list[-1][1] / combined_list[-4][1])
				print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {high[-i]}, current size {size_1}")
				res.append([distance_1, price_1, size_1, bigger_than])
				break

		for i in range(2, len(low)-6):

			if low[-i] < price_1:
				break
			elif low[-i] == price_1 and low[-i] <= min(low[-1:-i-6:-1]):
				bigger_than = int(combined_list[-1][1] / combined_list[-4][1])
				print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {low[-i]}, current size {size_1}")
				res.append([distance_1, price_1, size_1, bigger_than])
				break

	if size_2 >= max_avg_size and size_2_dollars >= avg_vol_60 and distance_2 <= search_distance:

		for i in range(2, len(high)-6):
			if high[-i] > price_2:
				break
			elif high[-i] == price_2 and high[-i] >= max(high[-1:-i-6:-1]):
				bigger_than = int(combined_list[-2][1] / combined_list[-4][1])
				print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {high[-i]}, current size {size_1}")
				res.append([distance_2, price_2, size_2, bigger_than])
				break

		for i in range(2, len(low)-6):
			if low[-i] < price_2:
				break
			elif low[-i] == price_2 and low[-i] <= min(low[-1:-i-6:-1]):
				bigger_than = int(combined_list[-2][1] / combined_list[-4][1])
				print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {low[-i]}, current size {size_1}")
				res.append([distance_2, price_2, size_2, bigger_than])
				break

	if size_3 >= max_avg_size and size_3_dollars >= avg_vol_60 and distance_3 <= search_distance:

		for i in range(2, len(high)-6):
			if high[-i] > price_3:
				break
			elif high[-i] == price_3 and high[-i] >= max(high[-1:-i-6:-1]):
				bigger_than = int(combined_list[-3][1] / combined_list[-4][1])
				print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {high[-i]}, current size {size_1}")
				res.append([distance_3, price_3, size_3, bigger_than])
				break

		for i in range(2, len(low)-6):
			if low[-i] < price_3:
				break
			elif low[-i] == price_3 and low[-i] <= min(low[-1:-i-6:-1]):
				bigger_than = int(combined_list[-3][1] / combined_list[-4][1])
				print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {low[-i]}, current size {size_1}")
				res.append([distance_3, price_3, size_3, bigger_than])
				break

	# if high[-1] >= max(high[-1:-181:-1]) and cumulative_delta[-1] <= min(cumulative_delta[-1:-181:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BEARISH 180") #, high[-3]: {high[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif high[-1] >= max(high[-1:-121:-1]) and cumulative_delta[-1] <= min(cumulative_delta[-1:-121:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BEARISH 120") # high[-3]: {high[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif high[-1] >= max(high[-1:-61:-1]) and cumulative_delta[-1] <= min(cumulative_delta[-1:-61:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BEARISH 60") #, high[-3]: {high[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif high[-1] >= max(high[-1:-31:-1]) and cumulative_delta[-1] <= min(cumulative_delta[-1:-31:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BEARISH 30") #, high[-3]: {high[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif high[-1] >= max(high[-1:-11:-1]) and cumulative_delta[-1] <= min(cumulative_delta[-1:-11:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BEARISH 10") #, high[-3]: {high[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	#
	#
	# elif low[-1] <= min(low[-1:-181:-1]) and cumulative_delta[-1] >= max(cumulative_delta[-1:-181:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BULLISH 180") #, low[-3]: {low[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif low[-1] <= min(low[-1:-121:-10]) and cumulative_delta[-1] >= max(cumulative_delta[-1:-121:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BULLISH 120") #, low[-3]: {low[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif low[-1] <= min(low[-1:-61:-1]) and cumulative_delta[-1] >= max(cumulative_delta[-1:-61:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BULLISH 60") #, low[-3]: {low[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif low[-1] <= min(low[-1:-31:-1]) and cumulative_delta[-1] >= max(cumulative_delta[-1:-31:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BULLISH 30") #, low[-3]: {low[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")
	# elif low[-1] <= min(low[-1:-11:-1]) and cumulative_delta[-1] >= max(cumulative_delta[-1:-11:-1]):
	# 	bot2.send_message(662482931, f"{datetime.now().strftime('%H:%M:%S')} {symbol} BULLISH 10") #, low[-3]: {low[-1]}: {int(buy_vol[-1])}, {int(sell_vol[-1])}")

	# for i in range(2, len(high)):
	#
	# 	if high[-i] >= max(high[-1: -i - 5: -1]) and high[-1: -i - 5: -1].count(high[-i]) >= 5 and market_type == "f":
	# 		distance_4 = abs(close - high[-i]) / (close / 100)
	# 		distance_4 = float('{:.2f}'.format(distance_4))
	#
	# 		if distance_4 <= 0.4:
	# 			print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {high[-i]}, LEVEL")
	#
	# 			res.append([distance_4, high[-i], 1, 1])
	# 			break
	#
	# 	if low[-i] <= min(low[-1: -i - 5: -1]) and low[-1: -i - 5: -1].count(low[-i]) >= 5 and market_type == "f":
	# 		distance_4 = abs(close - low[-i]) / (close / 100)
	# 		distance_4 = float('{:.2f}'.format(distance_4))
	#
	# 		if distance_4 <= 0.4:
	# 			print(f"{symbol} {market_type.capitalize()} {-i} candles ago was bounce at price {low[-i]}, LEVEL")
	#
	# 			res.append([distance_4, low[-i], 1, 1])
	# 			break

	return res
