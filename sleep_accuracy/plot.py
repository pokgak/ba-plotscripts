#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json

import matplotlib.pyplot as plt
import numpy as np

XTIMER_BACKOFF=40
# file = "sleep_time/xunit_test3.xml"
# file = "sleep_time/xunit_50repeat.xml"
# file = f"sleep_time/xunit_XTIMER_BACKOFF_{XTIMER_BACKOFF}.xml"
file = f"sleep_accuracy/xunit_xtimer_usleep_set_XTIMER_BACKOFF_{XTIMER_BACKOFF}.xml"
root = ET.parse(file).getroot()

# # gpio overhead
# gpio_delay = root.find("testcase[@classname='tests_gpio_overhead.Gpio Overhead']")
# gpio_overhead = gpio_delay.find(".//property[@name='gpio-overhead']")
# diffs = [float(r["diff"]) for r in eval(gpio_overhead.get("value"))]   # remove in newest data

# print(f"Sample count: {len(diffs)}")
# print(f"Min: {np.amin(diffs)}")
# print(f"Max: {np.amax(diffs)}")
# print(f"Average: {np.mean(diffs)}")
# print(f"Std: {np.std(diffs)}")

# microseconds sleep
sleep_delays = {}
for d in root.find("testcase[@name='Measure Xtimer Usleep Accuracy Microseconds Template']").findall(".//property"):
    duration = d.get("name").split('-')[-1]
    sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time

# full range
keys = list(sleep_delays.keys())
values = list(sleep_delays.values())
values_mean = [np.mean(v) for v in values]
values_std = [np.std(v) for v in values]
plt.plot(keys, [np.mean(v) for v in values], label="xtimer_usleep")

sleep_delays = {}
for d in root.find("testcase[@name='Measure Xtimer Set Accuracy Microseconds Template']").findall(".//property"):
    duration = d.get("name").split('-')[-1]
    sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time

# full range
keys = list(sleep_delays.keys())
values = list(sleep_delays.values())
values_mean = [np.mean(v) for v in values]
values_std = [np.std(v) for v in values]
plt.plot(keys, [np.mean(v) for v in values], label="xtimer_set")

plt.legend()
plt.xticks(np.arange(0, 1001, 100))
plt.title(f"Difference Sleep Time / Sleep Time XTIMER_BACKOFF={XTIMER_BACKOFF} [us]")

# plt.subplots_adjust(hspace=0.5)
plt.savefig(f"sleep_accuracy/sleep-time-xtimer-usleep-set-backoff-{XTIMER_BACKOFF}.png")
plt.show()
