# %%

from itertools import repeat
import os
import argparse
import itertools

import pandas as pd
import xml.etree.ElementTree as ET
from pandas.core.arrays.categorical import contains
import plotly.graph_objects as go
import plotly.express as px

from ast import literal_eval

# outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/repeat_stats/overhead"

# basedir = "/home/pokgak/git/RobotFW-tests/build/robot"
repeats = os.listdir(basedir)
boards = ['nucleo-f767zi']

data = {
    "i": [],
    "duration": [],
    "timer_version": [],
    "board": [],
    "sample_size": [],
}

for version, board, repeat in itertools.product(["xtimer", "ztimer"], boards, repeats):
    filename = f"{basedir}/{repeat}/{board}/tests_{version}_benchmarks/xunit.xml"
    root = ET.parse(filename)
    path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead'][@name='Measure Overhead TIMER_NOW']//property"
    for prop in root.iterfind(path):
        values = [v * 1000000 for v in literal_eval(prop.get("value"))]
        data["duration"].extend(values)
        data["i"].extend(range(len(values)))
        data["timer_version"].extend([version] * len(values))
        data["board"].extend([board] * len(values))
        data["sample_size"].extend([int(repeat.split('x')[1]) * 50] * len(values))

df = pd.DataFrame(data).sort_values('sample_size')

fig = px.histogram(df, x='duration', color='sample_size', barmode='overlay', facet_row='sample_size')
fig.update_yaxes(matches=None, title="Sample Count")
fig.update_xaxes(showticklabels=True, title="Timer NOW Overhead [us]")
fig.for_each_annotation(lambda a: a.update(font_size=22))

fig.write_html('/tmp/repeat_stats_timer_now.html')

# df = df.groupby(['timer_version', 'sample_size'])
# df = df.groupby(["timer_version", "board"]).describe()["duration"].reset_index()

# %%

    fig = px.bar(
        df,
        x="board",
        # y=["min", "mean", "max"],
        y="duration",
        barmode="group",
        color="timer_version",
        # facet_col="board"
    )
    fig.update_layout(
        xaxis_title="Board",
        legend=dict(title="Timer Version"),
    )
    fig.update_yaxes(matches=None, showticklabels=True, title="Duration [us]")
    fig.write_image(f"{outdir}/overhead_timer_now_combined.pdf")

    fig.write_html("/tmp/overhead_timer_now.html")
    fig.write_image("/tmp/overhead_timer_now.pdf")


if __name__ == "__main__":
    plot_timer_now()
    plot_set_remove()
