from math import floor

feetier_to_tickspacing_dict = {
    100: 1,
    500: 10,
    3000: 60,
    10000: 200
}


def feetier_to_tickspacing(feetier: int) -> int:
    return feetier_to_tickspacing_dict[feetier]


def tick_to_raw_price_token0(tick: int) -> float:
    return 1.0001 ** tick


def raw_price_to_price_token0(decimals_token0: int, decimals_token1: int, raw_price_token0: float) -> float:
    return 10 ** (decimals_token1 - decimals_token0) / raw_price_token0


def tick_to_price_token0(tick: int, decimals_token0: int, decimals_token1: int) -> float:
    return raw_price_to_price_token0(decimals_token0, decimals_token1, tick_to_raw_price_token0(tick))


def get_active_tick(current_tick: int, tick_spacing: int) -> int:
    return floor(current_tick // tick_spacing) * tick_spacing
