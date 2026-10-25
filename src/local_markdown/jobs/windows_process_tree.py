"""Windows Job Object management for clean child process-tree termination."""

from __future__ import annotations

import os
import sys
from typing import Optional

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    JobObjectExtendedLimitInformation = 9
    PROCESS_SET_QUOTA = 0x0100
    PROCESS_TERMINATE = 0x0001

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryLimit", ctypes.c_size_t),
            ("PeakJobMemoryLimit", ctypes.c_size_t),
        ]


class ProcessTreeJob:
    """Encapsulates a Win32 Job Object that bounds a child process and all its sub-processes."""

    def __init__(self) -> None:
        self._job_handle: Optional[int] = None
        if sys.platform == "win32":
            handle = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            if handle:
                self._job_handle = handle
                info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
                info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                ctypes.windll.kernel32.SetInformationJobObject(
                    handle,
                    JobObjectExtendedLimitInformation,
                    ctypes.byref(info),
                    ctypes.sizeof(info),
                )

    def assign_pid(self, pid: int) -> bool:
        """Assign a process to this Job Object by PID."""
        if not self._job_handle or sys.platform != "win32":
            return False
        h_process = ctypes.windll.kernel32.OpenProcess(
            PROCESS_SET_QUOTA | PROCESS_TERMINATE, False, pid
        )
        if not h_process:
            return False
        try:
            success = ctypes.windll.kernel32.AssignProcessToJobObject(
                self._job_handle, h_process
            )
            return bool(success)
        finally:
            ctypes.windll.kernel32.CloseHandle(h_process)

    def terminate(self) -> None:
        """Terminate all processes in the Job Object immediately and close the handle."""
        if self._job_handle and sys.platform == "win32":
            try:
                ctypes.windll.kernel32.TerminateJobObject(self._job_handle, 1)
            finally:
                ctypes.windll.kernel32.CloseHandle(self._job_handle)
                self._job_handle = None

    def close(self) -> None:
        """Close the job handle when process exits normally."""
        if self._job_handle and sys.platform == "win32":
            ctypes.windll.kernel32.CloseHandle(self._job_handle)
            self._job_handle = None
