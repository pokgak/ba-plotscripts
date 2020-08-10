# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from ast import literal_eval


# %%
# file = f"data/sleep_jitter/xunit copy.xml"
file = f"data/sleep_jitter/xunit divisor.xml"
root = ET.parse(file).getroot()

traces = {}
jitter_repeat = pd.DataFrame()
for testcase in root.findall("testcase[@classname='tests_gpio_overhead.Sleep Jitter']"):
    parent = testcase
    for d in testcase.findall(".//property"):
        name = d.get("name").split("-")
        if "intervals" in name:
            intervals = literal_eval(d.get("value"))
        elif "trace" in name:
            repeat_count = int(name[-1])
            traces[repeat_count] = literal_eval(d.get("value"))
        elif "divisor" in name:
            divisor = int(d.get("value"))

    newdf = {
        "repeat_count": n,
        "time": [i for i in range(1, len(traces[n]) + 1)],
        "trace": traces[n],
        "trace_milli": map(lambda x: x * 1000, traces[n]),
        "background_timers": [str(len(intervals))] * len(traces[n]),
    }

    if "Divisor" in parent.get("name"):
        newdf["divisor"] = [divisor] * len(newdf["trace"])

    for n in traces.keys():
        jitter_repeat = jitter_repeat.append(pd.DataFrame.from_dict(newdf))

# plot
# jitter_repeat_fig = px.violin(
#     jitter_repeat, x="background_timers", y="trace_milli", color="background_timers"
# )
# go.FigureWidget(jitter_repeat_fig)

# jitter_scatter = px.scatter(
#     jitter_repeat, y='time', x='trace_milli', color="background_timers", opacity=0.5, marginal_x='violin'
# )
# go.FigureWidget(jitter_scatter)


# %%
# plot the jitter with different "busyness" (divisor)
jitter_divisor = jitter_repeat.dropna()

# jitter_table = go.FigureWidget(data=[go.Table(
#     header=dict(values=['trace_milli', 'divisor']),
#     cells=dict(values=[jitter_divisor.trace_milli, jitter_divisor.divisor])
# )])
# go.FigureWidget(jitter_table)

jitter_divisor_fig = px.violin(
    jitter_divisor, x="divisor", y="trace_milli", color="divisor"
)
go.FigureWidget(jitter_divisor_fig)
# %% Plot Drift Simple Percentage Difference Measurements

# file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_gpio_overhead/xunit.xml"
# file = "data/drift/1-15-30-seconds-10-repeats.xml"
file = "data/drift/1-14-seconds-continuous-10-repeats.xml"
root = ET.parse(file).getroot()

drift_simple_single = dict()
dss = drift_simple_single
for testcase in root.findall("testcase[@classname='tests_gpio_overhead.Drift']"):

    for prop in testcase.findall(".//property"):
        # name formatted as 'name'-'unit', we ditch the unit
        name = prop.get("name").split("-")

        repeat_n = int(name[name.index("repeat") + 1])  # repeat count
        # values are recorded as string, convert to float
        value = float(literal_eval(prop.get("value"))[-1])

        key = int(name[2]) / 1_000_000
        if key not in dss:
            dss[key] = []

        dss[key].append(
            {
                "time": key,
                "repeat": repeat_n,
                "dut" if "dut" in name else "philip": value,
            }
        )

df = pd.DataFrame()
for k in dss.keys():
    for row in dss[k]:
        df = df.append(row, ignore_index=True)

# combine dut, philip rows with same (time, repeat) to remove NaN values
df = df.groupby(["time", "repeat"]).sum()
df["diff_dut_philip"] = df["dut"] - df["philip"]
df["diff_percentage"] = df["diff_dut_philip"] / df["dut"] * 100

dss_fig = px.box(
    df,
    x=df.index.get_level_values(0),
    y="diff_percentage",
    # color='x',
    hover_data=["diff_dut_philip", "diff_percentage"],
    # points="all",
    title=f"Drift Percentage for Sleep Duration {min(dss.keys())} - {max(dss.keys())} seconds",
    labels={
        "diff_dut_philip": "Difference [s]",
        "diff_percentage": "Percentage Actual/Given [%]",
        "time": "Sleep Duration [s]",
        "x": "Sleep Duration [s]",
    },
)

# to add max line based on board info
# dss_fig.update_layout(shapes=[

#     dict(
#         type='line',
#         yref= 'y', y0=0.2, y1=0.2,
#         xref= 'x', x0=0, x1=30,
#     )
# ])

dss_fig.write_html("docs/drift.html")
go.FigureWidget(dss_fig)

# %% Plot Line Chart for Drift Diff

# ignore
# line chart not useful due to the scale
dss_line_fig = px.line(df, x=df.index.get_level_values(0), y=["dut", "philip"], labels={
        "diff_dut_philip": "Difference [s]",
        "diff_percentage": "Percentage Actual/Given [%]",
        "time": "Sleep Duration [s]",
        "value": "Actual Sleep Duration [s]",
        "x": "Sleep Duration [s]",
    },)

dss_line_fig.write_html("docs/drift_line.html")
go.FigureWidget(dss_line_fig)
