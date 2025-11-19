import platform
import xr
import time

from xr_system import XRSystem
from xr_time import XRTimeProvider
from xr_actions import XRControllerActions
from xr_tracker import XRControllerTracker

from xr_broadcaster.panel import ControlPanel
from xr_broadcaster.visualizer import ControllerVisualizer


def main():
    # 扩展
    extensions = [xr.MND_HEADLESS_EXTENSION_NAME]
    if platform.system() == "Windows":
        extensions.append(xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME)
    else:
        extensions.append(xr.KHR_CONVERT_TIMESPEC_TIME_EXTENSION_NAME)

    # 初始化模块
    xr_sys = XRSystem(extensions)
    timer = XRTimeProvider(xr_sys.instance)
    actions = XRControllerActions(xr_sys.instance, xr_sys.session)
    tracker = XRControllerTracker(actions, timer)

    panel = ControlPanel(); panel.start()
    viz = ControllerVisualizer()

    # 主循环
    try:
        while True:
            xr_sys.poll_events()

            if xr_sys.state == xr.SessionState.FOCUSED:
                l_pose, r_pose = tracker.poll()

                if l_pose and r_pose:
                    panel.update({
                        "L_xyz": l_pose.position, "L_q": l_pose.orientation,
                        "R_xyz": r_pose.position, "R_q": r_pose.orientation
                    })
                    viz.update(l_pose, r_pose)

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()
