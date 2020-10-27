# %%
def get_intervals(min, max, count):
    val_range = max - min
    step = int(val_range / count)
    return [min + (i * step) + 10000 for i in range(count)]


# %%
import pandas as pd
import plotly.graph_objects as go

traces = []

for n in range(5, 26, 5):
    triggers = []
    intervals = get_intervals(10000, 100000, n)
    for i in intervals:
        # assuming all the timer starts at the same time,
        # extrapolate to see at which time the timer will triggers
        # before max test period finishes
        triggers.extend(range(0, 500000, i))

    # calculate differences between consecutive triggers
    triggers_uniq = sorted(list(set(triggers)))
    diffs = [j - i for i, j in zip(triggers_uniq[:-1], triggers_uniq[1:])]
    print("n", n, "max", max(diffs), "min", min(diffs))
    print("freq time cons. triggers:")
    print(pd.Series(diffs).value_counts().head())

    import pandas as pd
    import plotly.graph_objects as go

    # get frequency collision between timers
    freq = pd.Series(triggers).value_counts()
    freq = freq.drop(index=0)

    traces.append(go.Bar(x=freq.index, y=freq, name=n))

fig = go.Figure(traces)
fig.update_traces(opacity=0.75)
fig.update_layout(
    barmode="overlay",
    title="Trigger Frequency (assume all start at t=0)",
    yaxis_title="Count",
    xaxis_title="Time [us]",
)
fig.show()

# %%
