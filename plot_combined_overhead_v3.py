import os
import argparse
import itertools

import pandas as pd
import xml.etree.ElementTree as ET
from pandas.core.arrays.categorical import contains
import plotly.graph_objects as go
import plotly.express as px

from ast import literal_eval

outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
# basedir = "/home/pokgak/git/RobotFW-tests/build/robot"

boards = os.listdir(basedir)


def plot_set_remove():
    bres = {
        "i": [],
        "method": [],
        "duration": [],
        "timer_count": [],
        "timer_version": [],
        "board": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        filename = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        root = ET.parse(filename)
        path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead']//property"
        properties = [
            p
            for p in root.findall(path)
            if "set" in p.get("name") or "remove" in p.get("name")
        ]
        for prop in properties:
            name = prop.get("name").split("-")

            values = [v * 1000000 for v in literal_eval(prop.get("value"))]
            bres["i"].extend(range(len(values)))
            bres["duration"].extend(values)
            bres["timer_count"].extend([int(name[2])] * len(values))
            bres["method"].extend([name[3]] * len(values))
            bres["timer_version"].extend([version] * len(values))
            bres["board"].extend([board] * len(values))

    df = (
        pd.DataFrame(bres)
        .groupby(["timer_version", "method", "board", "timer_count"])
        .mean()
        .reset_index()
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

    fig.update_layout(legend_title="Board")
    # fig.for_each_annotation(lambda a: a.update(font_size=22))
    fig.update_yaxes(col=1, title_text="Duration [us]")
    fig.update_xaxes(row=1, title_text="Timer Count")

    fig.write_image(f"{outdir}/overhead_set_remove_combined.pdf")

    fig.write_html("/tmp/overhead.html")
    fig.write_image("/tmp/overhead.pdf")


def plot_timer_now():
    data = {
        "i": [],
        "duration": [],
        "timer_version": [],
        "board": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        filename = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        root = ET.parse(filename)
        path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead'][@name='Measure Overhead TIMER_NOW']//property"
        for prop in root.iterfind(path):
            values = [v * 1000000 for v in literal_eval(prop.get("value"))]
            data["duration"].extend(values)
            data["i"].extend(range(len(values)))
            data["timer_version"].extend([version] * len(values))
            data["board"].extend([board] * len(values))

    df = pd.DataFrame(data)
    df.drop(df[(df["i"] == 0)].index, inplace=True)
    df = (
        df.groupby(["timer_version", "board"])
        .describe(percentiles=[0.5, 0.90])["duration"]
        .reset_index()
    )

    fig = px.bar(
        df,
        x="board",
        y="mean",
        color="timer_version",
        text=df["mean"].round(3),
        barmode="group",
    )

    fig.update_layout(
        xaxis_title="Board",
        legend_title="Timer Version",
    )
    fig.update_yaxes(matches=None, showticklabels=True, title="Duration [us]")
    fig.write_image(f"{outdir}/overhead_timer_now_combined.pdf")


def plot_gpio():
    data = {
        "i": [],
        "duration": [],
        "timer_version": [],
        "board": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        filename = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        root = ET.parse(filename)
        path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead'][@name='Measure GPIO']//property"
        for prop in root.iterfind(path):
            values = [v * 1000000 for v in literal_eval(prop.get("value"))]
            data["duration"].extend(values)
            data["i"].extend(range(len(values)))
            data["timer_version"].extend([version] * len(values))
            data["board"].extend([board] * len(values))

    df = pd.DataFrame(data)
    df.drop(df[(df["i"] == 0)].index, inplace=True)
    df = (
        df.groupby(["timer_version", "board"])
        .describe(percentiles=[0.5, 0.90])["duration"]
        .reset_index()
    )

    fig = px.bar(
        df,
        y="board",
        x="mean",
        color="timer_version",
        text=df["mean"].round(3),
        barmode="group",
    )
    fig.update_layout(
        yaxis_title="Board",
        xaxis_title="Duration [us]",
        legend_title="Timer Version",
    )
    fig.write_image(f"{outdir}/overhead_gpio_combined.pdf")


if __name__ == "__main__":
    plot_gpio()
    plot_timer_now()
    plot_set_remove()
