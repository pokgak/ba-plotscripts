#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json

import matplotlib.pyplot as plt
import numpy as np

file = "diff_sleeptime/xunit_test3.xml"
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
for d in root.find("testcase[@name='Measure Sleep Delay Microseconds Template']").findall(".//property"):
    duration = d.get("name")[len('sleep-delay-'):]
    sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time

# full range
keys = list(sleep_delays.keys())
values = list(sleep_delays.values())
ax = plt.subplot(311)
ax.set_title("Difference Sleep Time / Sleep Time FULL [us]")
ax.plot(keys, [np.mean(v) for v in values])
ax.set_xticks(np.arange(0, 1001, 100))

# [0:100]
start = 0
end = 100
keys = list(sleep_delays.keys())[start:end]
values = list(sleep_delays.values())[start:end]
values_mean = [np.mean(v) for v in values]
values_std = [np.std(v) for v in values]
ax = plt.subplot(312)
ax.set_title(f"Difference Sleep Time / Sleep Time for range {str(start)}-{str(end)} [us]")
ax.set_xticks(np.arange(0, 1001, 10))
ax.errorbar(keys, values_mean, values_std)

# [600:700]
start = 600
end = 700
keys = list(sleep_delays.keys())[start:end]
values = list(sleep_delays.values())[start:end]
values_mean = [np.mean(v) for v in values]
values_std = [np.std(v) for v in values]
ax = plt.subplot(313)
ax.set_title(f"Difference Sleep Time / Sleep Time for range {str(start)}-{str(end)} [us]")
ax.set_xticks(np.arange(0, 1001, 10))
ax.errorbar(keys, values_mean, values_std)

plt.savefig("diff_sleeptime/microseconds-sleep-time.pdf")
plt.show()
