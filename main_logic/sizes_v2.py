import asyncio
from binance.klines import get_klines
from binance.order_book import order_book
from database_v2 import get_current_sizes, is_coin_active, unlist_coin_in_sizes
from main_logic.sizes_check import SizesManager
from mutual_variables.terminator import terminator


async def main_search(coin, reload_time, repeat_rate):
    sizes_manager = SizesManager(coin)

    while not terminator.is_set():

        if not is_coin_active(coin):
            unlist_coin_in_sizes(coin)
            print(f"Manual ban set for {coin}")
            break

        current_sizes: dict = get_current_sizes(coin)

        depth = await order_book(coin, "s")
        the_klines = await get_klines(coin, "1m", "s")

        if len(depth) <= 0 or len(the_klines) <= 0:
            unlist_coin_in_sizes(coin)
            print(f"Status set to break for {coin}")
            break

        (c_time, c_open, c_high, c_low, c_close, avg_vol, buy_vol, sell_vol, cumulative_delta, cd_sma) = the_klines

        sizes_manager.depth = depth[1] # [[ціна, об'єм], [ціна, об'єм], ...]
        sizes_manager.current_price = c_close[-1]
        sizes_manager.c_high = c_high
        sizes_manager.c_low = c_low
        sizes_manager.c_close = c_close
        sizes_manager.avg_vol = avg_vol
        sizes_manager.existing_sizes = set(current_sizes.keys())

        if current_sizes:
            await sizes_manager.update_existing(current_sizes, repeat_rate)

        await sizes_manager.new_sizes_search()
        await sizes_manager.new_extremums_search()
        await sizes_manager.new_two_dim_verification()
        await sizes_manager.new_size_decision()

        await asyncio.sleep(reload_time)

    print(f'End of the search for {coin}')