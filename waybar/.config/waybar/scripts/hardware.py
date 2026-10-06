#!/usr/bin/env python3
"""Waybar NVIDIA usage and dynamically discovered CPU/GPU temperatures."""

import json
from pathlib import Path
import subprocess
import sys


def read(path):
    try:
        return path.read_text().strip()
    except OSError:
        return ""


def cpu_temperature():
    values = []
    for sensor in Path("/sys/class/hwmon").glob("hwmon*"):
        if read(sensor / "name") not in {"coretemp", "k10temp", "zenpower"}:
            continue
        for entry in sensor.glob("temp*_input"):
            try:
                values.append(int(read(entry)) / 1000)
            except ValueError:
                pass
    return f"{max(values):.0f}°C" if values else "N/A"


def cpu_model():
    for line in read(Path("/proc/cpuinfo")).splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return "CPU"


def nvidia_readings():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu,name",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        )
        usage, temperature, model = result.stdout.splitlines()[0].split(",", 2)
        return f"{int(usage.strip())}%", f"{int(temperature.strip())}°C", model.strip()
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        model = "NVIDIA GPU"
        try:
            result = subprocess.run(
                ["lspci"], capture_output=True, text=True, timeout=3, check=True,
            )
            for line in result.stdout.splitlines():
                if "NVIDIA" in line and any(kind in line for kind in ("VGA", "3D", "Display")):
                    model = line.split(": ", 1)[-1].split(" (rev", 1)[0]
                    break
        except (OSError, subprocess.SubprocessError):
            pass
        return "N/A", "N/A", model + "\nDriver unavailable: nvidia-smi cannot read the GPU"


def main():
    usage, temperature, status = nvidia_readings()
    if len(sys.argv) > 1 and sys.argv[1] == "temperatures":
        output = {"text": f"CPU {cpu_temperature()} · GPU {temperature}",
                  "tooltip": "CPU: " + cpu_model() + "\nGPU: " + status}
    else:
        output = {"text": f"GPU {usage}", "tooltip": status}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
