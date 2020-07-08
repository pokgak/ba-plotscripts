#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json

import matplotlib.pyplot as plt
import numpy as np

XTIMER_BACKOFFS=[40, 30, 22]
for i, backoff in enumerate(XTIMER_BACKOFFS, start=1):
    file = f"sleep_accuracy/xunit_xtimer_usleep_set_XTIMER_BACKOFF_{backoff}_now.xml"
    root = ET.parse(file).getroot()

    # microseconds sleep
    sleep_delays = {}
    for d in root.find("testcase[@name='Measure Xtimer Set Accuracy Microseconds Template']").findall(".//property"):
        duration = d.get("name").split('-')[-1]
        sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time

    # xtimer_usleep
    start = 0
    end = 101
    keys = list(sleep_delays.keys())[start:end]
    values = list(sleep_delays.values())[start:end]
    values_mean = [np.mean(v) for v in values]
    values_std = [np.std(v) for v in values]
    plt.plot(keys, [np.mean(v) for v in values], label=f"xtimer_usleep / {backoff}")


    # microseconds sleep
    sleep_delays = {}
    for d in root.find("testcase[@name='Measure Xtimer Usleep Accuracy Microseconds Template']").findall(".//property"):
        duration = d.get("name").split('-')[-1]
        sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time

    # xtimer_set
    # start = 0
    # end = 1001
    keys = list(sleep_delays.keys())[start:end]
    values = list(sleep_delays.values())[start:end]
    values_mean = [np.mean(v) for v in values]
    values_std = [np.std(v) for v in values]
    plt.plot(keys, [np.mean(v) for v in values], label=f"xtimer_set / {backoff}")

    plt.xticks(np.arange(0, len(values) + 1, 10))
    plt.title(f"Difference / Specified Sleep Time [us]")

plt.gcf().set_size_inches(9.5, 6.5)
plt.legend(title='function / XTIMER_BACKOFF', loc='lower right')
plt.savefig(f"sleep_accuracy/sleep-accuracy-backoffs-now.png")
plt.show()
