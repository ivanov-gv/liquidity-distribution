# python 3.10
import plotly.express as px
from data import get_liquidity_distribution, get_current_liquidity_distribution
from datetime import datetime, timedelta

from graphql.pool import PoolInfo

if __name__ == "__main__":
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    base_token1 = False

    for_current_moment = False
    from_date = datetime(year=2021, month=12, day=1)
    to_date = datetime(year=2022, month=1, day=1)
    step = timedelta(days=7)

    pool = PoolInfo.get(pool_address)
    if for_current_moment:
        liquidity_data = get_current_liquidity_distribution(pool, price_bounds_multiplier=2.0, base_token1=base_token1)
    else:
        liquidity_data = get_liquidity_distribution(pool, from_date, to_date, step, progress_bar=True,
                                                    price_bounds_multiplier=2.0, base_token1=base_token1)

    if base_token1:
        x = 'price1'
        y = 'liquidityAdj1'
    else:
        x = 'price0'
        y = 'liquidityAdj0'

    fig = px.bar(liquidity_data, x=x, y=y, animation_frame="readable_date", color='label')
    fig["layout"].pop("updatemenus")
    fig.show()
