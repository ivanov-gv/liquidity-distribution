from graphql.pool import get_pool_info, get_pool_day_data
from graphql.tick import get_ticks
from utils import get_active_tick, feetier_to_tickspacing, tick_to_price_token0
from time import time
from datetime import datetime


def get_liquidity_distribution_data(pool_address: str, from_date: datetime, to_date: datetime,
                                    num_surrounding_ticks: int) -> list[dict]:
    """

    :param pool_address:
    :param from_date:
    :param to_date:
    :param num_surrounding_ticks:
    :return:
    """

    pool_info = get_pool_info(pool_address)
    tick_spacing = feetier_to_tickspacing(pool_info['feeTier'])
    from_timestamp = int(from_date.timestamp()) // 86400 * 86400
    to_timestamp = int(to_date.timestamp()) // 86400 * 86400

    active_ticks = get_pool_day_data(pool_address, from_timestamp, to_timestamp)

    for active_tick in active_ticks:
        tick_lower_bound = active_tick['tick'] - num_surrounding_ticks * tick_spacing
        tick_upper_bound = active_tick['tick'] + num_surrounding_ticks * tick_spacing
        liquidity_ticks = get_ticks(pool_address, tick_lower_bound, tick_upper_bound,
                                    active_tick['date'], active_tick['date'],
                                    pool_info['token0']['decimals'], pool_info['token1']['decimals'])

        ###
        # find next and previous tick to the current
        prev_tick_index = 0
        next_tick_index = 0
        for i in range(len(liquidity_ticks)):
            if liquidity_ticks[i]['tickIdx'] < active_tick['tick']:
                prev_tick_index = i
                continue
            if liquidity_ticks[i]['tickIdx'] > active_tick['tick']:
                next_tick_index = i
                break

        # go asc
        forward_ticks_liquidity = list()
        current_tick_liquidity = active_tick['liquidity']
        for i in range(next_tick_index, len(liquidity_ticks)):
            current_tick_liquidity = current_tick_liquidity + liquidity_ticks[i]['liquidityNet']
            forward_ticks_liquidity.append(current_tick_liquidity)

        # go desc
        previous_ticks_liquidity = list()
        current_tick_liquidity = active_tick['liquidity']
        for i in range(prev_tick_index, -1, -1):
            current_tick_liquidity = current_tick_liquidity - liquidity_ticks[i]['liquidityNet']
            previous_ticks_liquidity.append(current_tick_liquidity)

        # merge
        previous_ticks_liquidity.reverse()
        liquidity_list = previous_ticks_liquidity + forward_ticks_liquidity

        # add prices
        price_list = list()
        for tick in liquidity_ticks:
            price_list.append(tick['price0'])

        active_tick['liquidity_list'] = liquidity_list
        active_tick['price_list'] = price_list
        active_tick['current_price'] = tick_to_price_token0(active_tick['tick'],
                                                            pool_info['token0']['decimals'],
                                                            pool_info['token1']['decimals'])

    return active_ticks
