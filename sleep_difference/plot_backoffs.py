#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

first_ax = None
XTIMER_BACKOFFS=[30, 20, 12]
for idx, backoff in enumerate(XTIMER_BACKOFFS, start=1):
    file = f"sleep_difference/xunit_XTIMER_BACKOFF_{backoff}_now.xml"
    root = ET.parse(file).getroot()

    # microseconds sleep
    sleep_jitter = {}
    for d in root.find("testcase[@name='Measure Sleep Difference Microseconds Template']").findall(".//property"):
        duration = d.get("name").split('-')[2]
        sleep_jitter[duration] = []
        values = eval(d.get("value"))
        for i in range(0, int(len(values) / 2)):
            v_a = values[i * 2]["diff"]
            v_b = values[(i * 2) + 1]["diff"]
            sleep_jitter[duration].append(float(v_b) - float(v_a))

    # full range
    keys = list(sleep_jitter.keys())
    values = list(sleep_jitter.values())
    values_mean = [np.mean(v) for v in values]
    # print(f"Max values_mean: {max(values_mean)}")
    # print(f"Min values_mean: {min(values_mean)}")
    values_std = [np.std(v) for v in values]
    # ax = plt.subplot(len(XTIMER_BACKOFFS), 2, (idx * 2) - 1)
    ax = plt.subplot(len(XTIMER_BACKOFFS), 1, idx)
    if first_ax is None:
        ax = plt.subplot(len(XTIMER_BACKOFFS), 1, idx)
        first_ax = ax
    else:
        ax = plt.subplot(len(XTIMER_BACKOFFS), 1, idx, sharey=first_ax)

    ax.set_title(f"XTIMER_BACKOFF={backoff} [us]")
    ax.plot(keys, [np.mean(v) for v in values], label=str(backoff))
    ax.set_xticks(np.arange(0, 1001, 100))
    ax.axhline(0, color="black")

    # # [0:100]
    # start = 0
    # end = 151
    # keys = list(sleep_jitter.keys())[start:end]
    # values = list(sleep_jitter.values())[start:end]
    # values_mean = [np.mean(v) for v in values]
    # values_std = [np.std(v) for v in values]
    # ax = plt.subplot(len(XTIMER_BACKOFFS), 2, idx * 2)
    # ax.set_title(f"... for range {str(start)}-{str(end)}")
    # ax.set_xticks(np.arange(0, 1001, 50))
    # # for XTIMER_BACKOFF=30
    # ax.plot(keys, [np.mean(v) for v in values])
    # # ax.errorbar(keys, values_mean, values_std)
    # ax.axhline(0, color="black")

plt.subplots_adjust(hspace=0.5)
fig = plt.gcf()
fig.set_size_inches(10.5, 8.5)
fig.savefig(f"sleep_difference/sleep-difference-backoffs-now.png", dpi=100)
fig.suptitle("Jitter / Sleep Time [us]")
plt.show()
