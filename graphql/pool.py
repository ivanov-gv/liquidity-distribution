import requests

from utils import tick_to_price_token0, liquidity_to_token0_token1, get_active_tick


def get_pool_info(pool_address: str) -> dict:
    """
    Get pool statistics from subgraph for uniswap v3
    :param pool_address: pool address in 0x format
    :return: pool statistics
    """
    query = ''' 
    {{ pool(id: "{pool_address}") {{
          tick
          token0 {{
            symbol
            id
            decimals
          }}
          token1 {{
            symbol
            id
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

    # Convert fields to a preferred type
    pool_data['tick'] = int(pool_data['tick'])
    pool_data['feeTier'] = int(pool_data['feeTier'])
    pool_data['sqrtPrice'] = int(pool_data['sqrtPrice'])
    # TODO: calculate adjusted liquidity
    pool_data['liquidity'] = int(pool_data['liquidity'])
    pool_data['token0']['decimals'] = int(pool_data['token0']['decimals'])
    pool_data['token1']['decimals'] = int(pool_data['token1']['decimals'])
    return pool_data


def get_pool_day_data(pool_address: str, tick_spacing: int,
                      date_lower_bound: int, date_upper_bound: int,
                      token0_decimals: int, token1_decimals: int) -> list[dict]:
    """

    :param pool_address:
    :param date_lower_bound:
    :param date_upper_bound:
    :return:
    """

    query = ''' 
      {{
        poolDayDatas(
          first: 100,
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
                   date_gte=date_lower_bound)

    response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

    if response.status_code != 200:
        raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

    pool_data_list = response.json()['data']['poolDayDatas']

    if not pool_data_list:
        return []

    for data in pool_data_list:
        data['tick'] = int(data['tick'])
        data['liquidity'] = int(data['liquidity'])
        data['current_price'] = tick_to_price_token0(data['tick'], token0_decimals, token1_decimals)

        # recalculate liquidity to adjusted
        lower_tick = get_active_tick(data['tick'], tick_spacing)
        upper_tick = lower_tick + tick_spacing
        data['liquidityAdj'], _ = liquidity_to_token0_token1(data['liquidity'], lower_tick, upper_tick,
                                                             token0_decimals, token1_decimals)

    return pool_data_list
