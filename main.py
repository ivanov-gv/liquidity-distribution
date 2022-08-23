# python 3.10
import plotly.express as px
from data import get_liquidity_distribution, get_current_liquidity_distribution
from datetime import datetime, timedelta
from utils import feetier_to_fee_percent
from graphql.pool import PoolInfo

if __name__ == "__main__":
    # usdc eth 0.3 - 0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8
    # btc usdc 0.3 - 0x99ac8ca7087fa4a2a1fb6357269965a2014abc35

    pool_address = "0x99ac8ca7087fa4a2a1fb6357269965a2014abc35"
    base_token1 = True

    for_current_moment = True
    from_date = datetime(year=2022, month=8, day=1)
    to_date = datetime(year=2022, month=8, day=17)
    step = timedelta(days=1)

    pool = PoolInfo.get(pool_address)
    if for_current_moment:
        liquidity_data = get_current_liquidity_distribution(pool, price_bounds_multiplier=3.0, base_token1=base_token1)
    else:
        liquidity_data = get_liquidity_distribution(pool, from_date, to_date, step, progress_bar=True,
                                                    price_bounds_multiplier=3.0, base_token1=base_token1)

    if base_token1:
        x = 'price1'
        y = 'liquidityAdj1'
    else:
        x = 'price0'
        y = 'liquidityAdj0'

    fig = px.bar(liquidity_data, x=x, y=y, animation_frame="readable_date", color='label',
                 title=f'{pool.pair_name} {feetier_to_fee_percent(pool.fee_tier)} % , '
                       f'is current moment - {for_current_moment}')
    fig["layout"].pop("updatemenus")
    fig.show()
