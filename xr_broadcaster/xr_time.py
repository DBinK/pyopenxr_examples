import ctypes
import platform
import time
import xr


class XRTimeProvider:
    def __init__(self, instance):
        self.instance = instance
        self.platform = platform.system()

        if self.platform == "Windows":
            import ctypes.wintypes
            self.kernel32 = ctypes.WinDLL("kernel32")
            self.pc = ctypes.wintypes.LARGE_INTEGER()

            self.fn = ctypes.cast(
                xr.get_instance_proc_addr(
                    self.instance,
                    "xrConvertWin32PerformanceCounterToTimeKHR",
                ),
                xr.PFN_xrConvertWin32PerformanceCounterToTimeKHR,
            )
        else:
            self.ts = xr.timespec()
            self.fn = ctypes.cast(
                xr.get_instance_proc_addr(
                    self.instance,
                    "xrConvertTimespecTimeToTimeKHR",
                ),
                xr.PFN_xrConvertTimespecTimeToTimeKHR,
            )

    def now(self):
        if self.platform == "Windows":
            self.kernel32.QueryPerformanceCounter(ctypes.byref(self.pc))
            xr_time = xr.Time()
            self.fn(self.instance, ctypes.byref(self.pc), ctypes.byref(xr_time))
            return xr_time

        else:
            sec, frac = divmod(time.clock_gettime(time.CLOCK_MONOTONIC), 1)
            self.ts.tv_sec = int(sec)
            self.ts.tv_nsec = int(frac * 1e9)
            xr_time = xr.Time()
            self.fn(self.instance, ctypes.byref(self.ts), ctypes.byref(xr_time))
            return xr_time
