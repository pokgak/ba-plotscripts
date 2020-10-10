#!/usr/bin/env python3

import os
import argparse
import warnings
from ast import literal_eval

import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class FigurePlotter:
    def __init__(self, boards, **kwargs):
        self.outdir = kwargs["outdir"]
        self.datadir = kwargs["datadir"]
        self.timer = kwargs["timer"]
        self.save_svg = True
        self.boards = boards

    def get_drift_df(self, board):
        root = ET.parse(
            f"{self.datadir}/{board}/tests_{self.timer}_benchmarks/xunit.xml"
        ).getroot()

        dss = list()
        for testcase in root.findall(
            f"testcase[@classname='tests_{self.timer}_benchmarks.Drift']"
        ):

            for prop in testcase.findall(".//property"):
                # name formatted as 'name'-'unit', we ditch the unit
                name = prop.get("name").split("-")

                # values are recorded as string, convert to float
                value = literal_eval(prop.get("value"))
                # make sure value not in array
                if len(value) == 1:
                    value = value[0]

                value_source = "dut" if "dut" in name else "philip"

                key = int(name[2]) / 1_000_000

                # create a new row or update if already existed
                try:
                    row = next(e for e in dss if e["time"] == key)
                    row.update({"time": key, value_source: value})
                except StopIteration:
                    row = {"time": key, value_source: value}
                    dss.append(row)

        df = pd.DataFrame(dss, dtype="float64")
        # combine dut, philip rows with same (time, repeat) to remove NaN values
        df["diff_philip_target"] = df["philip"] - df["time"]
        df["diff_philip_target_percentage"] = df["diff_philip_target"] / df["time"]
        df["philip_target_percentage"] = df["philip"] / df["time"] * 100
        return df

    def get_skew_trace(self, board):
        df = self.get_drift_df(board)
        if df.empty:
            return

        # box = go.Box(
        #     x=df["time"],
        #     y=df["diff_philip_target"],
        #     legendgroup=board,
        #     showlegend=False,
        # )
        line = go.Scatter(
            x=df["time"].unique(),
            y=df.groupby("time")["diff_philip_target"].mean(),
            name=board,
            legendgroup=board,
        )

        return [
            # box,
            line
        ]

    def get_percentage_trace(self, board):
        df = self.get_drift_df(board)
        if df.empty:
            return

        return go.Box(x=df["time"], y=df["philip_target_percentage"], name=board)


def plot_skew_diff(plotter):
    traces = []
    for b in plotter.boards:
        traces.extend(plotter.get_skew_trace(b))

    fig = go.Figure()
    fig.add_traces(traces)
    fig.update_layout(
        title="Clock Skew on boards",
        title_xanchor="center",
        title_x=0.5,
        xaxis_title="Sleep Duration [s]",
        # yaxis_title="Difference real - target duration [s]",
        legend_title_text="Board",
    )

    fig.write_image(f"{args.outdir}/{args.timer}_drift.pdf")
    # fig.write_html(f"{args.outdir}/{args.timer}_drift.html", include_plotlyjs="cdn")


def plot_drift_percentage(plotter):
    traces = []
    for b in plotter.boards:
        traces.append(plotter.get_percentage_trace(b))

    fig = go.Figure()
    fig.add_traces(traces)
    fig.update_layout(
        title="Drift Percentage between Boards",
        xaxis_title="Sleep Duration [s]",
        yaxis_title="Percentage real/target [%]",
        legend_title_text="Board",
    )

    fig.write_image(f"{args.outdir}/{args.timer}_percentage.pdf")
    # fig.write_html(f"{args.outdir}/{args.timer}_percentage.html", include_plotlyjs="cdn")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Produce timer benchmarks plots from xunit results"
    )

    parser.add_argument(
        "--datadir",
        help="directory where data is",
        default="docs/drift/data",
    )
    parser.add_argument(
        "--outdir", help="output directory", default="docs/drift/result"
    )
    parser.add_argument("--timer", help="type of timer", choices=["xtimer", "ztimer"])
    parser.add_argument(
        "--exclude-board",
        metavar="BOARD",
        nargs="+",
        help="list of boards to exclude from result, separated by space",
        default="",
    )

    args = parser.parse_args()

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    boards = [b for b in os.listdir(args.datadir) if b not in args.exclude_board]

    plotter = FigurePlotter(boards, **vars(args))
    plot_skew_diff(plotter)
    # plot_drift_percentage(plotter)
