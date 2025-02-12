import re

import psutil


def get_cpu_gpu_mem_temps():
    temps = psutil.sensors_temperatures()
    if temps:
        cpu_temp_sum = 0
        cpu_count = 0
        gpu_temp = 0
        mem_temp = 0
        for name, entries in temps.items():
            for entry in entries:
                if re.match(r"cpu\d+_thermal", name):
                    cpu_temp_sum += entry.current
                    cpu_count += 1
                elif name == "ddr_thermal":
                    mem_temp: w = entry.current
                elif name == "video_thermal":
                    gpu_temp = entry.current

        cpu_temp_avg = cpu_temp_sum / cpu_count if cpu_count > 0 else 0.0
        return cpu_temp_avg, gpu_temp, mem_temp

    return None, None, None
