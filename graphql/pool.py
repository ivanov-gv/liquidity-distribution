from __future__ import annotations
import requests


class PoolInfo:
    __slots__ = (
        'tick',
        'fee_tier',
        'sqrt_price',
        'liquidity',
        'token0_decimals',
        'token1_decimals'
    )

    def __init__(self, tick: int, fee_tier: int, sqrt_price: int, liquidity: int, token0_decimals: int,
                 token1_decimals: int):
        self.tick: int = tick
        self.fee_tier: int = fee_tier
        self.sqrt_price: int = sqrt_price
        self.liquidity: int = liquidity
        self.token0_decimals: int = token0_decimals
        self.token1_decimals: int = token1_decimals

    @staticmethod
    def get(pool_address: str) -> PoolInfo:
        """
        Get pool statistics from subgraph for uniswap v3
        :param pool_address: pool address in 0x format
        :return: pool statistics
        """
        query = ''' 
        {{ pool(id: "{pool_address}") {{
              tick
              token0 {{
                decimals
              }}
              token1 {{
                decimals
              }}
              feeTier
              sqrtPrice
              liquidity
        }}}}'''.format(pool_address=pool_address)

        response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

        if response.status_code != 200:
            raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

        pool_data = response.json()['data']['pool']

        return PoolInfo(tick=int(pool_data['tick']),
                        fee_tier=int(pool_data['feeTier']),
                        sqrt_price=int(pool_data['sqrtPrice']),
                        liquidity=int(pool_data['liquidity']),
                        token0_decimals=int(pool_data['token0']['decimals']),
                        token1_decimals=int(pool_data['token1']['decimals']))


class PoolDateInfo:
    __slots__ = (
        'tick',
        'liquidity',
        'date'
    )

    def __init__(self, tick: int, liquidity: int, date: int):
        self.tick: int = tick
        self.liquidity: int = liquidity
        self.date: int = date

    @staticmethod
    def get(pool_address: str, date_lower_bound: int, date_upper_bound: int, first: int = 100) -> list[PoolDateInfo]:
        """

        :param pool_address:
        :param date_lower_bound:
        :param date_upper_bound:
        :return:
        """

        query = ''' 
          {{
            poolDayDatas(
              first: {first},
              where: {{
                pool: "{pool_address}",
                date_lte: {date_lte}, 
                date_gte: {date_gte},
              }}) 
            {{
              date
              tick
              liquidity
            }}
          }}'''.format(pool_address=pool_address,
                       date_lte=date_upper_bound,
                       date_gte=date_lower_bound,
                       first=first)

        response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

        if response.status_code != 200:
            raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

        pool_data_list = response.json()['data']['poolDayDatas']

        return [PoolDateInfo(tick=int(data['tick']),
                             liquidity=int(data['liquidity']),
                             date=data['date']
                             ) for data in pool_data_list]
