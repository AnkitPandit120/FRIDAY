# system_status.py
import platform
import shutil
import sys
from pathlib import Path

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


def system_status(
    parameters: dict = None,
    player=None,
) -> str:
    """
    Retrieves current system statistics including CPU usage, RAM utilization,
    Disk space, and Battery status.
    """
    if player:
        player.write_log("[SystemStatus] Querying system diagnostics...")

    report = []
    report.append("=== System Status Report ===")
    report.append(f"Operating System: {platform.system()} {platform.release()}")

    # CPU Information
    if _PSUTIL:
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            cpu_phys = psutil.cpu_count(logical=False)
            cpu_log = psutil.cpu_count(logical=True)
            report.append(f"CPU: {cpu_usage}% usage ({cpu_phys} physical / {cpu_log} logical cores)")
        except Exception as e:
            report.append(f"CPU: Error reading stats ({e})")
    else:
        report.append("CPU: psutil not installed (cannot read real-time usage)")

    # Memory (RAM) Information
    if _PSUTIL:
        try:
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            used_gb = mem.used / (1024 ** 3)
            report.append(f"RAM: {mem.percent}% used ({used_gb:.2f} GB used / {total_gb:.2f} GB total)")
        except Exception as e:
            report.append(f"RAM: Error reading stats ({e})")
    else:
        report.append("RAM: psutil not installed")

    # Disk Space (Root /)
    try:
        total, used, free = shutil.disk_usage("/")
        disk_pct = (used / total) * 100
        report.append(f"Disk: {disk_pct:.1f}% used ({free / (1024 ** 3):.2f} GB free of {total / (1024 ** 3):.2f} GB)")
    except Exception as e:
        report.append(f"Disk: Error reading stats ({e})")

    # Battery Status
    if _PSUTIL:
        try:
            battery = psutil.sensors_battery()
            if battery:
                plugged = "Plugged in" if battery.power_plugged else "Running on battery"
                secs = battery.secsleft
                time_left_str = ""
                if secs == psutil.POWER_TIME_UNLIMITED:
                    time_left_str = " (Unlimited/AC power)"
                elif secs == psutil.POWER_TIME_UNKNOWN:
                    time_left_str = " (Calculating time remaining...)"
                else:
                    hrs = secs // 3600
                    mins = (secs % 3600) // 60
                    time_left_str = f" ({hrs}h {mins}m remaining)"
                report.append(f"Battery: {battery.percent}% [{plugged}]{time_left_str}")
            else:
                report.append("Battery: No battery detected (likely desktop system)")
        except Exception as e:
            report.append(f"Battery: Error reading stats ({e})")
    else:
        report.append("Battery: psutil not installed")

    final_report = "\n".join(report)
    print(f"[SystemStatus] Diagnostics generated:\n{final_report}")
    return final_report
