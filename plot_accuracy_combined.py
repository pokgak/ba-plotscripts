import os
import argparse
import itertools

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ast import literal_eval

outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
boards = os.listdir(basedir)


def plot_accuracies(basedir, boards):
    data = {
        "function": [],
        "target_duration": [],
        "actual_duration": [],
        "timer_version": [],
        "board": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        inputfile = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        for prop in ET.parse(inputfile).findall(
            f"testcase[@classname='tests_{version}_benchmarks.Sleep Accuracy']//property"
        ):
            name = prop.get("name").lower().split("-")
            if "timer_sleep" in name:
                function = "timer_sleep"
            elif "timer_set" in name:
                function = "timer_set"
            else:
                raise LookupError

            target = literal_eval(name[-2])

            # convert to us
            actual = [v * 1000000 for v in literal_eval(prop.get("value"))]

            data["actual_duration"].extend(actual)
            data["target_duration"].extend([target] * len(actual))
            data["function"].extend([function] * len(actual))
            data["timer_version"].extend([version] * len(actual))
            data["board"].extend([board] * len(actual))
    return pd.DataFrame(data)


df = plot_accuracies(basedir, boards)
df["diff_actual_target"] = df["actual_duration"] - df["target_duration"]
df = (
    df.groupby(["timer_version", "board", "function", "target_duration"])
    .mean()
    .reset_index()
)

for func in ["set", "sleep"]:
    tmp = df[df["function"] == f"timer_{func}"]
    fig = px.line(
        tmp,
        x="target_duration",
        y="diff_actual_target",
        color="timer_version",
        facet_col="board",
        facet_col_spacing=0.05,
        facet_col_wrap=4,
        line_dash="timer_version",
        line_dash_sequence=["solid", "dot"]
    )
    fig.for_each_annotation(
        lambda a: a.update(text=a.text.split("=")[-1], font_size=16)
    )
    # fig.update_layout(font_size=24)

    fig.update_yaxes(matches=None, showticklabels=True)
    # legend
    fig.update_layout(
        legend=dict(
            title="Timer Version",
            # orientation="h",
            x=0.9,
            y=1.3,
        )
    )
    # hide original title
    fig.update_yaxes(title_text="")
    fig.update_xaxes(title_text="")
    # manually use annotations to set axis title
    fig.add_annotation(
        text="Target Duration [us]",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.2,
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

    # for i in range(2):
    #     fig.update_yaxes(title_text="Difference Actual - Target Duration [s]", row=i, col=1)
    # for i in range(4):
    #     fig.update_xaxes(title_text)

    fig.write_image(f"{outdir}/accuracy_{func}_combined.pdf")
    print(f"{outdir}/accuracy_{func}_combined.pdf")
    fig.write_html(f"/tmp/accuracy_{func}_combined.html")
