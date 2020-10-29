import os
import argparse
import itertools

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ast import literal_eval


def plot_list_ops(basedir, board):
    data = {"timer_count": [], "duration": [], "board": [], "timer_version": []}
    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        inputfile = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        test = ET.parse(inputfile).find(f".//testcase[@name='Measure Add Timers']")
        if test is None:
            raise RuntimeError("test case not found")

        for prop in test.findall("./properties/property"):
            name = prop.get("name").split("-")
            count = name[0]
            # convert to milliseconds
            trace = [v * 1000 for v in literal_eval(prop.get("value"))]

            data["board"].extend([board] * len(trace))
            data["timer_version"].extend([version] * len(trace))
            data["timer_count"].extend([count] * len(trace))
            data["duration"].extend(trace)

    df = pd.DataFrame(data)
    df["timer_count"] = pd.to_numeric(df["timer_count"])
    return df


outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
boards = os.listdir(basedir)

df = plot_list_ops(basedir, boards)

fig = px.line(
    df,
    x="timer_count",
    y="duration",
    color="board",
    facet_col="timer_version",
    labels={"board": "Board"},
)


fig.update_layout(
    yaxis_title="Duration [ms]",
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99,
    ),
)
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

fig.update_xaxes(title_text="Nr. of Timers", row=1, col=1)
fig.update_xaxes(title_text="Nr. of Timers", row=1, col=2)

# fig.write_html("/tmp/list_operations_combined.html", include_plotlyjs="cdn")
fig.write_image(f"{outdir}/list_operations_combined.pdf")
