"""
无头模式循环打印 Quest 3 左右手柄的位姿。

- 启用 MND_headless 扩展，无需图形上下文。
- 绑定 Oculus Touch 的握持姿态（grip pose）。
- Windows 下用性能计数器时间转换成 XrTime 同步输入。
"""

import ctypes
import time
import platform
import xr

from rich import print as rprint
 
from xr_broadcaster.panel import ControlPanel
from xr_broadcaster.visualizer import ControllerVisualizer

panel = ControlPanel()
panel.start()

visualizer = ControllerVisualizer()

# -- 实例 / 会话创建 ---------------------------------------------------------------
extensions = [xr.MND_HEADLESS_EXTENSION_NAME]
if platform.system() == "Windows":
    extensions.append(xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME)
else:
    extensions.append(xr.KHR_CONVERT_TIMESPEC_TIME_EXTENSION_NAME)

instance = xr.create_instance(
    xr.InstanceCreateInfo(enabled_extension_names=extensions),
)
system = xr.get_system(
    instance,
    xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY),
)
session = xr.create_session(
    instance,
    xr.SessionCreateInfo(system_id=system, next=None),
)


# -- 时间转换辅助 ------------------------------------------------------------------
if platform.system() == "Windows":
    import ctypes.wintypes

    kernel32 = ctypes.WinDLL("kernel32")
    pc_time = ctypes.wintypes.LARGE_INTEGER()
    pxr_convert_perf_counter = ctypes.cast(
        xr.get_instance_proc_addr(
            instance=instance,
            name="xrConvertWin32PerformanceCounterToTimeKHR",
        ),
        xr.PFN_xrConvertWin32PerformanceCounterToTimeKHR,
    )

    def xr_time_now() -> xr.Time:
        """将 QueryPerformanceCounter 转成 XrTime。"""
        kernel32.QueryPerformanceCounter(ctypes.byref(pc_time))
        xr_time = xr.Time()
        result = pxr_convert_perf_counter(
            instance,
            ctypes.pointer(pc_time),
            ctypes.byref(xr_time),
        )
        result = xr.check_result(result)
        if result.is_exception():
            raise result
        return xr_time

else:
    timespec_time = xr.timespec()
    pxr_convert_timespec = ctypes.cast(
        xr.get_instance_proc_addr(
            instance=instance,
            name="xrConvertTimespecTimeToTimeKHR",
        ),
        xr.PFN_xrConvertTimespecTimeToTimeKHR,
    )

    def xr_time_now() -> xr.Time:
        timespec_time.tv_sec, frac = divmod(time.clock_gettime(time.CLOCK_MONOTONIC), 1)
        timespec_time.tv_nsec = int(frac * 1e9)
        xr_time = xr.Time()
        result = pxr_convert_timespec(
            instance,
            ctypes.pointer(timespec_time),
            ctypes.byref(xr_time),
        )
        result = xr.check_result(result)
        if result.is_exception():
            raise result
        return xr_time


# -- Action / Space 配置 ----------------------------------------------------------
action_set = xr.create_action_set(
    instance=instance,
    create_info=xr.ActionSetCreateInfo(
        action_set_name="controller_set",
        localized_action_set_name="Controller Set",
        priority=0,
    ),
)
controller_paths = (xr.Path * 2)(
    xr.string_to_path(instance, "/user/hand/left"),
    xr.string_to_path(instance, "/user/hand/right"),
)
controller_pose_action = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.POSE_INPUT,
        action_name="hand_pose",
        localized_action_name="Hand Pose",
        count_subaction_paths=len(controller_paths),
        subaction_paths=controller_paths,
    ),
)
suggested_bindings = (xr.ActionSuggestedBinding * 2)(
    xr.ActionSuggestedBinding(
        action=controller_pose_action,
        binding=xr.string_to_path(
            instance=instance,
            path_string="/user/hand/left/input/grip/pose",
        ),
    ),
    xr.ActionSuggestedBinding(
        action=controller_pose_action,
        binding=xr.string_to_path(
            instance=instance,
            path_string="/user/hand/right/input/grip/pose",
        ),
    ),
)
# Quest 3 uses Oculus Touch
xr.suggest_interaction_profile_bindings(
    instance=instance,
    suggested_bindings=xr.InteractionProfileSuggestedBinding(
        interaction_profile=xr.string_to_path(
            instance,
            "/interaction_profiles/oculus/touch_controller",
        ),
        count_suggested_bindings=len(suggested_bindings),
        suggested_bindings=suggested_bindings,
    ),
)

xr.attach_session_action_sets(
    session=session,
    attach_info=xr.SessionActionSetsAttachInfo(action_sets=[action_set]),
)
action_spaces = [
    xr.create_action_space(
        session=session,
        create_info=xr.ActionSpaceCreateInfo(
            action=controller_pose_action,
            subaction_path=controller_paths[0],
        ),
    ),
    xr.create_action_space(
        session=session,
        create_info=xr.ActionSpaceCreateInfo(
            action=controller_pose_action,
            subaction_path=controller_paths[1],
        ),
    ),
]
reference_space = xr.create_reference_space(
    session=session,
    create_info=xr.ReferenceSpaceCreateInfo(
        reference_space_type=xr.ReferenceSpaceType.STAGE,
    ),
)


# -- Session loop -----------------------------------------------------------------
session_state = xr.SessionState.UNKNOWN
active_action_set = xr.ActiveActionSet(action_set=action_set, subaction_path=xr.NULL_PATH)

l_pose = None
r_pose = None

try:
    while True:
        # 轮询事件，跟踪会话状态变化
        while True:
            try:
                event_buffer = xr.poll_event(instance)
                event_type = xr.StructureType(event_buffer.type)
                if event_type == xr.StructureType.EVENT_DATA_SESSION_STATE_CHANGED:
                    event = ctypes.cast(
                        ctypes.byref(event_buffer),
                        ctypes.POINTER(xr.EventDataSessionStateChanged),
                    ).contents
                    session_state = xr.SessionState(event.state)
                    if session_state == xr.SessionState.READY:
                        # 进入 READY 后立刻 begin_session
                        xr.begin_session(
                            session,
                            xr.SessionBeginInfo(
                                primary_view_configuration_type=xr.ViewConfigurationType.PRIMARY_MONO,
                            ),
                        )
                    elif session_state == xr.SessionState.STOPPING:
                        # runtime 要停时先 end_session
                        xr.end_session(session)
                # 其他事件这里忽略
            except xr.EventUnavailable:
                break

        if session_state == xr.SessionState.FOCUSED:
            # 已经进入 FOCUSED，才同步输入和读取手柄位姿
            xr.sync_actions(
                session=session,
                sync_info=xr.ActionsSyncInfo(active_action_sets=[active_action_set]),
            )

            now = xr_time_now()
            for index, space in enumerate(action_spaces):
                location = xr.locate_space(
                    space=space,
                    base_space=reference_space,
                    time=now,
                )
                if location.location_flags & xr.SPACE_LOCATION_POSITION_VALID_BIT:
                    hand = "Left" if index == 0 else "Right"
                    # print(f"{hand} controller: {location.pose}")

                    if index == 0:
                        r_pose = location.pose
                    if index == 1:
                        l_pose = location.pose

            if l_pose and r_pose:
                panel.update({"L_xyz": l_pose.position, 
                            "L_q": l_pose.orientation,
                            "R_xyz": r_pose.position, 
                            "R_q": r_pose.orientation})
                visualizer.update(l_pose, r_pose)


            time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopped controller loop")
finally:
    xr.destroy_action_set(action_set)
    xr.destroy_instance(instance)
