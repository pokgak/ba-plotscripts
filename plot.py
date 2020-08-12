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
file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_gpio_overhead/xunit.xml"
# file = f"data/sleep_jitter/xunit.xml"
root = ET.parse(file).getroot()

jitter = {"timer_count": [], "sleep_duration": [], "divisor": []}
for testcase in root.findall("testcase[@classname='tests_gpio_overhead.Sleep Jitter']"):
    timer_count = len(literal_eval(testcase.find("properties/property[@name='intervals']").get('value')))
    divisor = literal_eval(testcase.find("properties/property[@name='divisor']").get('value'))
    traces = literal_eval(testcase.find("properties/property[@name='trace']").get('value'))

    jitter['sleep_duration'].extend(traces)
    jitter['timer_count'].extend([str(timer_count)] * len(traces))
    if 'Divisor' in testcase.get('name'):
        jitter['divisor'].extend([divisor] * len(traces))
    else:
        # divisor None means = 1, not used when varying timer count
        jitter['divisor'].extend([None] * len(traces))

jitter = pd.DataFrame(jitter)

# jitter_fig = px.box(jitter[jitter['divisor'].isnull()],
#     x="timer_count",
#     y="sleep_duration",
#     color="timer_count",
# )

# %%

## jitter stats

jitter_divisor = jitter[jitter['divisor'].notnull()]
jdg = jitter.groupby("divisor").describe()
jitter_table = go.Figure(
    data=[
        go.Table(
            header=dict(values=["divisor", "min", "mean", "max"]),
            cells=dict(
                align="left",
                values=[
                    jdg.index, jdg['sleep_duration']['min'], jdg['sleep_duration']['mean'], jdg['sleep_duration']['max'],
                ],
            ),
        )
    ]
)

go.FigureWidget(jitter_table)

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
df.reset_index(['time', 'repeat'], inplace=True)

dss_fig = px.box(
    df,
    x='time',
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

dss_fig.update_layout(
    updatemenus=[
        dict(
            buttons=list([
                dict(
                    args=["boxpoints", "outliers"],
                    label="Outliers",
                    method="restyle",
                ),
                dict(
                    args=["boxpoints", "all"],
                    label="All Points",
                    method="restyle",
                ),
            ]),
            showactive=True,
            x=0,
            xanchor="left",
            y=1.15,
            yanchor="top",
        ),
    ]
)

dss_fig.write_html("docs/drift.html")
go.FigureWidget(dss_fig)

# %% Plot Line Chart for Drift Diff

# TODO: combine with percentage using dropdowns

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
