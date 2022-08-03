from console_progressbar import ProgressBar
from datetime import date, datetime, timedelta
import pandas as pd
from math import log

from utils import *
from graphql.pool import PoolInfo, PoolDateInfo
from graphql.tick import TickInfo


def _get_liquidity_distribution(pool: PoolInfo, _date: Union[datetime, None],
                                num_surrounding_ticks: int) -> pd.DataFrame:
    """
    Get dataframe containing all ticks in range
    [active_tick - num_surrounding_ticks * pool.tick_spacing, active_tick + num_surrounding_ticks * pool.tick_spacing],

    :param pool: info about pool
    :param _date: datetime() for specific date or None for getting current moment data
    :param num_surrounding_ticks: width of the range counted in initialized ticks
    :return: pandas.DataFrame with columns:
            'tickIdx': tick id, integer
            'liquidityRaw': raw liquidity, integer,
            'liquidityNet': liquidity net, integer
            'liquidityAdj0': adjusted liquidity in token0,
            'liquidityAdj1': adjusted liquidity in token1,
            'price0': price in token0,
            'price1': price in token1
    """

    if _date:
        date_timestamp = round_timestamp_to_day(_date.timestamp())
        active_tick_info = PoolDateInfo.get(pool, date_timestamp)
    else:
        date_timestamp = int(datetime.now().timestamp())
        active_tick_info = pool

    max_num_ticks = min(200, num_surrounding_ticks)

    price_token0 = tick_to_price_token0(active_tick_info.active_tick, pool.token0_decimals, pool.token1_decimals)
    price_token1 = 1 / price_token0

    # create all ticks from active_tick to active_tick + num_surrounding_ticks * pool.tick_spacing in ascending order
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

        # get ticks with liquidity info
        if _date:
            tick_list = TickInfo.get(pool.address,
                                     tick_lower_bound=current_tick['tickIdx'],
                                     tick_upper_bound=next_tick_upper_bound,
                                     date_timestamp=date_timestamp,
                                     first=max_num_ticks)
        else:
            tick_list = TickInfo.get_current(pool.address,
                                             tick_lower_bound=current_tick['tickIdx'],
                                             tick_upper_bound=next_tick_upper_bound,
                                             first=max_num_ticks)

        # create all ticks and fill with liquidity info
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

    # create all ticks from active_tick - pool.tick_spacing to
    #   active_tick - num_surrounding_ticks * pool.tick_spacing in descending order
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

        # get ticks with liquidity info
        if _date:
            tick_list = TickInfo.get(pool.address,
                                     tick_lower_bound=next_tick_lower_bound,
                                     tick_upper_bound=current_tick['tickIdx'],
                                     date_timestamp=date_timestamp)
        else:
            tick_list = TickInfo.get_current(pool.address,
                                             tick_lower_bound=next_tick_lower_bound,
                                             tick_upper_bound=current_tick['tickIdx'])
        # turn to ascending order
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


def mark_half_liquidity_price(liquidity_ticks_df: pd.DataFrame, use_token1: bool) -> None:
    """
    Mark price at which sum liquidity on the left side is equal to sum liquidity on the right side
    :param liquidity_ticks_df: dataframe from _get_liquidity_distribution()
    :param use_token1: indicate which token to use for calculation
    :return: liquidity_ticks_df with changed 'label' column
    """
    if use_token1:
        liquidity_label = 'liquidityAdj1'
    else:
        liquidity_label = 'liquidityAdj0'

    liquidity_adj_cum_sum = liquidity_ticks_df[liquidity_label].cumsum()
    liquidity_sum = liquidity_adj_cum_sum.iloc[-1]
    half_liquidity = liquidity_adj_cum_sum.loc[liquidity_adj_cum_sum <= liquidity_sum / 2].max()

    half_liquidity_index = liquidity_adj_cum_sum[liquidity_adj_cum_sum == half_liquidity].index[0]
    liquidity_ticks_df.loc[liquidity_ticks_df.index == half_liquidity_index, 'label'] = 'half liquidity'


def get_liquidity_distribution(pool: PoolInfo,
                               from_date: datetime, to_date: datetime, step: timedelta,
                               price_bounds_multiplier: float = 2.0,
                               progress_bar: bool = True,
                               base_token1: bool = True) -> pd.DataFrame:
    """
    Get liquidity distribution for specific time range
    :param pool: pool to get the info from
    :param from_date: left bound of the time range
    :param to_date: right bound of the time range
    :param step:
    :param price_bounds_multiplier: price at the left border of graph will be price_bounds_multiplier times less
            than active price and also price at the right border will be price_bounds_multiplier times more than
            active price
    :param progress_bar: draw progressbar or not
    :param base_token1: True if you want to use token1 as a base token, False otherwise
    :return: pandas.DataFrame
    """
    total = to_date.timestamp() - from_date.timestamp()
    pb = ProgressBar(total, prefix='loading liquidity data', length=50)

    num_surrounding_ticks = int(log(price_bounds_multiplier, 1.0001)) // pool.tick_spacing

    _date = from_date
    liquidity_data = pd.DataFrame()

    while _date <= to_date:
        if progress_bar:
            pb.print_progress_bar(_date.timestamp() - from_date.timestamp())
        data = _get_liquidity_distribution(pool, _date, num_surrounding_ticks)
        mark_half_liquidity_price(data, use_token1=base_token1)
        liquidity_data = pd.concat((liquidity_data, data))
        _date = _date + step

    if progress_bar:
        pb.print_progress_bar(total)

    return liquidity_data


def get_current_liquidity_distribution(pool: PoolInfo,
                                       price_bounds_multiplier: float = 2.0,
                                       base_token1: bool = True) -> pd.DataFrame:
    """
    Get liquidity distribution for current moment
    :param pool: pool to get the info from
    :param price_bounds_multiplier: price at the left border of graph will be price_bounds_multiplier times less
            than active price and also price at the right border will be price_bounds_multiplier times more than
            active price
    :param base_token1: True if you want to use token1 as a base token, False otherwise
    :return: pandas.DataFrame
    """
    num_surrounding_ticks = int(log(price_bounds_multiplier, 1.0001)) // pool.tick_spacing
    data = _get_liquidity_distribution(pool, None, num_surrounding_ticks)
    mark_half_liquidity_price(data, use_token1=base_token1)
    return data
