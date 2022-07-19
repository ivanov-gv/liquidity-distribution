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


def raw_liquidity_to_token0_token1(liquidity_raw: int, tick: int, tick_spacing: int, decimals0: int, decimals1: int) \
        -> (float, float):
    # Compute the tick range. This code would work as well in Python: `tick // TICK_SPACING * TICK_SPACING`
    # However, using floor() is more portable.
    bottom_tick = floor(tick / tick_spacing) * tick_spacing
    top_tick = bottom_tick + tick_spacing

    # Compute the current price and adjust it to a human-readable format
    price = tick_to_raw_price_token0(tick)

    # Compute square roots of prices corresponding to the bottom and top ticks
    sa = tick_to_raw_price_token0(bottom_tick // 2)
    sb = tick_to_raw_price_token0(top_tick // 2)
    sp = price ** 0.5

    # Compute real amounts of the two assets
    amount0 = liquidity_raw * (sb - sp) / (sp * sb)
    amount1 = liquidity_raw * (sp - sa)

    return amount0, amount1
