import os
import asyncio
import aiohttp

from database_v2 import add_coin_to_coins


async def fetch_klines(session, url) -> dict:
    async with session.get(url) as response:
        weight = int(response.headers.get('x-mbx-used-weight-1m', 1000))

        if weight > 2000:
            raise ConnectionError('Too close to the limit. 429')

        return await response.json() if response.status == 200 else {}


async def get_trading_symbols(session, asset):
    """Отримує торгові символи Futures з перевіркою Spot, якщо увімкнено."""
    try:
        excluded = os.getenv('EXCLUDED', '')
        excluded = set(excluded.replace(' ', '').split(','))

        futures_info, spot_info = await asyncio.gather(
            fetch_klines(
                session,
                "https://fapi.binance.com/fapi/v1/exchangeInfo"
            ),
            fetch_klines(
                session,
                "https://api.binance.com/api/v3/exchangeInfo"
            )
        )

        if not futures_info or not spot_info:
            return {}

        spot_symbols = {
            item['symbol']
            for item in spot_info['symbols']
            if (
                item['quoteAsset'] == asset
                and item['status'] == 'TRADING'
            )
        }

        spot_verified = os.getenv('SPOT_VERIFIED', 'off') == 'on'

        if spot_verified:
            symbols = {
                item['symbol']: item['filters'][0]['tickSize']
                for item in futures_info['symbols']
                if (
                    item['quoteAsset'] == asset
                    and item['status'] == 'TRADING'
                    and item['symbol'] in spot_symbols
                    and item['symbol'] not in excluded
                )
            }
        else:
            symbols = {
                item['symbol']: item['filters'][0]['tickSize']
                for item in futures_info['symbols']
                if (
                    item['quoteAsset'] == asset
                    and item['status'] == 'TRADING'
                    and item['symbol'] not in excluded
                )
            }

        return symbols

    except Exception as e:
        print(f"⚠️ Error fetching trading symbols: {e}")
        return {}


async def calculate_pairs(
        session,
        pairs_dict,
        request_limit_length,
        frame,
        ticksize_filter,
        atr_filter
):
    for symbol, tick_size in pairs_dict.items():

        url = (
            f'https://fapi.binance.com/fapi/v1/klines'
            f'?symbol={symbol}'
            f'&interval={frame}'
            f'&limit={request_limit_length}'
        )

        try:
            binance_candle_data = await fetch_klines(session, url)

            if not binance_candle_data:
                continue

            close = [float(item[4]) for item in binance_candle_data]
            high = [float(item[2]) for item in binance_candle_data]
            low = [float(item[3]) for item in binance_candle_data]

            atr_percent = sum(
                (h - l) / (c / 100)
                for h, l, c in zip(high, low, close)
            ) / len(close)

            atr_percent = round(atr_percent, 4)

            ticksize_percent = float(tick_size) / (close[-1] / 100)
            ticksize_percent = round(ticksize_percent, 4)

            status = (
                1
                if (
                    ticksize_percent <= ticksize_filter
                    and atr_percent >= atr_filter
                )
                else 0
            )

            add_coin_to_coins(symbol, ticksize_percent, atr_percent, status)

        except Exception as e:
            print(f"⛔️ Error downloading klines for {symbol}: {e}")


def split_dict(input_dict, num_parts):
    keys = list(input_dict)

    if not keys:
        return []

    num_parts = min(num_parts, len(keys))

    avg, remainder = divmod(len(keys), num_parts)

    return [
        {
            key: input_dict[key]
            for key in keys[
                i * avg + min(i, remainder):
                (i + 1) * avg + min(i + 1, remainder)
            ]
        }
        for i in range(num_parts)
    ]


async def get_pairs_async(asset='USDT'):
    request_limit_length = int(os.getenv('KLINES_LEN'))
    chunk_count = 10

    ticksize_filter = float(os.getenv('TICKSIZE_FILTER'))
    atr_filter = float(os.getenv('ATR_FILTER'))
    frame = f"{os.getenv('TF')}m"

    async with aiohttp.ClientSession() as session:

        trading_symbols = await get_trading_symbols(
            session,
            asset
        )

        if not trading_symbols:
            return

        chunks = split_dict(
            trading_symbols,
            chunk_count
        )

        await asyncio.gather(
            *[
                calculate_pairs(
                    session,
                    chunk,
                    request_limit_length,
                    frame,
                    ticksize_filter,
                    atr_filter
                )
                for chunk in chunks
            ]
        )