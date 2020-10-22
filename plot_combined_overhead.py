#!/usr/bin/env python3

# %% parse xztimer
import os
import argparse
from ast import literal_eval

import xml.etree.ElementTree as ET
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


OUTFILE = "xztimer_overhead.tex"

data = {
    "xtimer": "docs/timer_benchmarks/data/samr21-xpro/tests_xtimer_benchmarks/xunit.xml",
    "ztimer": "docs/timer_benchmarks/data/samr21-xpro/tests_ztimer_benchmarks/xunit.xml"
}

bres = {"row": [], "test": [], "time": [], "version": []}

for timer, file in data.items():
    tests = [
        t
        for t in ET.parse(file).findall(
            f'.//testcase[@classname="tests_{timer}_benchmarks.Timer Overhead"]//property'
        )
        if "overhead" in t.get("name")
    ]
    for t in tests:
        values = literal_eval(t.get("value"))
        bres["time"].extend(values)
        name = t.get("name").split("-")
        bres["row"].extend([name[1]] * len(values))
        bres["test"].extend([" ".join(name[2:])] * len(values))
        bres["version"].extend([timer] * len(values))

df = pd.DataFrame(bres)
df = df.groupby(["row", "test", "version"])["time"].describe()
df = df.droplevel(0)  # drop row now, becuase only using it to sort the rows
df.to_latex(
    OUTFILE,
    columns=["mean", "std", "min", "max"],
    float_format="%.3e",
    multirow=True,
    bold_rows=True,
    caption="Overhead comparison of xtimer and ztimer",
    label="fig:xztimer-overhead",
)

df
