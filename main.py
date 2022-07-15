from graphql.get_pool_stat import get_pool_stat
from graphql.get_ticks import get_ticks
from utils import get_active_tick, feetier_to_tickspacing, raw_price_to_price_token0
from time import time

if __name__ == "__main__":
    #   Get pool info
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    pool_info = get_pool_stat(pool_address)

    #   Get ticks info
    tick_spacing = feetier_to_tickspacing(pool_info['feeTier'])

    # The pools current tick isn't necessarily a tick that can actually be initialized.
    # Find the nearest valid tick given the tick spacing.
    active_tick = get_active_tick(pool_info['tick'], tick_spacing)
    num_surrounding_ticks = 10

    # Our search bounds must take into account fee spacing. i.e. for fee tier 1%, only
    # ticks with index 200, 400, 600, etc can be active.
    tick_lower_bound = active_tick - num_surrounding_ticks * tick_spacing
    tick_upper_bound = active_tick + num_surrounding_ticks * tick_spacing

    # Round current timestamp to be dividable by 86400. Result is a timestamp at the beginning of the current date
    current_day = int(time()) // 86400 * 86400

    ticks = get_ticks(pool_address, tick_lower_bound, tick_upper_bound, current_day, current_day)
    for tick in ticks:
        tick['price0'] = raw_price_to_price_token0(pool_info['token0']['decimals'], pool_info['token1']['decimals'], tick['price0'])
        tick['price1'] = 1 / tick['price0']
