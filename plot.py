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
# file = "/home/pokgak/git/RobotFW-tests/build/robot/samr21-xpro/tests_timer_benchmarks/xunit.xml"
file = "/home/pokgak/git/ba-plotscripts/data/sleep_accuracy/duration-1-100-usec-backoff-30.xml"
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

accuracy_fig.update_layout(
    dict(
        title="Sleep Accuracy",
        xaxis_title="Target Sleep Duration (s)",
        yaxis_title="Difference Actual - Target Sleep Duration (s)",
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

dss_fig.update_layout(
    title=f"Drift for Sleep Duration {df['time'].min()} - {df['time'].max()} seconds",
    yaxis_title="Percentage Actual/Given Sleep Duration [%]",
    xaxis_title="Sleep Duration [s]",
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
            x=0.9,
            xanchor="left",
            y=1.1,
            yanchor="top",
        ),
        dict(
            buttons=list(
                [
                    dict(
                        args=[
                            {"visible": [True, False, False]},
                            {
                                "yaxis.title": "Percentage Actual/Given Sleep Duration [%]"
                            },
                        ],
                        label="Percentage",
                        method="update",
                    ),
                    dict(
                        args=[
                            {
                                "visible": [False, True, True],
                                "showlegend": [False, False, False],
                            },
                            {"yaxis.title": "Absolute Difference [s]"},
                        ],
                        label="Absolute Difference",
                        method="update",
                    ),
                ]
            ),
            showactive=True,
            x=0.75,
            xanchor="left",
            y=1.1,
            yanchor="top",
        ),
    ]
)

dss_fig.write_html("docs/drift.html")
go.FigureWidget(dss_fig)

# %% Get Dextool Test Case Stats from DB

import json
import sqlite3

conn = sqlite3.connect("/home/pokgak/git/RIOT-mutate/mutate/dextool_mutate.sqlite3")
c = conn.cursor()


def get_killing_tc_query(id):
    return f"SELECT t1.name,t2.location FROM all_test_case t1, killed_test_case t2, mutation t3 WHERE t3.id = {id} AND t3.st_id = t2.st_id AND t2.tc_id = t1.id;"


file = "data/dextool/report-1d1e9290.json"
report = json.load(open(file))

killed_muts = []
for file in report["files"]:
    for mut in file["mutations"]:
        if mut["status"] == "killed":
            killed_muts.append(mut["id"])

# TODO: get test cases with zero kills
kill_tc = []
for mut in killed_muts:
    killed_by = [
        tc[0] for tc in c.execute(get_killing_tc_query(mut)).fetchall()
    ]  # tc is tuple, remove unnecessary second item
    kill_tc.append({"id": mut, "killed_by": killed_by})

# %% Plot Dextool Test Case Stats

dextool_stat = pd.DataFrame()
for e in kill_tc:
    tmp = pd.DataFrame(
        {"id": e["id"] * len(e["killed_by"]), "killed_by": e["killed_by"]}
    )
    dextool_stat = dextool_stat.append(tmp, ignore_index=True)

dextool_stat = (
    dextool_stat.groupby("killed_by")
    .count()
    .reset_index()
    .rename(columns={"id": "mut_count"})
    .sort_values("mut_count")
)

dextool_stat_fig = px.bar(
    dextool_stat,
    x="killed_by",
    y="mut_count",
    title="Test Case Effectiveness",
    labels={"killed_by": "Test Case Name", "mut_count": "No. of Mutants Killed"},
)

dextool_stat_fig.write_html("docs/test_case_effectiveness.html")
go.FigureWidget(dextool_stat_fig)

# %% Timer Benchmarks

file = "data/timer_benchmarks/xunit.xml"
root = ET.parse(file).getroot()

bres = {
    "type": [],
    "time": [],
}

tests = ["set first timer", "set last timer", "remove first timer", "remove last timer"]
for t in tests:
    values = literal_eval(
        root.find('.//property[@name="overhead-{}"]'.format(t.replace(" ", "-"))).get(
            "value"
        )
    )
    bres["time"].extend(values)
    bres["type"].extend([t] * len(values))

bres = pd.DataFrame(bres)

## plot

bresgroup = bres.groupby("type")["time"].describe().reset_index()
columns = ["type", "mean", "std", "min", "max"]

bres_fig = go.Table(
    header=dict(values=columns),
    cells=dict(
        values=[list(bresgroup[col]) for col in columns],
        align="center",
        format=[[None], [".3e"]],
    ),
)
go.FigureWidget(bres_fig)

