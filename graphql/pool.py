from __future__ import annotations
import requests

from utils import feetier_to_tickspacing, get_active_tick, liquidity_to_token0_token1_adj


class PoolInfo:
    __slots__ = (
        'address',
        'current_tick',
        'active_tick',
        'fee_tier',
        'tick_spacing',
        'liquidity',
        'token0_decimals',
        'token1_decimals',
        'liquidity_token0',
        'liquidity_token1',
        'price_token1',
        'price_token0',
        'pair_name',
    )

    def __init__(self, address: str, tick: int, fee_tier: int, liquidity: int,
                 token0_decimals: int, token1_decimals: int,
                 price_token1: float, price_token0: float,
                 symbol0: str, symbol1: str):
        self.address = address
        self.current_tick: int = tick
        self.tick_spacing: int = feetier_to_tickspacing(fee_tier)
        self.fee_tier: int = fee_tier
        self.active_tick: int = get_active_tick(tick, self.tick_spacing)
        self.liquidity: int = liquidity
        self.token0_decimals: int = token0_decimals
        self.token1_decimals: int = token1_decimals
        liquidity_token0, liquidity_token1 = liquidity_to_token0_token1_adj(liquidity,
                                                                            self.active_tick,
                                                                            self.active_tick + self.tick_spacing,
                                                                            token0_decimals, token1_decimals)
        self.liquidity_token0: float = liquidity_token0
        self.liquidity_token1: float = liquidity_token1
        self.price_token0: float = price_token0
        self.price_token1: float = price_token1
        self.pair_name: str = f'{symbol0}/{symbol1}'

    @staticmethod
    def get(pool_address: str) -> PoolInfo:
        """
        Get pool statistics from subgraph for uniswap v3
        :param pool_address: pool address in 0x format
        :return: PoolInfo
        """
        query = ''' 
        {{ pool(id: "{pool_address}") {{
              tick
              token0 {{
                decimals
                symbol
              }}
              token1 {{
                decimals
                symbol
              }}
              feeTier
              liquidity
              token0Price
              token1Price
        }}}}'''.format(pool_address=pool_address)

        response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

        if response.status_code != 200:
            raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

        pool_data = response.json()['data']['pool']

        return PoolInfo(address=pool_address,
                        tick=int(pool_data['tick']),
                        fee_tier=int(pool_data['feeTier']),
                        liquidity=int(pool_data['liquidity']),
                        token0_decimals=int(pool_data['token0']['decimals']),
                        token1_decimals=int(pool_data['token1']['decimals']),
                        price_token1=float(pool_data['token1Price']),
                        price_token0=float(pool_data['token0Price']),
                        symbol0=pool_data['token0']['symbol'],
                        symbol1=pool_data['token1']['symbol'])


class PoolDateInfo:
    __slots__ = (
        'current_tick',
        'active_tick',
        'liquidity',
        'liquidity_token0',
        'liquidity_token1',
        'price_token0',
        'price_token1',
        'date'
    )

    def __init__(self, tick: int, active_tick: int, liquidity: int,
                 liquidity_token0: float, liquidity_token1: float,
                 price_token0: float, price_token1: float,
                 date: int):
        self.current_tick: int = tick
        self.active_tick: int = active_tick
        self.liquidity: int = liquidity
        self.liquidity_token0: float = liquidity_token0
        self.liquidity_token1: float = liquidity_token1
        self.price_token0: float = price_token0
        self.price_token1: float = price_token1
        self.date: int = date

    @staticmethod
    def get(pool: PoolInfo, date: int) -> PoolDateInfo:
        """
        Get pool statistics from subgraph for uniswap v3
        :param pool: pool_address: pool address in 0x format
        :param date:
        :return: PoolDateInfo
        """

        query = ''' 
        {{
            poolDayData(
              id: "{pool_address}-{date}") 
            {{
              date
              tick
              liquidity
              token0Price,
              token1Price
            }}
        }}'''.format(pool_address=pool.address,
                     date=date // 86400)

        response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

        if response.status_code != 200:
            raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

        data = response.json()['data']['poolDayData']

        tick = int(data['tick'])
        active_tick = get_active_tick(tick, pool.tick_spacing)
        liquidity = int(data['liquidity'])
        liquidity_token0, liquidity_token1 = liquidity_to_token0_token1_adj(liquidity, active_tick,
                                                                            active_tick + pool.tick_spacing,
                                                                            pool.token0_decimals, pool.token1_decimals)
        return PoolDateInfo(tick=tick,
                            active_tick=active_tick,
                            liquidity=liquidity,
                            liquidity_token0=liquidity_token0,
                            liquidity_token1=liquidity_token1,
                            price_token0=float(data['token0Price']),
                            price_token1=float(data['token1Price']),
                            date=data['date'])
