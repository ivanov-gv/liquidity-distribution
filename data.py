from graphql.pool import get_pool_info, get_pool_day_data
from graphql.tick import get_ticks
from utils import feetier_to_tickspacing, get_active_tick, tick_to_price_token0
from datetime import datetime

import pandas as pd


def get_liquidity_distribution_data(pool_address: str, from_date: datetime, to_date: datetime,
                                    num_surrounding_ticks: int) -> pd.DataFrame:
    """
    Get dataframe with all the data needed to draw histogram
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
        # find active pool tick
        active_tick = current_tick
        active_tick['tick'] = get_active_tick(current_tick['tick'], tick_spacing)
        active_tick['current_price'] = tick_to_price_token0(active_tick['tick'],
                                                            pool_info['token0']['decimals'],
                                                            pool_info['token1']['decimals'])

        # get all liquidity ticks
        tick_lower_bound = active_tick['tick'] - num_surrounding_ticks * tick_spacing
        tick_upper_bound = active_tick['tick'] + num_surrounding_ticks * tick_spacing
        liquidity_ticks = get_ticks(pool_address, tick_spacing,
                                    tick_lower_bound, tick_upper_bound,
                                    active_tick['date'], active_tick['date'],
                                    pool_info['token0']['decimals'], pool_info['token1']['decimals'])

        # build dataframe and normalize liquidity values to fit [0, 1]
        liquidity_ticks_df = pd.DataFrame(liquidity_ticks)
        max_liquidity = liquidity_ticks_df['liquidity'].max()
        min_liquidity = liquidity_ticks_df['liquidity'].min()
        liquidity_ticks_df['liquidity'] = liquidity_ticks_df['liquidity'] \
            .map(lambda x: (x - min_liquidity) / (max_liquidity - min_liquidity))

        # mark the bar with current active price
        liquidity_ticks_df['active_price'] = False
        liquidity_ticks_df.loc[
            liquidity_ticks_df.tickIdx == active_tick['tick'], ('active_price', 'liquidity')] = True, 1.0

        liquidity_df = pd.concat((liquidity_df, liquidity_ticks_df))

    return liquidity_df
