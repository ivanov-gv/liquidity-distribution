import plotly.express as px
from datetime import datetime, timedelta
from console_progressbar import ProgressBar

from data import *

if __name__ == "__main__":
    #   Get pool info
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    from_date = datetime(year=2021, month=6, day=1)
    to_date = datetime(year=2022, month=1, day=1)
    step = timedelta(days=7)

    pb = ProgressBar(total=to_date.timestamp() - from_date.timestamp(), prefix='loading liquidity data', length=50)

    date = from_date
    liquidity_data = pd.DataFrame()
    while date <= to_date:
        pb.print_progress_bar(date.timestamp() - from_date.timestamp())
        data = get_liquidity_distribution_full_2(pool_address, date)
        mark_half_liquidity_price(data)
        liquidity_data = pd.concat((liquidity_data, data))
        date = date + step

    # plotting
    fig = px.bar(liquidity_data, x="price0", y="liquidityAdj0", animation_frame="readable_date",
                 color='label')
    fig["layout"].pop("updatemenus")
    fig.show()
