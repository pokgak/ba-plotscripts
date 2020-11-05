# %%
import os
import re
import argparse
import itertools
from typing import Pattern

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ast import literal_eval

# %%

# outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
# basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
basedir = "/home/pokgak/git/RobotFW-tests/build/robot"
# basedir = "/home/pokgak/git/ba-plotscripts/docs/jitter/norepeat1warmup"

boards = os.listdir(basedir)


def get_value(property):
    return literal_eval(property.get("value"))


def get_result_type(property):
    return property.get("name").split("-")[0]


def get_timer_count(property):
    return property.get("name").split("-")[1]


def parse_result(basedir, boards):
    data = {
        "timer_count": [],
        "timer_interval": [],
        "i": [],
        "start_time": [],
        "wakeup_time": [],
        "result_type": [],
        "timer_version": [],
        "board": [],
    }

    entries = list()
    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        inputfile = "{:s}/{:s}/tests_{:s}_benchmarks/xunit.xml".format(
            basedir, board, version
        )

        testcase = ET.parse(inputfile).find(
            "testcase[@classname='tests_{:s}_benchmarks.Sleep Jitter']".format(version)
        )

        if testcase is None:
            continue

        timer_interval = testcase.find(".//property[@name='timer-interval']")
        if timer_interval is None:
            raise RuntimeError("timer_interval not found")

        start_times = [
            prop
            for prop in testcase.findall(".//property")
            if prop.get("name").endswith("start-time")
        ]
        wakeup_times = [
            prop
            for prop in testcase.findall(".//property")
            if prop.get("name").endswith("wakeup-time")
        ]

        for start, wakeup in zip(start_times, wakeup_times):
            if get_result_type(start) != get_result_type(wakeup):
                raise RuntimeError("Result type does not match")

            result_type = get_result_type(start)
            timer_count = get_timer_count(start)
            w = get_value(wakeup)
            w = w if result_type == "dut" else [t * 1000000 for t in w]
            data["i"].extend(range(len(w)))
            data["wakeup_time"].extend(w)
            data["start_time"].extend([get_value(start)] * len(w))
            data["result_type"].extend([result_type] * len(w))
            data["timer_count"].extend([timer_count] * len(w))

        data["timer_interval"] = [get_value(timer_interval)] * len(data["wakeup_time"])
        data["timer_version"] = [version] * len(data["wakeup_time"])
        data["board"] = [board] * len(data["wakeup_time"])

    for k, v in data.items():
        print(k, len(v))
    return pd.DataFrame(data)


df = parse_result(basedir, boards)

df["diff_from_start"] = df["wakeup_time"] - df["start_time"]
df["diff_from_target"] = df["diff_from_start"] % df["timer_interval"]

# %%
fig = px.box(
    df,
    x="timer_count",
    y="diff_from_target",
    color="timer_version",
    hover_data=["i", "diff_from_target", "diff_from_start"],
    # facet_col="timer_count",
    facet_row="result_type",
    points="all",
)

fig.update_yaxes(matches=None, showticklabels=True, title="Difference from target [us]")
fig.update_layout(
    legend_title="Timer Version",
)

fig

# %%

# the earlier sample points might be too small to trigger
# df.drop(df[(df["i"] == 0)].index, inplace=True)

fig = px.box(
    df,
    x="bg_timer_count",
    y="diff_actual_target_duration",
    color="timer_version",
    facet_col="board",
    facet_col_wrap=2,
    facet_col_spacing=0.06,
    points="all",
    hover_data=["i"],
)

fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font_size=16))
fig.update_yaxes(matches=None, showticklabels=True)
fig.update_xaxes(tick0=0, dtick=5, showticklabels=True)

# legend
fig.update_layout(
    legend=dict(
        title="Timer Version",
        orientation="h",
        x=0,
        y=1.1,
    )
)
# hide original title
fig.update_yaxes(title_text="")
fig.update_xaxes(title_text="")
# manually use annotations to set axis title
fig.add_annotation(
    text="Nr. of Background Timer",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.1,
    showarrow=False,
)
fig.add_annotation(
    text="Difference Actual-Target Duration [us]",
    textangle=270,
    xref="paper",
    yref="paper",
    x=-0.1,
    y=0.5,
    showarrow=False,
)

fig.write_html("/tmp/jitter_combined.html", include_plotlyjs="cdn")
# fig.write_image(f"{outdir}/jitter_combined.pdf", height=900, width=900)
# print(f"{outdir}/jitter_combined.pdf")
