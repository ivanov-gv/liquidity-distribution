import requests

from utils import raw_price_to_price_token0, raw_liquidity_to_token0_token1


def get_ticks(pool_address: str, tick_spacing: int,
              tick_lower_bound: int, tick_upper_bound: int,
              date_lower_bound: int, date_upper_bound: int,
              token0_decimals: int, token1_decimals: int) -> list[dict]:
    """

    :param pool_address:
    :param tick_lower_bound:
    :param tick_upper_bound:
    :param date_lower_bound:
    :param date_upper_bound:
    :param token0_decimals:
    :param token1_decimals:
    :return: list of ticks with pool day data
    """

    query = ''' 
        {{
          tickDayDatas(
            first: {first},
            skip: {skip},
            where: {{
              pool: "{pool}",
              date_lte: {date_lte}, 
              date_gte: {date_gte},
              tick_lte: "{pool}#{tick_lte}",
              tick_gte: "{pool}#{tick_gte}"
            }}) {{
            date
            tick{{
              price0,
              price1,
              liquidityNet,
              liquidityGross,
              createdAtTimestamp,
              tickIdx
            }}
          }}
        }} '''.format(first=200,
                      skip=0,
                      pool=pool_address,
                      date_lte=date_upper_bound,
                      date_gte=date_lower_bound,
                      tick_lte=tick_upper_bound,
                      tick_gte=tick_lower_bound)

    response = requests.post('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3', json={'query': query})

    if response.status_code != 200:
        raise RuntimeError(f"Response statuscode is not ok: {response.status_code}")

    tick_list = response.json()['data']['tickDayDatas']

    if not tick_list:
        return []

    raw_liquidity = 0
    for tick in tick_list:
        tick['price0'] = float(tick['tick']['price0'])
        tick['price1'] = float(tick['tick']['price1'])

        # Convert raw prices to actual ones
        tick['price0'] = raw_price_to_price_token0(token0_decimals, token1_decimals, tick['price0'])
        tick['price1'] = 1 / tick['price0']

        tick['liquidityNet'] = int(tick['tick']['liquidityNet'])
        tick['liquidityGross'] = int(tick['tick']['liquidityGross'])
        tick['createdAtTimestamp'] = int(tick['tick']['createdAtTimestamp'])
        tick['tickIdx'] = int(tick['tick']['tickIdx'])

        raw_liquidity += tick['liquidityNet']
        tick['liquidity'], _ = raw_liquidity_to_token0_token1(raw_liquidity, tick['tickIdx'], tick_spacing,
                                                              token0_decimals, token1_decimals)

        del tick['tick']

    return tick_list
