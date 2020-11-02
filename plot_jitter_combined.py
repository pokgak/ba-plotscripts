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


def plot_jitters(basedir, boards):
    data = {
        "bg_timer_count": [],
        "main_timer_interval": [],
        "i": [],
        "sleep_duration": [],
        "timer_version": [],
        "board": [],
    }

    for version, board in itertools.product(["xtimer", "ztimer"], boards):
        inputfile = f"{basedir}/{board}/tests_{version}_benchmarks/xunit.xml"
        for testcase in ET.parse(inputfile).findall(
            f"testcase[@classname='tests_{version}_benchmarks.Sleep Jitter']"
        ):
            bg_timer_count = int(
                testcase.find("properties/property[@name='bg-timer-count']").get(
                    "value"
                )
            )
            main_timer_interval = int(
                testcase.find("properties/property[@name='main-timer-interval']").get(
                    "value"
                )
            )
            # bg_timer_interval = int(
            #     testcase.find("properties/property[@name='bg-timer-interval']").get(
            #         "value"
            #     )
            # )
            traces = literal_eval(
                testcase.find("properties/property[@name='trace']").get("value")
            )
            # HACK: we repeat measurement for 51 times and
            # discard the first measurement as it is most likely 0
            # traces = traces[1:]
            # Philip record in seconds, convert to milliseconds
            traces = [v * 1000000 for v in traces]

            data["sleep_duration"].extend(traces)
            data['i'].extend(range(len(traces)))
            data["bg_timer_count"].extend([bg_timer_count] * len(traces))
            data["main_timer_interval"].extend([main_timer_interval] * len(traces))
            data["timer_version"].extend([version] * len(traces))
            data["board"].extend([board] * len(traces))
    return pd.DataFrame(data)


df = plot_jitters(basedir, boards)

# the earlier sample points might be too small to trigger
df.drop(df[(df["i"] <= 10)].index, inplace=True)

df["diff_actual_target_duration"] = df["sleep_duration"] - (df["main_timer_interval"])

fig = px.box(
    df,
    x="bg_timer_count",
    y="diff_actual_target_duration",
    color="timer_version",
    facet_col="board",
    facet_col_wrap=2,
    facet_col_spacing=0.06,
    # points="all",
    hover_data=['i'],
)

fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig.update_yaxes(matches=None, showticklabels=True)
fig.update_xaxes(tick0=0, dtick=5, showticklabels=True)

# legend
fig.update_layout(legend=dict(
    title="Timer Version",
    orientation="h",
    x=0,
    y=1.1,
))
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
fig.write_image(f"{outdir}/jitter_combined.pdf", height=900, width=900)
print(f"{outdir}/jitter_combined.pdf")
