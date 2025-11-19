"""
Quest 3 无头模式按键读取示例 (修复版)
支持读取 ABXY、摇杆、扳机、握把等所有按键和触摸事件
使用正确的 Oculus Touch 控制器交互配置文件
"""

import ctypes
import platform
import time
import xr
from xr_broadcaster.panel import ControlPanel

# 枚举必需的实例扩展
extensions = [xr.MND_HEADLESS_EXTENSION_NAME]  # 允许在没有图形显示的情况下使用
# 在无头模式下跟踪控制器需要获取当前XrTime的方法
if platform.system() == "Windows":
    extensions.append(xr.KHR_WIN32_CONVERT_PERFORMANCE_COUNTER_TIME_EXTENSION_NAME)
else:  # Linux
    extensions.append(xr.KHR_CONVERT_TIMESPEC_TIME_EXTENSION_NAME)

print("正在初始化 OpenXR...")

# 为无头使用创建实例
instance = xr.create_instance(
    xr.InstanceCreateInfo(
        enabled_extension_names=extensions,
    )
)

system = xr.get_system(
    instance,
    xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY),
)

session = xr.create_session(
    instance,
    xr.SessionCreateInfo(
        system_id=system,
        next=None,  # 在HEADLESS模式下不需要GraphicsBinding结构
    ),
)

# 时间转换函数设置
if platform.system() == "Windows":
    import ctypes.wintypes

    pc_time = ctypes.wintypes.LARGE_INTEGER()
    kernel32 = ctypes.WinDLL("kernel32")
    pxrConvertWin32PerformanceCounterToTimeKHR = ctypes.cast(
        xr.get_instance_proc_addr(
            instance=instance,
            name="xrConvertWin32PerformanceCounterToTimeKHR",
        ),
        xr.PFN_xrConvertWin32PerformanceCounterToTimeKHR,
    )

    def get_xr_time():
        kernel32.QueryPerformanceCounter(ctypes.byref(pc_time))
        xr_time = xr.Time()
        result = pxrConvertWin32PerformanceCounterToTimeKHR(
            instance,
            ctypes.pointer(pc_time),
            ctypes.byref(xr_time),
        )
        result = xr.check_result(result)
        if result.is_exception():
            raise result
        return xr_time
else:
    timespecTime = xr.timespec()
    pxrConvertTimespecTimeToTimeKHR = ctypes.cast(
        xr.get_instance_proc_addr(
            instance=instance,
            name="xrConvertTimespecTimeToTimeKHR",
        ),
        xr.PFN_xrConvertTimespecTimeToTimeKHR,
    )

    def get_xr_time():
        current_time_s = time.time()
        timespecTime.tv_sec = int(current_time_s)
        timespecTime.tv_nsec = int(
            (current_time_s - timespecTime.tv_sec) * 1_000_000_000
        )
        xr_time = xr.Time()
        result = pxrConvertTimespecTimeToTimeKHR(
            instance,
            ctypes.pointer(timespecTime),
            ctypes.byref(xr_time),
        )
        result = xr.check_result(result)
        if result.is_exception():
            raise result
        return xr_time


print("正在设置动作系统...")

# 创建动作集
action_set = xr.create_action_set(
    instance=instance,
    create_info=xr.ActionSetCreateInfo(
        action_set_name="quest3_input",
        localized_action_set_name="Quest 3 Input",
        priority=0,
    ),
)

# 定义控制器路径
controller_paths = (xr.Path * 2)(
    xr.string_to_path(instance, "/user/hand/left"),
    xr.string_to_path(instance, "/user/hand/right"),
)


# 所有按键配置表
ACTION_CONFIG = {
    "a_click": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "A Click",
        "paths": ["/user/hand/right/input/a/click"],
    },
    "a_touch": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "A Touch",
        "paths": ["/user/hand/right/input/a/touch"],
    },
    "b_click": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "B Click",
        "paths": ["/user/hand/right/input/b/click"],
    },
    "b_touch": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "B Touch",
        "paths": ["/user/hand/right/input/b/touch"],
    },
    # 左手按钮
    "x_click": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "X Click",
        "paths": ["/user/hand/left/input/x/click"],
    },
    "x_touch": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "X Touch",
        "paths": ["/user/hand/left/input/x/touch"],
    },
    "y_click": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "Y Click",
        "paths": ["/user/hand/left/input/y/click"],
    },
    "y_touch": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "Y Touch",
        "paths": ["/user/hand/left/input/y/touch"],
    },
    # 扳机（双手）
    "trigger": {
        "type": xr.ActionType.FLOAT_INPUT,
        "localized": "Trigger",
        "paths": [
            "/user/hand/left/input/trigger/value",
            "/user/hand/right/input/trigger/value",
        ],
        "subaction": True,
    },
    "trigger_touch": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "Trigger Touch",
        "paths": [
            "/user/hand/left/input/trigger/touch",
            "/user/hand/right/input/trigger/touch",
        ],
        "subaction": True,
    },
    # 握把
    "grip": {
        "type": xr.ActionType.FLOAT_INPUT,
        "localized": "Grip",
        "paths": [
            "/user/hand/left/input/squeeze/value",
            "/user/hand/right/input/squeeze/value",
        ],
        "subaction": True,
    },
    # 摇杆（二维）
    "thumbstick": {
        "type": xr.ActionType.VECTOR2F_INPUT,
        "localized": "Thumbstick",
        "paths": [
            "/user/hand/left/input/thumbstick",
            "/user/hand/right/input/thumbstick",
        ],
        "subaction": True,
    },
    "thumbstick_click": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "Thumbstick Click",
        "paths": [
            "/user/hand/left/input/thumbstick/click",
            "/user/hand/right/input/thumbstick/click",
        ],
        "subaction": True,
    },
    "thumbstick_touch": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "Thumbstick Touch",
        "paths": [
            "/user/hand/left/input/thumbstick/touch",
            "/user/hand/right/input/thumbstick/touch",
        ],
        "subaction": True,
    },
    # 左菜单、右系统
    "menu": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "Menu",
        "paths": ["/user/hand/left/input/menu/click"],
    },
    "system": {
        "type": xr.ActionType.BOOLEAN_INPUT,
        "localized": "System",
        "paths": ["/user/hand/right/input/system/click"],
    },
    # 控制器姿态（双手）
    "pose": {
        "type": xr.ActionType.POSE_INPUT,
        "localized": "Controller Pose",
        "paths": [
            "/user/hand/left/input/grip/pose",
            "/user/hand/right/input/grip/pose",
        ],
        "subaction": True,
    },
}

button_actions = {}  # name → action object
action_types = {}  # name → action type

for name, cfg in ACTION_CONFIG.items():
    sub_paths = None
    if cfg.get("subaction"):
        sub_paths = (xr.Path * 2)(
            xr.string_to_path(instance, "/user/hand/left"),
            xr.string_to_path(instance, "/user/hand/right"),
        )

    action = xr.create_action(
        action_set=action_set,
        create_info=xr.ActionCreateInfo(
            action_type=cfg["type"],
            action_name=name,
            localized_action_name=cfg["localized"],
            count_subaction_paths=2 if sub_paths else 0,
            subaction_paths=sub_paths,
        ),
    )

    # 保存动作对象
    button_actions[name] = action

    # 保存动作类型（按名称，而不是 Action 对象）
    action_types[name] = cfg["type"]


print("正在配置输入绑定...")

# Oculus Touch 控制器绑定 - 使用正确的路径
oculus_bindings = []

for name, cfg in ACTION_CONFIG.items():
    action = button_actions[name]
    for path in cfg["paths"]:
        oculus_bindings.append(
            xr.ActionSuggestedBinding(
                action=action,
                binding=xr.string_to_path(instance, path),
            )
        )

try:
    # 使用 Oculus Touch 控制器交互配置文件
    xr.suggest_interaction_profile_bindings(
        instance=instance,
        suggested_bindings=xr.InteractionProfileSuggestedBinding(
            interaction_profile=xr.string_to_path(
                instance, "/interaction_profiles/oculus/touch_controller"
            ),
            count_suggested_bindings=len(oculus_bindings),
            suggested_bindings=(xr.ActionSuggestedBinding * len(oculus_bindings))(
                *oculus_bindings
            ),
        ),
    )
    print("✓ Oculus Touch 控制器绑定成功")
except Exception as e:
    print(f"✗ 绑定失败: {e}")
    exit(1)

# 附加动作集到会话
xr.attach_session_action_sets(
    session=session,
    attach_info=xr.SessionActionSetsAttachInfo(
        action_sets=[action_set],
    ),
)

# 获取 pose 动作对象
POSE_NAME = "pose"
controller_pose_action = button_actions[POSE_NAME]

# 创建左右手的 action_space
controller_pose_spaces = [
    xr.create_action_space(
        session=session,
        create_info=xr.ActionSpaceCreateInfo(
            action=controller_pose_action,
            subaction_path=xr.string_to_path(instance, "/user/hand/left"),
        ),
    ),
    xr.create_action_space(
        session=session,
        create_info=xr.ActionSpaceCreateInfo(
            action=controller_pose_action,
            subaction_path=xr.string_to_path(instance, "/user/hand/right"),
        ),
    ),
]

# 创建动作空间
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

# 创建参考空间
reference_space = xr.create_reference_space(
    session=session,
    create_info=xr.ReferenceSpaceCreateInfo(
        reference_space_type=xr.ReferenceSpaceType.STAGE,
    ),
)


# 通用动作读取函数
def read_action_state(session, name, action, instance, sub_path=None):
    t = action_types[name]

    if sub_path:
        get_info = xr.ActionStateGetInfo(
            action=action,
            subaction_path=xr.string_to_path(instance, sub_path),
        )
    else:
        get_info = xr.ActionStateGetInfo(action=action)

    try:
        if t == xr.ActionType.BOOLEAN_INPUT:
            return xr.get_action_state_boolean(session, get_info).current_state

        if t == xr.ActionType.FLOAT_INPUT:
            return xr.get_action_state_float(session, get_info).current_state

        if t == xr.ActionType.VECTOR2F_INPUT:
            v = xr.get_action_state_vector2f(session, get_info).current_state
            return (v.x, v.y)
    except xr.XrException:
        print(f"XR Exception: {xr.XrException}")
        return None


session_state = xr.SessionState.UNKNOWN
print("\n🎮 Quest 3 无头模式按键读取开始...")
print("按键映射:")
print("  左手: X/Y按键, 左摇杆, 左扳机, 左握把, 菜单键")
print("  右手: A/B按键, 右摇杆, 右扳机, 右握把, 系统键")
print("  同时监控所有按键的触摸事件")
print("  按 Ctrl+C 退出\n")

# 初始化中控面板
panel = ControlPanel(title="Quest 3 控制器状态")
panel.start()


# 主循环
try:
    for frame_index in range(600):  # 运行10分钟
        # 处理会话状态变化事件
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
                    print(f"📱 OpenXR会话状态: {session_state.name}")
                    if session_state == xr.SessionState.READY:
                        xr.begin_session(
                            session,
                            xr.SessionBeginInfo(
                                primary_view_configuration_type=xr.ViewConfigurationType.PRIMARY_MONO,
                            ),
                        )
                    elif session_state == xr.SessionState.STOPPING:
                        break
                break
            except xr.EventUnavailable:
                break

        if session_state == xr.SessionState.STOPPING:
            break

        # 准备面板数据
        panel_data = {
            "会话状态": session_state.name,
            "帧计数": frame_index,
        }

        if session_state == xr.SessionState.FOCUSED:
            # 同步动作状态
            active_action_set = xr.ActiveActionSet(
                action_set=action_set,
                subaction_path=xr.NULL_PATH,  # type: ignore
            )
            xr.sync_actions(
                session=session,
                sync_info=xr.ActionsSyncInfo(
                    count_active_action_sets=1,
                    active_action_sets=ctypes.pointer(active_action_set),
                ),
            )

            try:
                panel_data = {
                    "会话状态": session_state.name,
                    "帧计数": frame_index,
                }

                # 自动读取所有动作
                for name, cfg in ACTION_CONFIG.items():
                    act = button_actions[name]

                    # 特殊处理 pose (跳过通用处理逻辑)
                    if cfg["type"] == xr.ActionType.POSE_INPUT:
                        for side, space in zip(
                            ["left", "right"], 
                            controller_pose_spaces
                        ):
                            try:
                                state = xr.locate_space(
                                    space=space,
                                    base_space=reference_space,
                                    time=get_xr_time(),
                                )

                                pos = state.pose.position
                                rot = state.pose.orientation

                                panel_data[f"{name}_{side}_pos"] = (
                                    round(pos.x, 3),
                                    round(pos.y, 3),
                                    round(pos.z, 3),
                                )
                                panel_data[f"{name}_{side}_rot"] = (
                                    round(rot.x, 3),
                                    round(rot.y, 3),
                                    round(rot.z, 3),
                                    round(rot.w, 3),
                                )
                            except Exception as e:
                                panel_data[f"{name}_{side}_pos"] = None
                                panel_data[f"{name}_{side}_rot"] = None
                        continue

                    # 处理其他类型的输入
                    if cfg.get("subaction"):
                        panel_data[f"{name}_left"] = read_action_state(
                            session, name, act, instance, "/user/hand/left"
                        )
                        panel_data[f"{name}_right"] = read_action_state(
                            session, name, act, instance, "/user/hand/right"
                        )
                    else:
                        panel_data[name] = read_action_state(
                            session, name, act, instance
                        )
                    

            except Exception as e:
                print(f"DEBUG: 读取摇杆数据时出错: {e}")
                pass

        elif session_state == xr.SessionState.IDLE:
            if frame_index % 60 == 0:  # 每分钟提醒一次
                print("⏳ 等待头显激活...")

        # 更新中控面板
        panel.update(panel_data)

        # 减慢循环
        time.sleep(0.1)


except KeyboardInterrupt:
    print("\n👋 用户中断，正在退出...")
except Exception as e:
    print(f"❌ 发生错误: {e}")
    import traceback

    traceback.print_exc()
finally:
    # 清理资源
    print("🧹 清理资源...")
    if session:
        try:
            xr.destroy_session(session)
        except:
            pass
    if instance:
        try:
            xr.destroy_instance(instance)
        except:
            pass
    print("✅ 清理完成，程序退出")
