#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

# file = "list_operations/xunit.xml"
# file = "list_operations/xunit2.xml"
# file = "list_operations/xunit_offset_no_overlap.xml"
file = "list_operations/xunit_50repeat.xml"
root = ET.parse(file).getroot()

set_n_timer = {}
for d in root.find("testcase[@name='Set Increasing Timer Template']").findall(".//property"):
    count = int(d.get("name").split('-')[1]) # get 'N' from 'set-N-timer'
    set_n_timer[count] = [float(v["diff"]) / count for v in eval(d.get("value"))]   # find average to set one timer TODO: calculate here or later?

keys = list(set_n_timer.keys())
values = list(set_n_timer.values())
values_mean = [np.mean(v) for v in values]
print(f"Max values_mean: {max(values_mean)}")
print(f"Min values_mean: {min(values_mean)}")
values_std = [np.std(v) for v in values]
ax = plt.subplot(111)
ax.set_title("Time / Number of timer FULL [us]")
ax.plot(keys, values_mean, marker='*')
# ax.errorbar(keys, values_mean, values_std)
ax.set_xticks(np.arange(0, max(keys) + 1, 5))

plt.savefig(f"list_operations/set_increasing_timer_9_17.png")
plt.show()

