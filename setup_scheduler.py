#!/usr/bin/env python3
"""
Setup Windows Task Scheduler for daily Paper Digest execution.

This script creates a Windows scheduled task that runs paper_digest
every day at 8:00 AM (or your specified time).

Usage:
    python setup_scheduler.py                  # Schedule at 08:00
    python setup_scheduler.py --time 07:30     # Schedule at 07:30
    python setup_scheduler.py --remove         # Remove the scheduled task
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TASK_NAME = "PaperDigest_PlantBiology"
PYTHON_EXE = sys.executable
MAIN_SCRIPT = BASE_DIR / "main.py"


def create_scheduled_task(hour: int, minute: int):
    """Create a Windows Task Scheduler task for daily execution."""
    if os.name != "nt":
        print("⚠ This script only supports Windows Task Scheduler.")
        print("  For Linux/Mac, use cron instead:")
        print(f"  0 {hour} * * * cd {BASE_DIR} && {PYTHON_EXE} {MAIN_SCRIPT} >> {BASE_DIR}/logs/cron.log 2>&1")
        return

    # Build the XML task definition
    task_xml = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{__import__('datetime').datetime.now().isoformat()}</Date>
    <Author>Paper Digest Bot</Author>
    <Description>Daily plant biology paper digest generation at {hour:02d}:{minute:02d}</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}T{hour:02d}:{minute:02d}:00</StartBoundary>
      <Repetition>
        <Interval>PT24H</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.environ.get('USERNAME', os.environ.get('USER', 'SYSTEM'))}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>true</WakeToRun>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{PYTHON_EXE}</Command>
      <Arguments>{MAIN_SCRIPT}</Arguments>
      <WorkingDirectory>{BASE_DIR}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''

    # Write XML to temp file
    xml_path = BASE_DIR / "task_definition.xml"
    xml_path.write_text(task_xml, encoding="utf-16")

    try:
        # Remove existing task if any
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            capture_output=True,
        )

        # Create the task
        result = subprocess.run(
            [
                "schtasks", "/Create",
                "/TN", TASK_NAME,
                "/XML", str(xml_path),
                "/F",
            ],
            capture_output=True,
            text=True,
        )

        # Clean up
        xml_path.unlink()

        if result.returncode == 0:
            print(f"✅ 计划任务已创建成功！")
            print(f"   任务名称: {TASK_NAME}")
            print(f"   执行时间: 每天 {hour:02d}:{minute:02d}")
            print(f"   执行命令: {PYTHON_EXE} {MAIN_SCRIPT}")
            print(f"   工作目录: {BASE_DIR}")
            print()
            print("💡 提示:")
            print(f"   - 查看所有计划任务: schtasks /Query")
            print(f"   - 手动运行一次: schtasks /Run /TN \"{TASK_NAME}\"")
            print(f"   - 删除此任务: python setup_scheduler.py --remove")
        else:
            print(f"❌ 创建失败:")
            print(result.stderr)
    except FileNotFoundError:
        print("❌ 未找到 schtasks 命令，请确认在 Windows 系统上运行。")
    except Exception as e:
        print(f"❌ 错误: {e}")


def remove_scheduled_task():
    """Remove the Paper Digest scheduled task."""
    if os.name != "nt":
        print("⚠ This script only supports Windows.")
        return

    result = subprocess.run(
        ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(f"✅ 计划任务 '{TASK_NAME}' 已删除。")
    elif "ERROR: The system cannot find the file specified" in result.stderr:
        print(f"⚠ 计划任务 '{TASK_NAME}' 不存在。")
    else:
        print(f"❌ {result.stderr}")


def check_task_status():
    """Display the current scheduled task status."""
    if os.name != "nt":
        print("⚠ This script only supports Windows.")
        return

    result = subprocess.run(
        ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"⚠ 计划任务 '{TASK_NAME}' 不存在。")
        print("  运行 'python setup_scheduler.py' 来创建。")


def main():
    parser = argparse.ArgumentParser(
        description="设置 Paper Digest 的 Windows 计划任务",
    )
    parser.add_argument(
        "--time", "-t",
        type=str,
        default="08:00",
        help="每日执行时间，HH:MM 格式 (默认: 08:00)",
    )
    parser.add_argument(
        "--remove", "-r",
        action="store_true",
        help="删除现有的计划任务",
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="查看当前计划任务状态",
    )

    args = parser.parse_args()

    if args.remove:
        remove_scheduled_task()
    elif args.status:
        check_task_status()
    else:
        try:
            hour, minute = map(int, args.time.split(":"))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except ValueError:
            print(f"❌ 无效的时间格式: '{args.time}'")
            print("  请使用 HH:MM 格式，如 08:00, 07:30")
            sys.exit(1)

        print("🌱 Paper Digest - 计划任务配置")
        print("=" * 50)
        print(f"  Python: {PYTHON_EXE}")
        print(f"  脚本: {MAIN_SCRIPT}")
        print(f"  时间: 每天 {hour:02d}:{minute:02d}")
        print("=" * 50)
        print()

        create_scheduled_task(hour, minute)


if __name__ == "__main__":
    main()
