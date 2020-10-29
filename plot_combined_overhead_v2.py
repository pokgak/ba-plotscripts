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
    bres = {"test": [], "time": [], "timer_version": [], "board": []}

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
        values = literal_eval(t.get("value"))
        bres["test"].extend([" ".join(name[2:])] * len(values))
        bres["time"].extend(values)
        bres["timer_version"].extend([timer_version] * len(values))
        bres["board"].extend([board] * len(values))

    return pd.DataFrame(bres)


boards = os.listdir(basedir)

df = pd.DataFrame(columns=["timer_version", "board", "test", "time"])

for version, board in itertools.product(["xtimer", "ztimer"], boards):
    df = df.append(get_overhead_df(version, board))
if df.empty:
    raise RuntimeError("Empty dataframe")

# use this to exclude any test
# df.drop(df[df["test"] == "gpio"].index, inplace=True)

# use this to focus on a test
# df = df[df['test'] == 'gpio']

fig = px.box(
    df,
    x="timer_version",
    y="time",
    # color="board",
    color="timer_version",
    facet_row="board",
    facet_col="test",
    facet_col_spacing=0.04,
)

fig.update_layout(showlegend=False)
# simplify column title
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

# update yaxis title
fig.update_yaxes(showticklabels=True, matches=None, title="")
fig.update_yaxes(title_text="Duration [s]", row=4, col=1)
# fig.update_yaxes(title_text="Duration [s]", row=2, col=1)
# hide xaxis labels
fig.update_xaxes(showticklabels=True, title="")
# fig.show()
# fig.write_image(f"{outdir}/{version}/overhead_combined.pdf")
# fig.write_html(f"/tmp/overhead_combined.html", include_plotlyjs="cdn")
fig.write_image(f"/{outdir}/overhead_combined.pdf", height=1240, width=1748)
