from graphql.pool import get_pool_info, get_pool_day_data
from graphql.tick import get_ticks
from utils import feetier_to_tickspacing, get_active_tick
from datetime import datetime

import pandas as pd


def get_liquidity_distribution_data(pool_address: str, from_date: datetime, to_date: datetime,
                                    num_surrounding_ticks: int) -> pd.DataFrame:
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

    pool_current_ticks = get_pool_day_data(pool_address, from_timestamp, to_timestamp,
                                     pool_info['token0']['decimals'], pool_info['token1']['decimals'])

    liquidity_df = pd.DataFrame()
    for current_tick in pool_current_ticks:
        # find initialized tick
        # const activeTickIdx = Math.floor(poolCurrentTickIdx / tickSpacing) * tickSpacing
        active_tick = current_tick
        active_tick['tick'] = get_active_tick(current_tick['tick'], tick_spacing)

        tick_lower_bound = active_tick['tick'] - num_surrounding_ticks * tick_spacing
        tick_upper_bound = active_tick['tick'] + num_surrounding_ticks * tick_spacing
        liquidity_ticks = get_ticks(pool_address, tick_lower_bound, tick_upper_bound,
                                    active_tick['date'], active_tick['date'],
                                    pool_info['token0']['decimals'], pool_info['token1']['decimals'])

        liquidity_ticks_df = pd.DataFrame(liquidity_ticks)
        prev_tick = liquidity_ticks_df['tickIdx'] \
            .loc[(liquidity_ticks_df.tickIdx <= active_tick['tick']) &
                 (liquidity_ticks_df.tickIdx > active_tick['tick'] - tick_spacing)]
        prev_tick_index = prev_tick.index[0]

        liquidity_ticks_df['liquidity'] = liquidity_ticks_df['liquidityNet'].cumsum()
        difference = active_tick['liquidity'] - liquidity_ticks_df.loc[prev_tick_index, 'liquidity']
        liquidity_ticks_df['liquidity'] = liquidity_ticks_df['liquidity'].map(lambda x: x + difference)

        liquidity_df = pd.concat((liquidity_df, liquidity_ticks_df))

    return liquidity_df
