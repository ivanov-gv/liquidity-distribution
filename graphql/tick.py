from __future__ import annotations
import datetime
import requests

from utils import raw_price_to_price_token0, liquidity_to_token0_token1


class TickInfo:
    __slots__ = (
        'date',
        'readable_date',
        'liquidity_net',
        'tick_idx'
    )

    def __init__(self, date: int, readable_date: str, liquidity_net: int, tick_idx: int):
        self.date = date
        self.readable_date = readable_date
        self.liquidity_net = liquidity_net
        self.tick_idx = tick_idx

    @staticmethod
    def get(pool_address: str,
            tick_lower_bound: int, tick_upper_bound: int,
            date_lower_bound: int, date_upper_bound: int,
            first: int = 200) -> list[TickInfo]:
        """

        :param pool_address:
        :param tick_lower_bound:
        :param tick_upper_bound:
        :param date_lower_bound:
        :param date_upper_bound:
        :return: list of ticks with pool day data
        """

        query = ''' 
            {{
              tickDayDatas(
                first: {first},
                where: {{
                  pool: "{pool}",
                  date_lte: {date_lte}, 
                  date_gte: {date_gte},
                  tick_lte: "{pool}#{tick_lte}",
                  tick_gte: "{pool}#{tick_gte}"
                }}) {{
                date
                tick{{
                  liquidityNet,
                  tickIdx
                }}
              }}
            }} '''.format(first=first,
                          pool=pool_address,
                          date_lte=date_upper_bound,
                          date_gte=date_lower_bound,
                          tick_lte=tick_upper_bound,
                          tick_gte=tick_lower_bound)

        response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

        if response.status_code != 200:
            raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

        tick_list = response.json()['data']['tickDayDatas']

        return [TickInfo(date=tick['date'],
                         readable_date=str(datetime.date.fromtimestamp(tick['date'])),
                         liquidity_net=int(tick['tick']['liquidityNet']),
                         tick_idx=int(tick['tick']['tickIdx']))
                for tick in tick_list]

    @staticmethod
    def get_current(pool_address: str,
                    tick_lower_bound: int, tick_upper_bound: int,
                    first: int = 400) -> list[TickInfo]:
        query = ''' 
            {{
              ticks(
                first: {first},
                where: {{
                  pool: "{pool}",
                  tickIdx_lte: "{tick_lte}",
                  tickIdx_gte: "{tick_gte}"
                }}) {{
                  liquidityNet,
                  tickIdx
              }}
            }} '''.format(first=first,
                          pool=pool_address,
                          tick_lte=tick_upper_bound,
                          tick_gte=tick_lower_bound)

        response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

        if response.status_code != 200:
            raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

        tick_list = response.json()['data']['ticks']

        now = datetime.datetime.now()
        date = int(now.timestamp())
        readable_date = str(now)

        return [TickInfo(date=date,
                         readable_date=readable_date,
                         liquidity_net=int(tick['liquidityNet']),
                         tick_idx=int(tick['tickIdx']))
                for tick in tick_list]
