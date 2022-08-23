from math import floor
from typing import Union

feetier_to_tickspacing_dict = {
    100: 1,
    500: 10,
    3000: 60,
    10000: 200
}

"""The minimum tick that can be used on any pool."""
MIN_TICK: int = -887272

"""The maximum tick that can be used on any pool."""
MAX_TICK: int = -MIN_TICK


def feetier_to_tickspacing(feetier: int) -> int:
    return feetier_to_tickspacing_dict[feetier]


def feetier_to_fee_percent(feetier: int) -> float:
    return float(feetier) / 10000.0


def tick_to_raw_price_token0(tick: int) -> float:
    return 1.0001 ** tick


def raw_price_to_price_token0(decimals_token0: int, decimals_token1: int, raw_price_token0: float) -> float:
    return 10 ** (decimals_token1 - decimals_token0) / raw_price_token0


def tick_to_price_token0(tick: int, decimals_token0: int, decimals_token1: int) -> float:
    return raw_price_to_price_token0(decimals_token0, decimals_token1, tick_to_raw_price_token0(tick))


def get_active_tick(current_tick: int, tick_spacing: int) -> int:
    return floor(current_tick // tick_spacing) * tick_spacing


def liquidity_to_token0_token1_adj(liquidity: int,
                                   lower_tick: int, upper_tick: int,
                                   decimals0: int, decimals1: int) -> (float, float):
    # Compute square roots of prices corresponding to the bottom and top ticks
    sqrt_price_a = tick_to_raw_price_token0(lower_tick // 2)  # price = 1.0001 ** tick i.e.
    sqrt_price_b = tick_to_raw_price_token0(upper_tick // 2)  # sqrt(price) = 1.0001 ** (tick // 2)

    # Compute virtual amounts of the two assets
    amount0 = liquidity * (sqrt_price_b - sqrt_price_a) / (sqrt_price_a * sqrt_price_b)
    amount1 = liquidity * (sqrt_price_b - sqrt_price_a)

    # Compute adjusted amount
    adj_amount0 = amount0 / (10 ** decimals0)
    adj_amount1 = amount1 / (10 ** decimals1)
    return adj_amount0, adj_amount1


def round_timestamp_to_day(timestamp: Union[float, int]) -> int:
    return int(timestamp) // 86400 * 86400
