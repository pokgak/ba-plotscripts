import os
import argparse
import itertools

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import pandas as pd

from ast import literal_eval


def plot_list_ops(basedir, board):
    df = {}
    for version in ["xtimer", "ztimer"]:
        inputfile = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        data = {"timer_count": [], "duration": []}
        test = ET.parse(inputfile).find(f".//testcase[@name='Measure Add Timers']")
        if test is None:
            raise RuntimeError("test case not found")

        for prop in test.findall("./properties/property"):
            name = prop.get("name").split("-")
            count = name[0]
            # convert to milliseconds
            trace = [v * 1000 for v in literal_eval(prop.get("value"))]

            data["timer_count"].extend([count] * len(trace))
            data["duration"].extend(trace)

        tmp = pd.DataFrame(data)
        tmp['timer_count'] = pd.to_numeric(tmp['timer_count'])
        tmp = tmp.groupby('timer_count').mean().reset_index()
        df[version] = tmp

    return {
        "xtimer": go.Scatter(
            x=df["xtimer"]["timer_count"], y=df["xtimer"]["duration"], name=board, mode="lines",
        ),
        "ztimer": go.Scatter(
            x=df["ztimer"]["timer_count"], y=df["ztimer"]["duration"], name=board, mode="lines",
        ),
    }


outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
boards = os.listdir(basedir)

traces = [plot_list_ops(basedir, board) for board in boards]

for version in ["xtimer", "ztimer"]:
    vtraces = [t[version] for t in traces]
    fig = go.Figure(vtraces)
    fig.update_layout(
        title=f"List Operations Comparison with {version}",
        yaxis_title="Duration [ms]",
        xaxis_title="Nr. of Timers",
        # yaxis_range=[0, 5],
    )
    # fig.show()
    fig.write_image(f"{outdir}/{version}/list_operations_combined.pdf")
