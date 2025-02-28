import re

import psutil


def get_cpu_gpu_mem_temps():
    temps = psutil.sensors_temperatures()
    if temps:
        gpu_temp = 0
        mem_temp = 0
        max_temp = 0
        for name, entries in temps.items():
            for entry in entries:
                if re.match(r"cpu\d+_thermal", name):
                    max_temp = max(max_temp, entry.current)
                elif name == "ddr_thermal":
                    mem_temp: w = entry.current
                elif name == "video_thermal":
                    gpu_temp = entry.current

        return max_temp, gpu_temp, mem_temp

    return None, None, None
