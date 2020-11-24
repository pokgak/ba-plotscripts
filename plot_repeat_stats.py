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

outdir = "/home/pokgak/git/ba-plotscripts/docs/repeat_stats"
basedir = "/home/pokgak/git/ba-plotscripts/docs/repeat_stats"
boards = [
    "nucleo-f767zi",
    "arduino-due",
]

# %% timer now distribution


def timer_now_dist():
    data = {
        "duration": [],
        "timer_version": [],
        "board": [],
        "sample_size": [],
    }
    repeats = os.listdir(f"{basedir}/overhead")
    for version, board, repeat in itertools.product(
        ["xtimer", "ztimer"], boards, repeats
    ):
        filename = (
            f"{basedir}/overhead/{repeat}/{board}/tests_{version}_benchmarks/xunit.xml"
        )
        root = ET.parse(filename)
        path = f"testcase[@classname='tests_{version}_benchmarks.Timer Overhead'][@name='Measure Overhead TIMER_NOW']//property"
        for prop in root.iterfind(path):
            values = [v * 1000000 for v in literal_eval(prop.get("value"))]
            data["duration"].extend(values)
            data["timer_version"].extend([version] * len(values))
            data["board"].extend([board] * len(values))
            data["sample_size"].extend([int(repeat.split("x")[1]) * 50] * len(values))

    df = pd.DataFrame(data).sort_values("sample_size")

    df = df[df.timer_version == "ztimer"]

    fig = px.histogram(
        df,
        x="duration",
        # nbins=100,
        histnorm="percent",
        facet_col="sample_size",
        facet_row="board",
        facet_row_spacing=0.1,
        title="Timer Now sample distributions; on ztimer",
    )

    # fig.for_each_annotation(lambda a: a.update(font_size=18))
    fig.update_yaxes(col=1, title="Share [%]")
    fig.update_xaxes(
        showticklabels=True, matches=None, tickangle=45, ticks="outside", title=""
    )
    for row in range(len(boards)):
        rowmatch = f"x{'' if row == 0 else 1 + (row * 5)}"
        fig.update_xaxes(row=row + 1, matches=rowmatch)

    fig.add_annotation(
        text="Duration [us]",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.2,
        showarrow=False,
    )

    # fig.write_image("/tmp/repeat_stats_timer_now.pdf")
    fig.write_image(f"{outdir}/repeat_stats_timer_now.pdf")


# %% set remove distribution


def get_timer_set_remove_df():
    data = {
        "method": [],
        "duration": [],
        "timer_count": [],
        "timer_version": [],
        "board": [],
        "sample_size": [],
    }

    repeats = os.listdir(f"{basedir}/overhead")
    for version, board, repeat in itertools.product(["ztimer"], boards, repeats):
        filename = (
            f"{basedir}/overhead/{repeat}/{board}/tests_{version}_benchmarks/xunit.xml"
        )
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
            data["duration"].extend(values)
            data["timer_count"].extend([int(name[2])] * len(values))
            data["method"].extend([name[3]] * len(values))
            data["timer_version"].extend([version] * len(values))
            data["board"].extend([board] * len(values))
            data["sample_size"].extend([int(repeat.split("x")[1]) * 50] * len(values))

    return pd.DataFrame(data).sort_values("sample_size")


def set_remove_dist():
    df = get_timer_set_remove_df()
    df = df[df["timer_count"] == 25]  # observe only 25 timer
    df = df[df.timer_version == "ztimer"]
    for method in ["set", "remove"]:
        tmp = df[df.method == method]

        fig = px.histogram(
            tmp,
            x="duration",
            nbins=250,
            histnorm="percent",
            facet_col="sample_size",
            facet_row="board",
            facet_row_spacing=0.1,
            title=f"Timer {method} sample distributions; 25 timers on ztimer",
        )

        fig.update_yaxes(col=1, title="Share [%]")
        fig.update_xaxes(
            showticklabels=True, matches=None, tickangle=45, ticks="outside", title=""
        )
        for row in range(len(boards)):
            rowmatch = f"x{'' if row == 0 else 1 + (row * 5)}"
            fig.update_xaxes(row=row + 1, matches=rowmatch)

        fig.add_annotation(
            text="Duration [us]",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.2,
            showarrow=False,
        )

        # fig.write_image(f"/tmp/repeat_stats_timer_{method}.pdf")
        fig.write_image(f"{outdir}/repeat_stats_timer_{method}.pdf")


# %% Jitter distribution


def jitter_dist():
    data = {
        "i": [],
        "wakeup_time": [],
        "timer_count": [],
        "board": [],
        "sample_size": [],
        "start_time": [],
        "timer_interval": [],
    }

    repeats = os.listdir(f"{basedir}/jitter")
    for board, repeat in itertools.product(boards, repeats):
        filename = (
            f"{basedir}/jitter/{repeat}/{board}/tests_ztimer_benchmarks/xunit.xml"
        )
        root = ET.parse(filename)
        path = "testcase[@classname='tests_ztimer_benchmarks.Sleep Jitter']//property"
        properties = root.findall(path)

        start_times = [
            prop for prop in properties if prop.get("name").endswith("start-time") and "hil" in prop.get("name")
        ]
        wakeup_times = [
            prop for prop in properties if prop.get("name").endswith("wakeup-time") and "hil" in prop.get("name")
        ]

        for start, wakeup in zip(start_times, wakeup_times):
            w = [v * 1000000 for v in literal_eval(wakeup.get("value"))]
            data["i"].extend(range(len(w)))
            data["start_time"].extend([literal_eval(start.get("value")) * 1000000] * len(w))
            data["wakeup_time"].extend(w)
            data["board"].extend([board] * len(w))
            data["sample_size"].extend([int(repeat.split("x")[1]) * 100] * len(w))
            data["timer_interval"].extend([10000] * len(w))
            data["timer_count"].extend(
                [int(wakeup.get("name").split("-")[1])] * len(w)
            )

    df = pd.DataFrame(data).sort_values("sample_size")

    df["calculated_target"] = df["start_time"] + (df["i"] + 1) * df["timer_interval"]
    df["diff_target_from_start"] = df["calculated_target"] - df["start_time"]
    df["diff_wakeup_from_start"] = df["wakeup_time"] - df["start_time"]
    df["diff_wakeup_from_target"] = df["wakeup_time"] - df["calculated_target"]

    df = df[df.timer_count == 10]

    fig = px.histogram(
        df,
        x="diff_wakeup_from_target",
        # nbins=2000,
        histnorm="percent",
        facet_col="sample_size",
        facet_row="board",
        facet_row_spacing=0.1,
        title=f"Jitter sample distributions with 10 timers on ztimer",
    )

    fig.update_yaxes(col=1, title="Share [%]")
    fig.update_xaxes(
        showticklabels=True, matches=None, tickangle=45, ticks="outside", title=""
    )
    for row in range(len(boards)):
        rowmatch = f"x{'' if row == 0 else 1 + (row * len(repeats))}"
        fig.update_xaxes(row=row + 1, matches=rowmatch)

        rowmatch = f"y{'' if row == 0 else 1 + (row * len(repeats))}"
        fig.update_yaxes(row=row + 1, matches=rowmatch)

    fig.add_annotation(
        text="Difference from target wakeup time [us]",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.2,
        showarrow=False,
    )

    fig.write_image(f"{outdir}/repeat_stats_jitter.pdf")
    fig.write_html(f"/tmp/repeat_stats_jitter.html", include_plotlyjs="cdn")


def accuracy_dist():
    data = {
        "duration": [],
        "target_duration": [],
        "method": [],
        "board": [],
        "sample_size": [],
    }

    repeats = os.listdir(f"{basedir}/accuracy")
    for board, repeat in itertools.product(boards, repeats):
        filename = (
            f"{basedir}/accuracy/{repeat}/{board}/tests_ztimer_benchmarks/xunit.xml"
        )
        root = ET.parse(filename)
        path = "testcase[@classname='tests_ztimer_benchmarks.Sleep Accuracy']//property"
        for prop in root.iterfind(path):
            name = prop.get("name").split("-")
            values = [v * 1000000 for v in literal_eval(prop.get("value"))]
            data["duration"].extend(values)
            data["target_duration"].extend([int(name[2])] * len(values))
            data["board"].extend([board] * len(values))
            data["sample_size"].extend([int(repeat.split("x")[1]) * 50] * len(values))
            data["method"].extend([name[1]] * len(values))

    df = pd.DataFrame(data).sort_values("sample_size")
    df = df[df.target_duration == 100]

    for method in ["TIMER_SET", "TIMER_SLEEP"]:
        tmp = df[df.method == method]

        fig = px.histogram(
            tmp,
            x="duration",
            histnorm="percent",
            facet_col="sample_size",
            facet_row="board",
            facet_row_spacing=0.1,
            title=f"Accuracy {method} sample distributions for target duration 100 us on ztimer",
        )

        fig.update_yaxes(col=1, title="Share [%]")
        fig.update_xaxes(
            showticklabels=True, matches=None, tickangle=45, ticks="outside", title=""
        )
        for row in range(len(boards)):
            rowmatch = f"x{'' if row == 0 else 1 + (row * len(repeats))}"
            fig.update_xaxes(row=row + 1, matches=rowmatch)

            rowmatch = f"y{'' if row == 0 else 1 + (row * len(repeats))}"
            fig.update_yaxes(row=row + 1, matches=rowmatch)

        fig.add_annotation(
            text="Difference from target sleep duration [us]",
            xref="paper",
            yref="paper",
            x=0.5,
            y=-0.2,
            showarrow=False,
        )

        fig.write_image(f"{outdir}/repeat_stats_accuracy_{method}.pdf")


if __name__ == "__main__":
    timer_now_dist()
    # set_remove_dist()
    # accuracy_dist()
    # jitter_dist()
