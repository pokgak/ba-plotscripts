#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json

import matplotlib.pyplot as plt
import numpy as np

XTIMER_BACKOFFS=[60, 40, 30]
for i, backoff in enumerate(XTIMER_BACKOFFS, start=1):
    file = f"sleep_time/xunit_XTIMER_BACKOFF_{backoff}.xml"
    root = ET.parse(file).getroot()

    # microseconds sleep
    sleep_delays = {}
    for d in root.find("testcase[@name='Measure Sleep Delay Microseconds Template']").findall(".//property"):
        duration = d.get("name")[len('sleep-delay-'):]
        sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time

    # full range
    start = 0
    end = 101
    keys = list(sleep_delays.keys())[start:end]
    values = list(sleep_delays.values())[start:end]
    values_mean = [np.mean(v) for v in values]
    values_std = [np.std(v) for v in values]
    plt.title(f"Difference / Specified Sleep Time [us]")
    plt.plot(keys, [np.mean(v) for v in values], label=str(backoff))
    # ax.errorbar(keys, values_mean, values_std)
    plt.xticks(np.arange(0, len(values) + 1, 20))

plt.legend(title='XTIMER_BACKOFF')
plt.savefig(f"sleep_time/sleep-time-xtimer-backoffs-errorbar.png")
# plt.show()
