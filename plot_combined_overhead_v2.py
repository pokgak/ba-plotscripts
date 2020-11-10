import os
import argparse
import itertools

import pandas as pd
import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px

from ast import literal_eval

outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"


def get_overhead_df(timer_version, board):
    bres = {"test": [], "time": [], "timer_version": [], "board": [], "i": []}

    filename = f"{basedir}/{board}/tests_{timer_version}_benchmarks/xunit.xml"

    tests = [
        t
        for t in ET.parse(filename).findall(
            f"testcase[@classname='tests_{timer_version}_benchmarks.Timer Overhead']//property"
        )
        if "overhead" in t.get("name")
    ]
    for t in tests:
        name = t.get("name").split("-")
        values = [v * 1000000 for v in literal_eval(t.get("value"))]
        bres["test"].extend([" ".join(name[2:])] * len(values))
        bres["time"].extend(values)
        bres["i"].extend(range(len(values)))
        bres["timer_version"].extend([timer_version] * len(values))
        bres["board"].extend([board] * len(values))

    return pd.DataFrame(bres)


boards = os.listdir(basedir)

df = pd.DataFrame(columns=["timer_version", "board", "test", "time", "i"])

for version, board in itertools.product(["xtimer", "ztimer"], boards):
    df = df.append(get_overhead_df(version, board))
if df.empty:
    raise RuntimeError("Empty dataframe")

df.drop(df[(df["i"] <= 5)].index, inplace=True)

# separate figure to separate groups
groups = [
    ["gpio", "timer now"],
    ["set first timer", "set middle timer", "set last timer"],
    ["remove first timer", "remove middle timer", "remove last timer"],
]

for i, group in enumerate(groups):
    # fetch only test in group
    tmp = df[[b for b in df.test.isin(group)]]

    fig = px.box(
        tmp,
        x="timer_version",
        y="time",
        # color="board",
        color="timer_version",
        facet_row="board",
        facet_col="test",
        facet_col_spacing=0.06,
        hover_data=["i"],
        # points="all",
    )

    fig.update_layout(showlegend=False, font_size=16)
    # simplify column title
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font_size=22))

    # update yaxis title
    fig.update_yaxes(showticklabels=True, matches=None, title="")
    fig.add_annotation(
        text="Duration [us]",
        textangle=270,
        xref="paper",
        x=-0.09,
        yref="paper",
        y=0.5,
        showarrow=False,
    )

    # hide xaxis labels
    fig.update_xaxes(showticklabels=True, title="")

    # print(f"{outdir}/overhead_combined_{i}.pdf")
    fig.write_html(f"/tmp/overhead_combined_{i}.html", include_plotlyjs="cdn")
    fig.write_image(f"{outdir}/overhead_combined_{i}.pdf", height=1600, width=1200)
