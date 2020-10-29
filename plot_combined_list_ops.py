import os
import argparse
import itertools

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import pandas as pd

from ast import literal_eval


def plot_list_ops(basedir, board, version):
    inputfile = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
    data = {"timer_count": [], "duration": []}
    test = ET.parse(inputfile).find(f".//testcase[@name='Measure Add Timers']")
    if test is None:
        raise RuntimeError("test case not found")

    for prop in test.findall("./properties/property"):
        name = prop.get("name").split("-")
        count = name[0]
        trace = literal_eval(prop.get("value"))

        data["timer_count"].extend([count] * len(trace))
        data["duration"].extend(trace)

    df = pd.DataFrame(data)

    return go.Box(x=df["timer_count"], y=df["duration"], name=board)


basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
boards = os.listdir(basedir)
timer_versions = ["xtimer", "ztimer"]

traces = [
    plot_list_ops(basedir, board, version)
    for version, board in itertools.product(timer_versions, boards)
]
fig = go.Figure(traces)
fig.update_layout(
    yaxis_title="Duration [s]",
    xaxis_title="Nr. of Timers",
)
fig.show()


# fig.update_layout(
#     title="Setting N Timers: {:s} with {:s}".format(self.board, self.timer_version),
#     yaxis_title="Duration [s]",
#     xaxis_title="Nr. of Timers",
# )
# fig.write_image(
#     "{}/{}_{}.pdf".format(self.outdir, self.board, filename),
# )
