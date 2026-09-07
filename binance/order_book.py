import logging
import os

import aiohttp

from bot_setup.bot_setup import bot
from database_v2 import set_coin_status


async def order_book(symbol, market_type: str) -> list[list[float]]:
    perfect_depth_len = int(os.getenv('DEPTH_LEN'))
    min_depth_len = int(os.getenv('MIN_DEPTH_LEN'))

    futures_order_book = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit={perfect_depth_len}"
    spot_order_book = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit={perfect_depth_len}"

    url = futures_order_book if market_type == "f" else spot_order_book

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # print(f"Weight used by {symbol} for book: {response.headers.get('x-mbx-used-weight-1m')}")

            w = int(response.headers.get('x-mbx-used-weight-1m', 1000))
            if w > 4000:
                print(f"WARNING! Order book request reached {w}")
            elif w > 5000:
                raise ConnectionError(f"Too close to the 429 limit: {w}")

            if response.status == 200:
                response_data = await response.json()

                if len(response_data['bids']) >= min_depth_len and len(response_data['asks']) >= min_depth_len:

                    bids = response_data.get('bids')
                    asks = response_data.get('asks')
                    # close = float(asks[0][0])

                    all_prices = [item[0] for item in bids + asks]
                    # max_decimal = max(len(price.rstrip('0').split('.')[-1]) for price in all_prices)

                    combined_list = [[float(item[0]), float(item[1])] for item in reversed(asks)]
                    for item in bids:
                        combined_list.append([float(item[0]), float(item[1])])
                    combined_list_sorted_by_price = sorted(combined_list, key=lambda x: x[0])

                    if len(bids) == 0 or len(asks) == 0:
                        print(f'Missing bids/asks for {symbol}: bids={len(bids)}, asks={len(asks)}')
                        return []
                    else:
                        return combined_list_sorted_by_price

                else:
                    print(
                        f'Not full order book for {symbol}: bids={len(response_data['bids'])}, asks={len(response_data['asks'])}')
                    set_coin_status(symbol, 2)
                    print(f'Added {symbol} to ignore list')
                    return []

            elif response.status == 429:
                msg = f"⛔️ {symbol} ({market_type}) LIMITS REACHED !!!! 429 CODE !!!!"
                await bot.send_message(chat_id=os.getenv('CHAT_ID'), text=msg)
                logging.warning(msg)
                exit()


            else:
                response_data = await response.json()
                print(
                    f'Something went wrong while we requested depth for {symbol} '
                    f'({market_type}): status={response.status}, response={response_data}'
                )
                return []

# async def main():
#     while True:
#         await order_book("BTCUSDT", 199, 's')
#         await asyncio.sleep(3)
# import asyncio
# if __name__ == "__main__":
#     asyncio.run(main())
