import plotly.express as px

from data import get_liquidity_distribution_data
from datetime import datetime

if __name__ == "__main__":
    #   Get pool info
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    from_date = datetime(year=2022, month=7, day=8)
    to_date = datetime(year=2022, month=7, day=19)
    num_surrounding_ticks = 200

    liquidity_data = get_liquidity_distribution_data(pool_address, from_date, to_date, num_surrounding_ticks)

    # plotting
    fig = px.bar(liquidity_data, x="price0", y="liquidity", animation_frame="readable_date", color="active_price")
    fig["layout"].pop("updatemenus")
    fig.show()
