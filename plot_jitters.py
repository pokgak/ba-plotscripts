#!/usr/bin/env python3

import os
import argparse
import warnings
from ast import literal_eval

import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_df(board):
    root = ET.parse(
        "docs/jitter/data/{}/tests_ztimer_benchmarks/xunit.xml".format(board)
    )

    df = {"timer_count": [], "sleep_duration": []}
    for testcase in root.findall(
        f"testcase[@classname='tests_ztimer_benchmarks.Sleep Jitter']"
    ):
        timer_count = len(
            literal_eval(
                testcase.find("properties/property[@name='intervals']").get("value")
            )
        )
        traces = literal_eval(
            testcase.find("properties/property[@name='trace']").get("value")
        )

        df["sleep_duration"].extend(traces)
        df["timer_count"].extend([int(timer_count)] * len(traces))

    df["board"] = [board] * len(df["sleep_duration"])

    df = pd.DataFrame(df)
    if df.empty:
        return

    return df


def plot(df):
    df["sleep_duration_target_diff"] = df["sleep_duration"] - (
        [0.1] * len(df["sleep_duration"])
    )

    fig = px.violin(
        df,
        x="timer_count",
        y="sleep_duration_target_diff",
        color="timer_count",
        # points="all",
        facet_row="board",
    )

    fig.update_yaxes(matches=None, showticklabels=True, title="")

    fig.update_layout(
        # title="Jitter of periodic 100ms sleep with increasing nr. of background timer",
        xaxis_title="Nr. of background timers",
        legend_orientation="h",
    )

    fig.write_html(
        "docs/jitter/jitter.html",
        full_html=True,
        include_plotlyjs="cdn",
    )


if __name__ == "__main__":

    boards = os.listdir("docs/jitter/data")

    df = pd.DataFrame()
    for b in boards:
        df = df.append(get_df(b), ignore_index=True)

    plot(df)
