from matplotlib import pyplot as plt
from matplotlib.widgets import Slider

from data import get_liquidity_distribution_data
from datetime import datetime

if __name__ == "__main__":
    #   Get pool info
    pool_address = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
    from_date = datetime(year=2022, month=6, day=1)
    to_date = datetime(year=2022, month=6, day=20)
    num_surrounding_ticks = 100

    liquidity_data = get_liquidity_distribution_data(pool_address, from_date, to_date, num_surrounding_ticks)

    # plotting
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)
    ax.set_xlim(xmin=liquidity_data[0]['current_price'] - 500,
                xmax=liquidity_data[0]['current_price'] + 500)
    liquidity_plot, = plt.plot(liquidity_data[0]['price_list'], liquidity_data[0]['liquidity_list'])
    price_line = plt.axvline(x=liquidity_data[0]['current_price'], color='b')

    ax_date = plt.axes([0.25, 0.15, 0.65, 0.03])

    # create the sliders
    slider_date = Slider(
        ax_date, "Date", 0, len(liquidity_data) - 1,
        valinit=0, valstep=1,
        color="green"
    )


    def update(date_index):
        liquidity_plot.set_xdata(liquidity_data[date_index]['price_list'])
        liquidity_plot.set_ydata(liquidity_data[date_index]['liquidity_list'])
        price_line.set_xdata(liquidity_data[date_index]['current_price'])
        ax.set_xlim(xmin=liquidity_data[date_index]['current_price'] - 500, xmax= liquidity_data[date_index]['current_price'] + 500)
        fig.canvas.draw_idle()


    slider_date.on_changed(update)
    plt.show()
