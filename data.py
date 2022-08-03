from console_progressbar import ProgressBar
from datetime import datetime, timedelta
import pandas as pd
from math import isnan, log

from utils import *
from graphql.pool import PoolInfo, PoolDateInfo
from graphql.tick import TickInfo


def get_liquidity_distribution_current(pool: PoolInfo, num_surrounding_ticks: int) -> pd.DataFrame:
    """

    :param pool:
    :param num_surrounding_ticks:
    :return:
    """

    tick_lower_bound = pool.active_tick - num_surrounding_ticks * pool.tick_spacing
    tick_upper_bound = pool.active_tick + num_surrounding_ticks * pool.tick_spacing
    liquidity_list = TickInfo.get_current(pool.address, pool.tick_spacing, tick_lower_bound, tick_upper_bound)

    liquidity_ticks_df = pd.DataFrame(liquidity_list)
    nearest_using_tick = liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx <= pool.active_tick, 'tickIdx'].max()
    calculated_liquidity = liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == nearest_using_tick] \
        .iloc[0]['liquidity']
    liquidity_ticks_df['liquidity'] = liquidity_ticks_df['liquidity'] \
        .map(lambda x: x - calculated_liquidity + pool.liquidity_token0_adj)

    # mark the bar with current active price
    liquidity_ticks_df['active_price'] = False
    liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == nearest_using_tick, 'active_price'] = True

    return liquidity_ticks_df


def get_liquidity_distribution_on_date(pool: PoolInfo, date: datetime.date,
                                       num_surrounding_ticks: int) -> pd.DataFrame:
    date_timestamp = round_timestamp_to_day(date.timestamp())
    active_tick_info = PoolDateInfo.get(pool, date_timestamp)

    max_num_ticks = min(200, num_surrounding_ticks)

    price_token0 = tick_to_price_token0(active_tick_info.active_tick, pool.token0_decimals, pool.token1_decimals)
    price_token1 = 1 / price_token0

    # asc
    final_tick_list_asc = []
    tick_highest = active_tick_info.active_tick + num_surrounding_ticks * pool.tick_spacing
    current_tick = {'tickIdx': active_tick_info.active_tick,
                    'liquidityRaw': active_tick_info.liquidity,
                    'liquidityNet': 0,
                    'liquidityAdj0': active_tick_info.liquidity_token0,
                    'liquidityAdj1': active_tick_info.liquidity_token1,
                    'price0': price_token0,
                    'price1': price_token1}

    while current_tick['tickIdx'] <= tick_highest:
        next_tick_upper_bound = min(tick_highest, current_tick['tickIdx'] + pool.tick_spacing * max_num_ticks)

        tick_list = TickInfo.get(pool.address,
                                 tick_lower_bound=current_tick['tickIdx'],
                                 tick_upper_bound=next_tick_upper_bound,
                                 date_timestamp=date_timestamp, first=max_num_ticks)

        for tick_idx in range(current_tick['tickIdx'], next_tick_upper_bound + 1, pool.tick_spacing):
            if tick_list and tick_list[0].tick_idx == tick_idx:
                current_tick['liquidityNet'] = tick_list[0].liquidity_net
                tick_list = tick_list[1:]

            final_tick_list_asc.append(current_tick)

            # next tick
            next_tick_idx = tick_idx + pool.tick_spacing
            liquidity_raw_next = current_tick['liquidityRaw'] + current_tick['liquidityNet']
            liquidity_adj_next0, _ = liquidity_to_token0_token1_adj(liquidity_raw_next,
                                                                    next_tick_idx,
                                                                    next_tick_idx + pool.tick_spacing,
                                                                    pool.token0_decimals, pool.token1_decimals)

            liquidity_adj_next1 = liquidity_adj_next0 * active_tick_info.price_token1

            price_token0 = tick_to_price_token0(next_tick_idx, pool.token0_decimals, pool.token1_decimals)
            price_token1 = 1 / price_token0

            current_tick = {'tickIdx': next_tick_idx,
                            'liquidityRaw': liquidity_raw_next,
                            'liquidityNet': 0,
                            'liquidityAdj0': liquidity_adj_next0,
                            'liquidityAdj1': liquidity_adj_next1,
                            'price0': price_token0,
                            'price1': price_token1}

    # desc
    final_tick_list_desc = []
    tick_lowest = active_tick_info.active_tick - num_surrounding_ticks * pool.tick_spacing
    current_tick = {'tickIdx': active_tick_info.active_tick - pool.tick_spacing,
                    'liquidityRaw': active_tick_info.liquidity,
                    'liquidityNet': 0,
                    'liquidityAdj0': 0,
                    'liquidityAdj1': 0,
                    'price0': 0,
                    'price1': 0}

    while current_tick['tickIdx'] > tick_lowest:
        next_tick_lower_bound = max(tick_lowest, current_tick['tickIdx'] - max_num_ticks * pool.tick_spacing)

        tick_list = TickInfo.get(pool.address,
                                 tick_lower_bound=next_tick_lower_bound,
                                 tick_upper_bound=current_tick['tickIdx'],
                                 date_timestamp=date_timestamp)

        tick_list.reverse()

        for tick_idx in range(current_tick['tickIdx'], next_tick_lower_bound - pool.tick_spacing, -pool.tick_spacing):
            current_tick['tickIdx'] = tick_idx
            current_tick['liquidityNet'] = 0

            if tick_list and tick_list[0].tick_idx == tick_idx:
                current_tick['liquidityNet'] = tick_list[0].liquidity_net
                current_tick['liquidityRaw'] -= current_tick['liquidityNet']
                tick_list = tick_list[1:]

            _, liquidity_adj1 = liquidity_to_token0_token1_adj(current_tick['liquidityRaw'],
                                                               current_tick['tickIdx'],
                                                               current_tick['tickIdx'] + pool.tick_spacing,
                                                               pool.token0_decimals, pool.token1_decimals)

            liquidity_adj0 = liquidity_adj1 * active_tick_info.price_token0

            price_token0 = tick_to_price_token0(current_tick['tickIdx'], pool.token0_decimals, pool.token1_decimals)
            price_token1 = 1 / price_token0

            current_tick.update({'liquidityAdj0': liquidity_adj0,
                                 'liquidityAdj1': liquidity_adj1,
                                 'price0': price_token0,
                                 'price1': price_token1})

            final_tick_list_desc.append(current_tick.copy())

    final_tick_list_desc.reverse()
    liquidity_ticks_df = pd.DataFrame(final_tick_list_desc + final_tick_list_asc)

    # mark current price
    liquidity_ticks_df['readable_date'] = str(date.fromtimestamp(date_timestamp))
    liquidity_ticks_df['label'] = 'price'
    liquidity_ticks_df.loc[liquidity_ticks_df.tickIdx == active_tick_info.active_tick, 'label'] = 'active price'
    return liquidity_ticks_df


def mark_half_liquidity_price(liquidity_ticks_df: pd.DataFrame, use_token1: bool = False) -> None:
    if use_token1:
        liquidity_label = 'liquidityAdj1'
    else:
        liquidity_label = 'liquidityAdj0'

    liquidity_adj_cum_sum = liquidity_ticks_df[liquidity_label].cumsum()
    liquidity_sum = liquidity_adj_cum_sum.iloc[-1]
    half_liquidity = liquidity_adj_cum_sum.loc[liquidity_adj_cum_sum <= liquidity_sum / 2].max()

    if isnan(half_liquidity):
        return
    half_liquidity_index = liquidity_adj_cum_sum[liquidity_adj_cum_sum == half_liquidity].index[0]
    liquidity_ticks_df.loc[liquidity_ticks_df.index == half_liquidity_index, 'label'] = 'half liquidity'


def get_liquidity_distribution(pool: PoolInfo,
                               from_date: datetime, to_date: datetime, step: timedelta,
                               price_bounds_multiplier: float = 2.0,
                               progress_bar: bool = True) -> pd.DataFrame:

    total = to_date.timestamp() - from_date.timestamp()
    pb = ProgressBar(total, prefix='loading liquidity data', length=50)

    num_surrounding_ticks = int(log(price_bounds_multiplier, 1.0001)) // pool.tick_spacing

    date = from_date
    liquidity_data = pd.DataFrame()

    while date <= to_date:
        if progress_bar:
            pb.print_progress_bar(date.timestamp() - from_date.timestamp())
        data = get_liquidity_distribution_on_date(pool, date, num_surrounding_ticks)
        mark_half_liquidity_price(data)
        liquidity_data = pd.concat((liquidity_data, data))
        date = date + step

    if progress_bar:
        pb.print_progress_bar(total)

    return liquidity_data
