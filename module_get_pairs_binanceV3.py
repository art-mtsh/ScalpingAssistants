import requests

def binance_pairs(chunks, quote_assets, day_range_filter, day_density_filter, tick_size_filter):
    excluded_substrings = ["RUB", "USDPUSDT", "EURBUSD", "EURUSDT", "TUSDUSDT", "USDCUSDT", "FDUSDUSDT"]
    filtered_symbols = []
    
    ts_dict = {}
    futures_exchange_info_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    spot_exchange_info_url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(futures_exchange_info_url)
    response_data = response.json()
    response_data = response_data.get("symbols")
    for data in response_data:
        symbol = data['symbol']
        filters = data['filters']
        tick_size = filters[0]['tickSize']
        quoteAsset = data['quoteAsset']
        if quoteAsset in quote_assets:
            ts_dict.update({symbol: tick_size})
    
    
    day_info_dict = {}
    futures_day_info_url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    spot_day_info_url = "https://api.binance.com/api/v3/ticker/24hr"
    response = requests.get(futures_day_info_url)
    response_data = response.json()
    for data in response_data:
        symbol = data['symbol']
        high = data['highPrice']
        low = data['lowPrice']
        last_price = data['lastPrice']
        day_info_dict.update({symbol: [high, low, last_price]})
    
    merged_dict = {}
    for key, value in ts_dict.items():
        if key in day_info_dict.keys():
            ts = float(ts_dict[key])
            h = float(day_info_dict[key][0])
            l = float(day_info_dict[key][1])
            c = float(day_info_dict[key][2])
            
            if c != 0 and ts != 0 and not any(substring in key for substring in excluded_substrings):
                day_range = (h - l) / (c / 100)
                density = (h - l) / ts
                ts_p = ts / (c / 100)
                
                if day_range >= day_range_filter and density >= day_density_filter and ts_p <= tick_size_filter:
                    filtered_symbols.append([key, ts])
    
 
    # Calculate the chunk size
    chunk_size = len(filtered_symbols) // chunks

    # Split symbols_from_bi into chunks
    chunked_symbols = [filtered_symbols[i:i + chunk_size] for i in range(0, len(filtered_symbols), chunk_size)]

    return chunked_symbols


# pairs = binance_pairs(15, ["USDT"], 0, 0, 100)
# for i in pairs:
#     print(i)
#
# print(f"Start search for {sum(len(inner_list) for inner_list in pairs)} pairs")