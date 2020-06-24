#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

XTIMER_BACKOFF = 30
file = f"sleep_jitter/xunit_XTIMER_BACKOFF_{XTIMER_BACKOFF}.xml"
root = ET.parse(file).getroot()

# microseconds sleep
sleep_jitter = {}
for d in root.find("testcase[@name='Measure Sleep Jitter Microseconds Template']").findall(".//property"):
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
print(f"Max values_mean: {max(values_mean)}")
print(f"Min values_mean: {min(values_mean)}")
values_std = [np.std(v) for v in values]
ax = plt.subplot(211)
ax.set_title(f"Jitter / Sleep Time XTIMER_BACKOFF={XTIMER_BACKOFF} [us]")
ax.plot(keys, [np.mean(v) for v in values])
# ax.errorbar(keys, values_mean, values_std)
ax.set_xticks(np.arange(0, 1001, 100))
ax.axhline(0, color="black")

# [0:100]
start = 0
end = 151
keys = list(sleep_jitter.keys())[start:end]
values = list(sleep_jitter.values())[start:end]
values_mean = [np.mean(v) for v in values]
values_std = [np.std(v) for v in values]
ax = plt.subplot(212)
ax.set_title(f"... for range {str(start)}-{str(end)} [us]")
ax.set_xticks(np.arange(0, 1001, 50))
# for XTIMER_BACKOFF=30
mark = [47]
ax.plot(keys, [np.mean(v) for v in values], '-D', markevery=mark)
# ax.errorbar(keys, values_mean, values_std)
ax.axhline(0, color="black")

# [600:700]
# start = 700
# end = 900
# keys = list(sleep_jitter.keys())[start:end]
# values = list(sleep_jitter.values())[start:end]
# values_mean = [np.mean(v) for v in values]
# values_std = [np.std(v) for v in values]
# ax = plt.subplot(313)
# ax.set_title(f"Difference Sleep Time / Sleep Time for range {str(start)}-{str(end)} [us]")
# ax.set_xticks(np.arange(0, 1001, 10))
# ax.plot(keys, [np.mean(v) for v in values])
# # ax.errorbar(keys, values_mean, values_std)
# ax.axhline(0, color="black")

plt.subplots_adjust(hspace=0.8)
plt.savefig(f"sleep_jitter/microseconds-sleep-jitter-xtimer-backoff-{XTIMER_BACKOFF}.png")
plt.show()
