import plotly.express as px
from data import get_liquidity_distribution
from datetime import datetime, timedelta

from graphql.pool import PoolInfo

if __name__ == "__main__":
    #   Get pool info
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    from_date = datetime(year=2021, month=6, day=1)
    to_date = datetime(year=2022, month=1, day=1)
    step = timedelta(days=7)

    pool = PoolInfo.get(pool_address)
    liquidity_data = get_liquidity_distribution(pool, from_date, to_date, step, progress_bar=True)

    # plotting
    fig = px.bar(liquidity_data, x="price0", y="liquidityAdj0", animation_frame="readable_date",
                 color='label')
    fig["layout"].pop("updatemenus")
    fig.show()
