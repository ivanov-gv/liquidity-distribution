from graphql.pool import get_pool_info, get_pool_day_data
from graphql.tick import *
from utils import *
from datetime import datetime

import pandas as pd


def get_liquidity_distribution_for_period(pool_address: str, from_date: datetime, to_date: datetime,
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

    pool_current_ticks = get_pool_day_data(pool_address, tick_spacing,
                                           from_timestamp, to_timestamp,
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

        liquidity_ticks_df = pd.DataFrame(liquidity_ticks)
        nearest_using_tick = liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx <= active_tick['tick'], 'tickIdx'].max()
        calculated_liquidity = liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == nearest_using_tick] \
            .iloc[0]['liquidity']
        liquidity_ticks_df['liquidity'] = liquidity_ticks_df['liquidity'] \
            .map(lambda x: x - calculated_liquidity + active_tick['liquidity'])

        # mark the bar with current active price
        liquidity_ticks_df['active_price'] = False
        liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == nearest_using_tick, 'active_price'] = True

        liquidity_df = pd.concat((liquidity_df, liquidity_ticks_df))

    return liquidity_df


def get_liquidity_distribution_for_today(pool_address: str, num_surrounding_ticks: int) -> pd.DataFrame:
    """

    :param pool_address:
    :param num_surrounding_ticks:
    :return:
    """

    pool_info = get_pool_info(pool_address)
    tick_spacing = feetier_to_tickspacing(pool_info['feeTier'])
    active_tick = get_active_tick(pool_info['tick'], tick_spacing)
    token0_decimals = pool_info['token0']['decimals']
    token1_decimals = pool_info['token1']['decimals']
    active_tick_liquidity, _ = liquidity_to_token0_token1(pool_info['liquidity'],
                                                          active_tick, active_tick + tick_spacing,
                                                          token0_decimals, token1_decimals)

    tick_lower_bound = active_tick - num_surrounding_ticks * tick_spacing
    tick_upper_bound = active_tick + num_surrounding_ticks * tick_spacing
    liquidity_list = get_current_ticks(pool_address, tick_spacing, tick_lower_bound, tick_upper_bound,
                                       token0_decimals, token1_decimals)

    liquidity_ticks_df = pd.DataFrame(liquidity_list)
    nearest_using_tick = liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx <= active_tick, 'tickIdx'].max()
    calculated_liquidity = liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == nearest_using_tick] \
        .iloc[0]['liquidity']
    liquidity_ticks_df['liquidity'] = liquidity_ticks_df['liquidity'] \
        .map(lambda x: x - calculated_liquidity + active_tick_liquidity)

    # mark the bar with current active price
    liquidity_ticks_df['active_price'] = False
    liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == nearest_using_tick, 'active_price'] = True

    return liquidity_ticks_df


def get_liquidity_distribution_full(pool_address: str) -> pd.DataFrame:
    pool_info = get_pool_info(pool_address)
    tick_spacing = feetier_to_tickspacing(pool_info['feeTier'])
    active_tick = get_active_tick(pool_info['tick'], tick_spacing)
    token0_decimals = pool_info['token0']['decimals']
    token1_decimals = pool_info['token1']['decimals']
    active_tick_liquidity, _ = liquidity_to_token0_token1(pool_info['liquidity'],
                                                          active_tick, active_tick + tick_spacing,
                                                          token0_decimals, token1_decimals)

    today_timestamp = int(datetime(year=2021, month=4, day=25).timestamp()) // 86400 * 86400

    tick_list = get_ticks(pool_address, tick_spacing,
                          tick_lower_bound=0, tick_upper_bound=200 * tick_spacing,
                          date_lower_bound=today_timestamp, date_upper_bound=today_timestamp,
                          token0_decimals=token0_decimals, token1_decimals=token1_decimals)

    current_tick = tick_list[0]
    tick_list = tick_list[1:]
    final_tick_list = []
    liquidity_raw = 0
    liquidity_sum = 0

    while tick_list:
        for next_tick in tick_list:
            liquidity_raw += current_tick['liquidityNet']
            liquidity_adj, _ = liquidity_to_token0_token1(liquidity_raw,
                                                          current_tick['tickIdx'], next_tick['tickIdx'],
                                                          token0_decimals, token1_decimals)
            liquidity_sum += liquidity_adj

            current_tick['liquidityRaw'] = liquidity_raw
            current_tick['liquidityAdj'] = liquidity_adj
            current_tick['liquiditySum'] = liquidity_sum
            final_tick_list.append(current_tick)

            current_tick = next_tick

        tick_list = get_ticks(pool_address, tick_spacing,
                              tick_lower_bound=current_tick['tickIdx'] + tick_spacing,
                              tick_upper_bound=current_tick['tickIdx'] + tick_spacing * 201,
                              date_lower_bound=today_timestamp, date_upper_bound=today_timestamp,
                              token0_decimals=token0_decimals, token1_decimals=token1_decimals)

    half_liquidity = final_tick_list[-1]['liquiditySum'] / 2

    liquidity_ticks_df = pd.DataFrame(final_tick_list)
    equal_liquidity_tick = liquidity_ticks_df.loc[liquidity_ticks_df.liquiditySum <= half_liquidity, 'tickIdx'].max()

    # mark the bar with current active price
    liquidity_ticks_df['equal_liquidity_price'] = False
    liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == equal_liquidity_tick, 'equal_liquidity_price'] = True
    return liquidity_ticks_df

