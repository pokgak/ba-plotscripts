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
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"

# basedir = "/home/pokgak/git/RobotFW-tests/build/robot"
boards = os.listdir(basedir)


def get_overhead_df(timer_version, board):
    bres = {
        "i": [],
        "method": [],
        "duration": [],
        "timer_count": [],
        "timer_version": [],
        "board": [],
    }

    filename = f"{basedir}/{board}/tests_{timer_version}_benchmarks/xunit.xml"
    root = ET.parse(filename)
    path = f"testcase[@classname='tests_{timer_version}_benchmarks.Timer Overhead']//property"
    properties = [p for p in root.findall(path) if "overhead-list" in p.get("name")]
    for prop in properties:
        name = prop.get("name").split("-")

        values = [v * 1000000 for v in literal_eval(prop.get("value"))]
        bres["i"].extend(range(len(values)))
        bres["duration"].extend(values)
        bres["timer_count"].extend([int(name[3])] * len(values))
        bres["method"].extend([name[4]] * len(values))
        bres["timer_version"].extend([timer_version] * len(values))
        bres["board"].extend([board] * len(values))

    return pd.DataFrame(bres)


df = pd.DataFrame()
for version, board in itertools.product(["xtimer", "ztimer"], boards):
    df = df.append(get_overhead_df(version, board))

df = (
    df.groupby(["timer_version", "method", "board", "timer_count"]).mean().reset_index()
)

fig = px.line(
    df,
    x="timer_count",
    y="duration",
    color="board",
    facet_col="timer_version",
    facet_col_spacing=0.06,
    facet_row="method",
    line_dash="board",
)

# match axis by row
fig.update_yaxes(showticklabels=True, matches=None)
fig.update_yaxes(row=1, matches="y11")
fig.update_yaxes(row=2, matches="y21")

fig.update_layout(legend=dict(title="Board", title_font_size=14))
fig.for_each_annotation(lambda a: a.update(font_size=22))
fig.update_yaxes(col=1, title_text="Duration [us]")
fig.update_xaxes(row=1, title_text="Timer Count")


fig.write_html("/tmp/overhead.html")
fig.write_image("/tmp/overhead.pdf", height=1600, width=1200)
