# %%
import os
import itertools

import pandas as pd
import xml.etree.ElementTree as ET
import plotly.graph_objects as go
import plotly.express as px

from ast import literal_eval

US_PER_SECOND = 1000000
AGING_RATE = 5

# %% ppm calc
def get_threshold(tolerance, age=0):
    freq_tolerance = tolerance + (age * AGING_RATE)

    threshold_x = list(range(1, 60))
    threshold_y = [
        (t * (freq_tolerance / 1000000)) * US_PER_SECOND for t in threshold_x
    ]
    return go.Scatter(
        x=threshold_x,
        y=threshold_y,
        fill="tozeroy",
        # fillcolor="red",
        # opacity=0.1,
        name="threshold",
    )


# %%

outdir = "/home/pokgak/git/ba-plotscripts/docs/drift"
basedir = "/home/pokgak/git/ba-plotscripts/docs/drift/data"

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

fig.update_layout(legend_title="Board")
fig.update_yaxes(col=1, title="Diff. actual duration from target [us]")
fig.update_xaxes(title="Target Duration [s]")

fig.write_image(f"{outdir}/drift.pdf")
go.FigureWidget(fig)

# %%
df2 = df.query("board not in @excluded_boards")
fig2 = px.line(
    df2,
    x=[v / 1000000 for v in df2["target_duration"]],
    y="diff_actual_target",
    color="board",
    facet_col="timer_version",
    title=f"Without {', '.join(excluded_boards)} boards",
)

fig2.update_layout(legend_title="Board")
fig2.update_yaxes(col=1, title="Diff. actual duration from target [us]")
fig2.update_xaxes(title="Target Duration [s]")

fig2.add_trace(get_threshold(50))

fig2.write_image(f"{outdir}/drift_partial.pdf")
go.FigureWidget(fig2)
