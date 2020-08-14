# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from ast import literal_eval

# %% Parse GPIO Overhead
file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_timer_benchmarks/xunit.xml"
# file = f"data/gpio_overhead/xunit.xml"
root = ET.parse(file).getroot()

for prop in root.findall(
    "testcase[@classname='tests_timer_benchmarks.Gpio Overhead']//property"
):
    if prop.get("name") != "gpio-overhead":
        raise RuntimeError("Other property than 'gpio-overhead' found")

    gpio_overhead = pd.Series(literal_eval(prop.get("value")))
    print(gpio_overhead.describe())

# %% Accuracy
file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_timer_benchmarks/xunit.xml"
root = ET.parse(file).getroot()

accuracy_rows = []
backoff = literal_eval(
    root.find(
        "testcase[@classname='tests_timer_benchmarks.Sleep Accuracy']//property[@name='xtimer-backoff']"
    ).get("value")
)
for prop in root.findall(
    "testcase[@classname='tests_timer_benchmarks.Sleep Accuracy']//property"
):
    name = prop.get("name")
    if "accuracy" in name:
        function = name.split("-")[-2]
        target = literal_eval(name.split("-")[-1]) / 1_000_000  # convert to sec
        actuals = literal_eval(prop.get("value"))

        for i, v in enumerate(actuals):
            accuracy_rows.append(
                {
                    "target_duration": target,
                    "actual_duration": v,
                    "diff_actual_target": v - target,
                    "repeat": i,
                    "backoff": backoff,
                    "type": function,
                }
            )

accuracy = pd.DataFrame(accuracy_rows)

accuracy_fig = go.Figure()
for typ, backoff in accuracy.groupby(["type", "backoff"]).groups.keys():
    df = accuracy.query(f"type == '{typ}' and backoff == {backoff}")
    accuracy_fig.add_trace(
        go.Scatter(
            x=df["target_duration"],
            y=df["diff_actual_target"],
            name=f"{typ} / {backoff}",
        )
    )

go.FigureWidget(accuracy_fig)


# %%    Jitter - varied timer count
file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_timer_benchmarks/xunit.xml"
# file = f"data/sleep_jitter/xunit.xml"
root = ET.parse(file).getroot()

jitter = {"timer_count": [], "sleep_duration": [], "divisor": []}
for testcase in root.findall(
    "testcase[@classname='tests_timer_benchmarks.Sleep Jitter']"
):
    timer_count = len(
        literal_eval(
            testcase.find("properties/property[@name='intervals']").get("value")
        )
    )
    divisor = literal_eval(
        testcase.find("properties/property[@name='divisor']").get("value")
    )
    traces = literal_eval(
        testcase.find("properties/property[@name='trace']").get("value")
    )

    jitter["sleep_duration"].extend(traces)
    jitter["timer_count"].extend([str(timer_count)] * len(traces))
    if "Divisor" in testcase.get("name"):
        jitter["divisor"].extend([divisor] * len(traces))
    else:
        # divisor None means = 1, not used when varying timer count
        jitter["divisor"].extend([None] * len(traces))

jitter = pd.DataFrame(jitter)

jitter_fig = px.strip(
    jitter[jitter["divisor"].isnull()], x="timer_count", y="sleep_duration",
)

go.FigureWidget(jitter_fig)

# %% Jitter - varied divisor

jitter_divisor = jitter[jitter["divisor"].notnull()]
jdg = jitter.groupby("divisor").describe()
jitter_table = go.Figure(
    data=[
        go.Table(
            header=dict(values=["divisor", "min", "mean", "max"]),
            cells=dict(
                align="left",
                values=[
                    jdg.index,
                    jdg["sleep_duration"]["min"],
                    jdg["sleep_duration"]["mean"],
                    jdg["sleep_duration"]["max"],
                ],
            ),
        )
    ]
)

go.FigureWidget(jitter_table)

# %% Plot Drift Simple Percentage Difference Measurements

# file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_timer_benchmarks/xunit.xml"
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
df.reset_index(["time", "repeat"], inplace=True)

# dss_fig = px.box(
#     df,
#     x='time',
#     y="diff_percentage",
#     # color='x',
#     hover_data=["diff_dut_philip", "diff_percentage"],
#     # points="all",
#     title=f"Drift Percentage for Sleep Duration {min(dss.keys())} - {max(dss.keys())} seconds",
#     labels={
#         "diff_dut_philip": "Difference [s]",
#         "diff_percentage": "Percentage Actual/Given [%]",
#         "time": "Sleep Duration [s]",
#         "x": "Sleep Duration [s]",
#     },
# )

percentage = go.Box(x=df["time"], y=df["diff_percentage"])
absolute = go.Box(x=df["time"], y=df["diff_dut_philip"], visible=False)
absolute_line = go.Scatter(
    x=df["time"].unique(),
    y=df.groupby("time").mean()["diff_dut_philip"].array,
    visible=False,
)
dss_fig = go.Figure([percentage, absolute, absolute_line])

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
            buttons=list(
                [
                    dict(
                        args=["boxpoints", "outliers"],
                        label="Outliers",
                        method="restyle",
                    ),
                    dict(
                        args=["boxpoints", "all"], label="All Points", method="restyle",
                    ),
                ]
            ),
            showactive=True,
            x=0,
            xanchor="left",
            y=1.15,
            yanchor="top",
        ),
        dict(
            buttons=list(
                [
                    dict(
                        args=[{"visible": [True, False, False]}],
                        label="Percentage",
                        method="update",
                    ),
                    dict(
                        args=[{"visible": [False, True, True]}],
                        label="Absolute Difference",
                        method="update",
                    ),
                ]
            ),
            showactive=True,
            x=0.1,
            xanchor="left",
            y=1.15,
            yanchor="top",
        ),
    ]
)

dss_fig.write_html("docs/drift.html")
go.FigureWidget(dss_fig)
