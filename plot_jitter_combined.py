# %%
import os
import itertools

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ast import literal_eval

outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"

# basedir = "/home/pokgak/git/RobotFW-tests/build/robot"

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
        "timer_version": [],
        "board": [],
        "result_type": [],
        "wakeup_time": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        inputfile = "{:s}/{:s}/tests_{:s}_benchmarks/xunit.xml".format(
            basedir, board, version
        )

        if not os.path.isfile(inputfile):
            print(f"{inputfile} does not exists")

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

            if not all(
                e == get_result_type(start)
                for e in [
                    get_result_type(start),
                    get_result_type(wakeup),
                ]
            ):
                raise RuntimeError(f"Result type does not match")

            result_type = get_result_type(start)
            timer_count = get_timer_count(start)
            w = get_value(wakeup)
            w = w if result_type == "dut" else [t * 1000000 for t in w]
            s = get_value(start)
            s = s if result_type == "dut" else s * 1000000

            data["i"].extend(range(len(w)))
            data["wakeup_time"].extend(w)
            data["start_time"].extend([s] * len(w))
            data["result_type"].extend([result_type] * len(w))
            data["timer_count"].extend([timer_count] * len(w))

            data["timer_interval"].extend([get_value(timer_interval)] * len(w))
            data["timer_version"].extend([version] * len(w))
            data["board"].extend([board] * len(w))

    return pd.DataFrame(data)


df = parse_result(basedir, boards)

df["calculated_target"] = df["start_time"] + (df["i"] + 1) * df["timer_interval"]
df["diff_target_from_start"] = df["calculated_target"] - df["start_time"]
df["diff_wakeup_from_start"] = df["wakeup_time"] - df["start_time"]
df["diff_wakeup_from_target"] = df["wakeup_time"] - df["calculated_target"]

df = df[df.result_type == "hil"]

fig = px.box(
    df,
    x="timer_count",
    y="diff_wakeup_from_target",
    color="timer_version",
    hover_data=["i", "diff_wakeup_from_target"],
    facet_col="board",
    facet_col_wrap=2,
    facet_col_spacing=0.06,
)

fig.update_yaxes(
    matches=None,
    showticklabels=True,
)

# legend
fig.update_layout(
    legend=dict(
        title=dict(
            text="Timer Version",
            font_size=22,
        ),
        # orientation="h",
        x=.9,
        y=1.1,
        font_size=22,
    )
)
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font_size=22))
# hide original title
fig.update_yaxes(title_text="")
fig.update_xaxes(title_text="", dtick=1)
# manually use annotations to set axis title
fig.add_annotation(
    text="Nr. of Background Timer",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.05,
    showarrow=False,
    font_size=22,
)
fig.add_annotation(
    text="Difference (actual - target) wakeup time [us]",
    textangle=270,
    xref="paper",
    yref="paper",
    x=-.07,
    y=0.5,
    showarrow=False,
    font_size=22,
)

fig.write_html("/tmp/jitter_combined.html", include_plotlyjs="cdn")
fig.write_image(f"{outdir}/jitter_combined.pdf", height=1600, width=1200)

fig.write_image(f"/tmp/jitter_combined.pdf", height=1600, width=1200)
