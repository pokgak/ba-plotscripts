# %%

from __future__ import print_function
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

outdir = "/home/pokgak/git/ba-plotscripts/docs/repeat_stats"
basedir = "/home/pokgak/git/ba-plotscripts/docs/repeat_stats/overhead"

repeats = os.listdir(basedir)
boards = [
    "nucleo-f767zi",
    "arduino-due",
]

# %% timer now distribution

data = {
    # "i": [],
    "duration": [],
    "timer_version": [],
    "board": [],
    "sample_size": [],
}


def timer_now_dist():
    for version, board, repeat in itertools.product(
        ["xtimer", "ztimer"], boards, repeats
    ):
        filename = f"{basedir}/{repeat}/{board}/tests_{version}_benchmarks/xunit.xml"
        root = ET.parse(filename)
        path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead'][@name='Measure Overhead TIMER_NOW']//property"
        for prop in root.iterfind(path):
            values = [v * 1000000 for v in literal_eval(prop.get("value"))]
            data["duration"].extend(values)
            # data["i"].extend(range(len(values)))
            data["timer_version"].extend([version] * len(values))
            data["board"].extend([board] * len(values))
            data["sample_size"].extend([int(repeat.split("x")[1]) * 50] * len(values))

    df = pd.DataFrame(data).sort_values("sample_size")

    df = df[df.timer_version == 'ztimer']

    fig = px.histogram(
        df,
        x="duration",
        nbins=100,
        histnorm="percent",
        facet_col="sample_size",
        facet_row="board",
        facet_row_spacing=0.1,
    )

    # fig.for_each_annotation(lambda a: a.update(font_size=18))
    fig.update_yaxes(col=1, title="Sample Percentage [%]")
    fig.update_xaxes(showticklabels=True, matches=None, tickangle=45, ticks="outside", title="")
    for row in range(len(boards)):
        rowmatch = f"x{'' if row == 0 else 1 + (row * 5)}"
        # print(row, rowmatch)
        fig.update_xaxes(row=row + 1, matches=rowmatch)
        # fig.update_yaxes(row=row + 1, matches=rowmatch)

    fig.write_html("/tmp/repeat_stats_timer_now.html", include_plotlyjs="cdn")
    fig.write_image("/tmp/repeat_stats_timer_now.pdf")
    fig.write_image(f"{outdir}/repeat_stats_timer_now.pdf")


# %% set remove distribution

# data = {
#         "method": [],
#         "duration": [],
#         "timer_count": [],
#         "timer_version": [],
#         "board": [],
#         "sample_size": [],
#     }

# for version, board, repeat in itertools.product(["xtimer", "ztimer"], boards, repeats):
#     filename = f"{basedir}/{repeat}/{board}/tests_{version}_benchmarks/xunit.xml"
#     root = ET.parse(filename)
#     path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead']//property"
#     properties = [
#         p
#         for p in root.findall(path)
#         if "set" in p.get("name") or "remove" in p.get("name")
#     ]
#     for prop in properties:
#         name = prop.get("name").split("-")

#         values = [v * 1000000 for v in literal_eval(prop.get("value"))]
#         data["duration"].extend(values)
#         data["timer_count"].extend([int(name[2])] * len(values))
#         data["method"].extend([name[3]] * len(values))
#         data["timer_version"].extend([version] * len(values))
#         data["board"].extend([board] * len(values))
#         data["sample_size"].extend([int(repeat.split("x")[1]) * 50] * len(values))


# df = pd.DataFrame(data).sort_values('sample_size')
# df = df[df['timer_count'] == 25]    # observe only 25 timer


# %%

if __name__ == "__main__":
    timer_now_dist()
    # set_remove_dist()
