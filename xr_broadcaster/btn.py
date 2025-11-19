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
instance = xr.create_instance(xr.InstanceCreateInfo(
    enabled_extension_names=extensions,
))
 
system = xr.get_system(
    instance,
    xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY),
)
 
session = xr.create_session(
    instance,
    xr.SessionCreateInfo(
        system_id=system,
        next=None,  # 在HEADLESS模式下不需要GraphicsBinding结构
    )
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
        timespecTime.tv_nsec = int((current_time_s - timespecTime.tv_sec) * 1_000_000_000)
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
 
# 创建按键动作 - 只使用 Quest 支持的路径
button_actions = {}
 
# A/B按键 (仅右手)
button_actions['a_click'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="a_click",
        localized_action_name="A Click",
    ),
)
 
button_actions['a_touch'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="a_touch",
        localized_action_name="A Touch",
    ),
)
 
button_actions['b_click'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="b_click",
        localized_action_name="B Click",
    ),
)
 
button_actions['b_touch'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="b_touch",
        localized_action_name="B Touch",
    ),
)
 
# X/Y按键 (仅左手)
button_actions['x_click'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="x_click",
        localized_action_name="X Click",
    ),
)
 
button_actions['x_touch'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="x_touch",
        localized_action_name="X Touch",
    ),
)
 
button_actions['y_click'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="y_click",
        localized_action_name="Y Click",
    ),
)
 
button_actions['y_touch'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="y_touch",
        localized_action_name="Y Touch",
    ),
)
 
# 扳机值 (双手)
button_actions['trigger'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.FLOAT_INPUT,
        action_name="trigger",
        localized_action_name="Trigger",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
button_actions['trigger_touch'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="trigger_touch",
        localized_action_name="Trigger Touch",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
# 握把 (双手)
button_actions['grip'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.FLOAT_INPUT,
        action_name="grip",
        localized_action_name="Grip",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
# 摇杆 (双手)
button_actions['thumbstick'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.VECTOR2F_INPUT,
        action_name="thumbstick",
        localized_action_name="Thumbstick",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
button_actions['thumbstick_click'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="thumbstick_click",
        localized_action_name="Thumbstick Click",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
button_actions['thumbstick_touch'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="thumbstick_touch",
        localized_action_name="Thumbstick Touch",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
# 菜单/系统按键
button_actions['menu'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="menu",
        localized_action_name="Menu",
    ),
)
 
button_actions['system'] = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.BOOLEAN_INPUT,
        action_name="system",
        localized_action_name="System",
    ),
)
 
# 控制器姿态
controller_pose_action = xr.create_action(
    action_set=action_set,
    create_info=xr.ActionCreateInfo(
        action_type=xr.ActionType.POSE_INPUT,
        action_name="controller_pose",
        localized_action_name="Controller Pose",
        count_subaction_paths=2,
        subaction_paths=controller_paths,
    ),
)
 
print("正在配置输入绑定...")
 
# Oculus Touch 控制器绑定 - 使用正确的路径
oculus_bindings = [
    # 姿态
    xr.ActionSuggestedBinding(
        action=controller_pose_action,
        binding=xr.string_to_path(instance, "/user/hand/left/input/grip/pose"),
    ),
    xr.ActionSuggestedBinding(
        action=controller_pose_action,
        binding=xr.string_to_path(instance, "/user/hand/right/input/grip/pose"),
    ),
    
    # A/B 按键 (右手)
    xr.ActionSuggestedBinding(
        action=button_actions['a_click'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/a/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['a_touch'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/a/touch"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['b_click'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/b/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['b_touch'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/b/touch"),
    ),
    
    # X/Y 按键 (左手)
    xr.ActionSuggestedBinding(
        action=button_actions['x_click'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/x/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['x_touch'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/x/touch"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['y_click'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/y/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['y_touch'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/y/touch"),
    ),
    
    # 扳机
    xr.ActionSuggestedBinding(
        action=button_actions['trigger'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/trigger/value"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['trigger'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/trigger/value"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['trigger_touch'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/trigger/touch"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['trigger_touch'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/trigger/touch"),
    ),
    
    # 握把
    xr.ActionSuggestedBinding(
        action=button_actions['grip'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/squeeze/value"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['grip'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/squeeze/value"),
    ),
    
    # 摇杆
    xr.ActionSuggestedBinding(
        action=button_actions['thumbstick'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/thumbstick"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['thumbstick'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/thumbstick"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['thumbstick_click'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/thumbstick/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['thumbstick_click'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/thumbstick/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['thumbstick_touch'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/thumbstick/touch"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['thumbstick_touch'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/thumbstick/touch"),
    ),
    
    # 菜单/系统按键
    xr.ActionSuggestedBinding(
        action=button_actions['menu'],
        binding=xr.string_to_path(instance, "/user/hand/left/input/menu/click"),
    ),
    xr.ActionSuggestedBinding(
        action=button_actions['system'],
        binding=xr.string_to_path(instance, "/user/hand/right/input/system/click"),
    ),
]
 
try:
    # 使用 Oculus Touch 控制器交互配置文件
    xr.suggest_interaction_profile_bindings(
        instance=instance,
        suggested_bindings=xr.InteractionProfileSuggestedBinding(
            interaction_profile=xr.string_to_path(instance, "/interaction_profiles/oculus/touch_controller"),
            count_suggested_bindings=len(oculus_bindings),
            suggested_bindings=(xr.ActionSuggestedBinding * len(oculus_bindings))(*oculus_bindings),
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
                        ctypes.POINTER(xr.EventDataSessionStateChanged)).contents
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
                subaction_path=xr.NULL_PATH, # type: ignore
            )
            xr.sync_actions(
                session=session,
                sync_info=xr.ActionsSyncInfo(
                    count_active_action_sets=1,
                    active_action_sets=ctypes.pointer(active_action_set),
                ),
            )
 
# ... existing code ...
            # 读取右手布尔型按键 (A/B)
            try:
                # A键
                a_click_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['a_click']),
                )
                
                a_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['a_touch']),
                )
                
                # B键
                b_click_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['b_click']),
                )
                
                b_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['b_touch']),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["右手A键"] = a_click_state.current_state
                panel_data["右手A键触摸"] = a_touch_state.current_state
                panel_data["右手B键"] = b_click_state.current_state
                panel_data["右手B键触摸"] = b_touch_state.current_state
            except Exception as e:
                pass

            # 读取左手布尔型按键 (X/Y)
            try:
                # X键
                x_click_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['x_click']),
                )
                
                x_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['x_touch']),
                )
                
                # Y键
                y_click_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['y_click']),
                )
                
                y_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['y_touch']),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手X键"] = x_click_state.current_state
                panel_data["左手X键触摸"] = x_touch_state.current_state
                panel_data["左手Y键"] = y_click_state.current_state
                panel_data["左手Y键触摸"] = y_touch_state.current_state
            except Exception as e:
                pass

            # 读取菜单和系统键
            try:
                menu_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['menu']),
                )
                
                system_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(action=button_actions['system']),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手菜单键"] = menu_state.current_state
                panel_data["右手系统键"] = system_state.current_state
            except Exception as e:
                pass

            # 读取扳机触摸
            try:
                left_trigger_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['trigger_touch'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/left"),
                    ),
                )
                
                right_trigger_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['trigger_touch'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/right"),
                    ),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手扳机触摸"] = left_trigger_touch_state.current_state
                panel_data["右手扳机触摸"] = right_trigger_touch_state.current_state
            except Exception as e:
                pass

            # 读取摇杆点击
            try:
                left_thumbstick_click_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['thumbstick_click'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/left"),
                    ),
                )
                
                right_thumbstick_click_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['thumbstick_click'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/right"),
                    ),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手摇杆点击"] = left_thumbstick_click_state.current_state
                panel_data["右手摇杆点击"] = right_thumbstick_click_state.current_state
            except Exception as e:
                pass

            # 读取摇杆触摸
            try:
                left_thumbstick_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['thumbstick_touch'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/left"),
                    ),
                )
                
                right_thumbstick_touch_state = xr.get_action_state_boolean(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['thumbstick_touch'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/right"),
                    ),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手摇杆触摸"] = left_thumbstick_touch_state.current_state
                panel_data["右手摇杆触摸"] = right_thumbstick_touch_state.current_state
            except Exception as e:
                pass

            # 读取浮点型输入 (扳机和握把)
            try:
                # 左手扳机
                left_trigger_state = xr.get_action_state_float(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['trigger'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/left"),
                    ),
                )
                
                # 右手扳机
                right_trigger_state = xr.get_action_state_float(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['trigger'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/right"),
                    ),
                )
                
                # 左手握把
                left_grip_state = xr.get_action_state_float(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['grip'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/left"),
                    ),
                )
                
                # 右手握把
                right_grip_state = xr.get_action_state_float(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=button_actions['grip'],
                        subaction_path=xr.string_to_path(instance, "/user/hand/right"),
                    ),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手扳机"] = f"{left_trigger_state.current_state}"
                panel_data["右手扳机"] = f"{right_trigger_state.current_state}"
                panel_data["左手握把"] = f"{left_grip_state.current_state}"
                panel_data["右手握把"] = f"{right_grip_state.current_state}"
            except Exception as e:
                pass

            # 读取摇杆输入 (2D向量)
            try:
                thumbstick_action = button_actions['thumbstick']
                # 一次性读取左右手摇杆数据
                left_state = xr.get_action_state_vector2f(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=thumbstick_action,
                        subaction_path=xr.string_to_path(instance, "/user/hand/left"),
                    ),
                )
                
                right_state = xr.get_action_state_vector2f(
                    session=session,
                    get_info=xr.ActionStateGetInfo(
                        action=thumbstick_action,
                        subaction_path=xr.string_to_path(instance, "/user/hand/right"),
                    ),
                )
                
                # 在try块最后统一更新panel_data
                panel_data["左手摇杆X"] = f"{left_state.current_state.x:.2f}"
                panel_data["左手摇杆Y"] = f"{left_state.current_state.y:.2f}"
                panel_data["右手摇杆X"] = f"{right_state.current_state.x:.2f}"
                panel_data["右手摇杆Y"] = f"{right_state.current_state.y:.2f}"
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