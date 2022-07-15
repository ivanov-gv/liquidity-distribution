import requests


def get_ticks(pool_address: str, tick_lower_bound: int, tick_upper_bound: int,
              date_lower_bound: int, date_upper_bound: int) -> list:
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
        }} '''.format(first=100,
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

    # Move fields from underlying 'tick' dictionary and convert fields to proper types
    for tick in tick_list:
        tick['price0'] = float(tick['tick']['price0'])
        tick['price1'] = float(tick['tick']['price1'])

        tick['liquidityNet'] = int(tick['tick']['liquidityNet'])
        tick['liquidityGross'] = int(tick['tick']['liquidityGross'])
        tick['createdAtTimestamp'] = int(tick['tick']['createdAtTimestamp'])
        tick['tickIdx'] = int(tick['tick']['tickIdx'])

        del tick['tick']

    return tick_list
