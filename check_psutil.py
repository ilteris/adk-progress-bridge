import psutil
import os

proc = psutil.Process()
print(f"Process Memory Info: {proc.memory_info()}")
print(f"Process CPU Times: {proc.cpu_times()}")
print(f"Process Num Threads: {proc.num_threads()}")
print(f"Process Nice: {proc.nice()}")
print(f"Process Ionice: {proc.ionice() if hasattr(proc, 'ionice') else 'N/A'}")
print(f"System CPU Times: {psutil.cpu_times()}")
print(f"System CPU Percent (per-cpu): {psutil.cpu_percent(percpu=True)}")
print(f"System Virtual Memory: {psutil.virtual_memory()}")
print(f"System Swap Memory: {psutil.swap_memory()}")
print(f"System Disk Partitions: {psutil.disk_partitions()}")
print(f"System Net IO Counters: {psutil.net_io_counters()}")
print(f"System Sensors Temperatures: {psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else 'N/A'}")
print(f"System Sensors Battery: {psutil.sensors_battery() if hasattr(psutil, 'sensors_battery') else 'N/A'}")
