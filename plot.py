#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json

import matplotlib.pyplot as plt
import numpy as np

file = "xunit_test2.xml"
root = ET.parse(file).getroot()

# # gpio overhead
# gpio_delay = root.find("testcase[@classname='tests_gpio_overhead.Gpio Overhead']")
# gpio_overhead = gpio_delay.find(".//property[@name='GPIO-Overhead']")
# result = gpio_overhead.get("value")
# result = json.loads(result.replace("\'", "\""))
# print(len(result))

# diffs = [float(r["diff"]) for r in result if r["event"] == "FALLING"]
# print(diffs)

# print(f"Min: {np.amin(diffs)}")
# print(f"Max: {np.amax(diffs)}")
# print(f"Average: {np.mean(diffs)}")
# print(f"Std: {np.std(diffs)}")

# microseconds sleep
sleep_delays = {}
for d in root.find("testcase[@classname='tests_gpio_overhead.Sleep Delay']").findall(".//property"):    # TODO: use name instead of classname
    duration = d.get("name")[len('sleep-delay-'):]
    sleep_delays[duration] = [float(v["diff"]) - (int(duration) / 1000_000) for v in eval(d.get("value"))]    # diff from sleep time
    # sleep_delays[duration] = [float(v["diff"]) for v in eval(d.get("value"))]   # real sleep time

plt.subplot(211)
plt.gca().set_title("Actual Sleep Time / Sleep Time [us]")
plt.plot(
    list(sleep_delays.keys()),
    [np.mean(v) for v in sleep_delays.values()]
)
plt.xticks(np.arange(0, 1001, 100))
# plt.setp(plt.gca().get_xticklabels(), rotation=-90)

plt.subplot(212)
plt.plot(
    list(sleep_delays.keys())[:50],
    [np.mean(v) for v in sleep_delays.values()][:50]
)
plt.xticks(np.arange(0, 50, 5))

plt.gca().set_title("Actual Sleep Time / Sleep Time for range 1-50 [us]")
plt.savefig("microseconds.pdf")
plt.show()
