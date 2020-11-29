# %%
import os
import itertools

import pandas as pd
import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px

from ast import literal_eval
from plotly.subplots import make_subplots

# %% ppm calc
US_PER_SECOND = 1000000
AGING_RATE = 5

# tolerance = sum of (freq. stability(DUT) + freq. tolerance (DUT) + freq. tolerance (PHILIP))
# tolerance = 50 + 50 + 50
TOLERANCE = 150
AGE = 2


def get_color(idx, alpha):
    color = px.colors.qualitative.Plotly[idx]
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def get_threshold_line(tolerance, age=0):
    freq_tolerance = tolerance + (age * AGING_RATE)

    threshold_x = list(range(1, 60))
    threshold_y = [
        (t * (freq_tolerance / 1000000)) * US_PER_SECOND for t in threshold_x
    ]
    return (
        go.Scatter(
            x=threshold_x,
            y=threshold_y,
            # fill="tozeroy",
            # opacity=0.1,
            # fillcolor="red",
            line=dict(width=2, dash="dot", color="black"),
            # showlegend=False,
            name="Threshold",
            legendgroup="threshold",
        ),
        go.Scatter(
            x=threshold_x,
            y=[-y for y in threshold_y],
            # fill="tozeroy",
            # opacity=0.1,
            # fillcolor="red",
            line=dict(width=2, dash="dot", color="black"),
            showlegend=False,
            name="Threshold",
            legendgroup="threshold",
        ),
    )


# based on https://plotly.com/python/line-charts/#filled-lines
def get_threshold(tmp, idx, tolerance, age):
    board = tmp["board"].iloc[0]
    x = list(tmp["target_duration"])
    x_rev = x[::-1]

    fill = [
        tolerance + (age * AGING_RATE) for i in range(len(tmp["diff_actual_target"]))
    ]
    y_upper = [y + r for y, r in zip(list(tmp["diff_actual_target"]), fill)]
    y_lower = [y - r for y, r in zip(list(tmp["diff_actual_target"]), fill)][::-1]

    # print('\n', board)
    # print('y', list(tmp['diff_actual_target']))
    # print('fill:', fill)
    # print('x', x + x_rev)
    # print('y', y_upper + y_lower)
    return go.Scatter(
        x=x + x_rev,
        y=y_upper + y_lower,
        name=board,
        mode="lines",
        fill="toself",
        fillcolor=get_color(idx, 0.3),
        line_color="rgba(255,255,255,0)",
        showlegend=False,
        legendgroup=board,
    )


# %%

outdir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/result"
basedir = "/home/pokgak/git/ba-plotscripts/docs/timer_benchmarks/data"

excluded_boards = ["samr21-xpro", "saml10-xpro", "frdm-kw41z"]
# boards = [b for b in os.listdir(basedir) if b not in excluded_boards]
boards = os.listdir(basedir)

data = {
    "board": [],
    "timer_version": [],
    "result_type": [],
    "target_duration": [],
    "actual_duration": [],
}

for timer, board in itertools.product(["xtimer", "ztimer"], boards):
    root = ET.parse(f"{basedir}/{board}/tests_{timer}_benchmarks/xunit.xml")

    path = f"testcase[@classname='tests_{timer}_benchmarks.Drift']//property"
    for prop in root.iterfind(path):
        name = prop.get("name").split("-")
        target_duration = name[2]
        result_type = name[0]
        if result_type == "dut":
            continue

        data["board"].append(board)
        data["timer_version"].append(timer)
        data["result_type"].append(result_type)
        data["target_duration"].append(int(target_duration))

        duration = literal_eval(prop.get("value"))
        duration = (
            float(duration[0]) * 1000000
            if result_type == "dut"
            else float(duration) * 1000000
        )
        data["actual_duration"].append((duration))

df = pd.DataFrame(data)
df["diff_actual_target"] = df["actual_duration"] - df["target_duration"]


fig = px.line(
    df,
    x=[v / 1000000 for v in df["target_duration"]],
    y="diff_actual_target",
    color="board",
    facet_col="timer_version",
)

fig.add_traces(get_threshold_line(TOLERANCE, AGE), rows=1, cols=1)
fig.add_traces(get_threshold_line(TOLERANCE, AGE), rows=1, cols=2)
fig.data[-2].showlegend = False

fig.update_layout(legend_title="Board")
fig.update_yaxes(col=1, title="Diff. actual duration from target [us]")
fig.update_xaxes(title="Target Duration [s]")

fig.write_image(f"{outdir}/drift.pdf")
go.FigureWidget(fig)

# %%

df2 = df.query("(board not in @excluded_boards)").copy()
df2["target_duration"] = [t / 1000000 for t in df2["target_duration"]]

fig2 = px.line(
    df2,
    x="target_duration",
    y="diff_actual_target",
    color="board",
    facet_col="timer_version",
    title=f"Without {', '.join(excluded_boards)} boards",
    labels={
        "diff_actual_target": "Duration actual - target [us]",
        "target_duration": "Target Sleep Duration [s]",
        "board": "Board",
    },
)

for col, timer in enumerate(df2["timer_version"].unique()):
    for idx, board in enumerate(df2["board"].unique()):
        tmp = df2[(df2.board == board) & (df2.timer_version == timer)]
        fill = get_threshold(tmp, idx, tolerance=TOLERANCE, age=AGE)
        fig2.add_trace(fill, row=1, col=col + 1)
    fig2.add_trace(get_threshold_line(TOLERANCE, AGE)[0], row=1, col=col + 1)
fig2.data[-1].showlegend = False  # only show one legend for threshold

fig2.write_image(f"{outdir}/drift_partial.pdf")
# go.FigureWidget(fig2)
# fig2.show()
