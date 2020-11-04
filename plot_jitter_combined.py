import os
import argparse
import itertools

import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from ast import literal_eval

# outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
# basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"
basedir = "/home/pokgak/git/RobotFW-tests/build/robot"
# basedir = "/home/pokgak/git/ba-plotscripts/docs/jitter/norepeat1warmup"

boards = os.listdir(basedir)


def get_value(element, property):
    return element.find("properties/property[@name='{}']".format(property)).get("value")


def parse_result(basedir, boards):
    data = {
        "timer_count": [],
        "timer_interval": [],
        # "i": [],
        "dut_start_time": [],
        "dut_wakeup_time": [],
        "hil_start_time": [],
        "hil_wakeup_time": [],
        "timer_version": [],
        "board": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        inputfile = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        for testcase in ET.parse(inputfile).findall(
            f"testcase[@classname='tests_{version}_benchmarks.Sleep Jitter']"
        ):
            timer_count = int(get_value(testcase, "timer-count"))
            timer_interval = int(get_value(testcase, "timer-interval"))

            dut_start_time = literal_eval(get_value(testcase, "dut-start-time"))
            dut_wakeup_time = literal_eval(get_value(testcase, "dut-wakeup-time"))

            hil_wakeup_time = literal_eval(get_value(testcase, "hil-wakeup-time"))
            hil_start_time = literal_eval(get_value(testcase, "hil-start-time"))

            # Philip record in seconds, convert to microseconds
            hil_start_time = hil_start_time * 1000000
            hil_wakeup_time = [v * 1000000 for v in hil_wakeup_time]

            data["hil_start_time"].extend([hil_start_time] * len(hil_wakeup_time))
            data["dut_start_time"].extend([dut_start_time] * len(dut_wakeup_time))

            data["hil_wakeup_time"].extend(hil_wakeup_time)
            data["dut_wakeup_time"].extend(dut_wakeup_time)

            data["timer_count"].extend([timer_count] * len(hil_wakeup_time))
            data["timer_interval"].extend([timer_interval] * len(hil_wakeup_time))

            data["timer_version"].extend([version] * len(hil_wakeup_time))
            data["board"].extend([board] * len(hil_wakeup_time))

    for k, v in data.items():
        print(k, len(v))
    return pd.DataFrame(data)


df = parse_result(basedir, boards)

# %%

# the earlier sample points might be too small to trigger
# df.drop(df[(df["i"] == 0)].index, inplace=True)

df["diff_actual_target_duration"] = df["sleep_duration"] - (df["main_timer_interval"])

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
