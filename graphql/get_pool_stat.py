import requests


def get_pool_stat(pool_address: str) -> dict:
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
    pool_data['liquidity'] = int(pool_data['liquidity'])
    pool_data['token0']['decimals'] = int(pool_data['token0']['decimals'])
    pool_data['token1']['decimals'] = int(pool_data['token1']['decimals'])
    return pool_data
