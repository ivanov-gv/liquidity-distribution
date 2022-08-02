import plotly.express as px

from data import *
from datetime import datetime

if __name__ == "__main__":
    #   Get pool info
    pool_address = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
    from_date = datetime(year=2022, month=7, day=1)
    to_date = datetime(year=2022, month=7, day=29)
    num_surrounding_ticks = 200

    liquidity_data = get_liquidity_distribution_full(pool_address)

    # plotting
    fig = px.bar(liquidity_data, x="price0", y="liquidityAdj", animation_frame="readable_date",
                 color='equal_liquidity_price')
    fig["layout"].pop("updatemenus")
    fig.show()
