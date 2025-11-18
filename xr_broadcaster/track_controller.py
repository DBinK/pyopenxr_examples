"""
pyopenxr example program track_controller_quest3.py

在 Meta Quest 3 上打印左右手控制器的位置，共 30 帧。
"""
from rich import print
import ctypes
import time
import xr
from xr.utils.gl import ContextObject
from xr.utils.gl.glfw_util import GLFWOffscreenContextProvider


# ContextObject 是一个高层封装，用来简化常见的 OpenXR 使用场景
with ContextObject(
    context_provider=GLFWOffscreenContextProvider(),
    instance_create_info=xr.InstanceCreateInfo(
        enabled_extension_names=[
            # 必须启用图形相关的扩展（这里用 OpenGL）
            xr.KHR_OPENGL_ENABLE_EXTENSION_NAME,
        ],
    ),
) as context:
    # 设置左右手控制器的路径
    controller_paths = (xr.Path * 2)(  # noqa
        xr.string_to_path(context.instance, "/user/hand/left"),
        xr.string_to_path(context.instance, "/user/hand/right"),
    )

    # 创建用于手柄姿态（位姿）的 Action
    controller_pose_action = xr.create_action(
        action_set=context.default_action_set,
        create_info=xr.ActionCreateInfo(
            action_type=xr.ActionType.POSE_INPUT,
            action_name="hand_pose",
            localized_action_name="Hand Pose",
            count_subaction_paths=len(controller_paths),
            subaction_paths=controller_paths,
        ),
    )

    # 为左右手创建 pose 绑定（这里使用 grip pose）
    suggested_bindings = (xr.ActionSuggestedBinding * 2)(
        xr.ActionSuggestedBinding(
            action=controller_pose_action,
            binding=xr.string_to_path(
                instance=context.instance,
                path_string="/user/hand/left/input/grip/pose",
            ),
        ),
        xr.ActionSuggestedBinding(
            action=controller_pose_action,
            binding=xr.string_to_path(
                instance=context.instance,
                path_string="/user/hand/right/input/grip/pose",
            ),
        ),
    )

    # 只为 Quest 系列使用的 Oculus Touch 控制器 profile 提供绑定
    xr.suggest_interaction_profile_bindings(
        instance=context.instance,
        suggested_bindings=xr.InteractionProfileSuggestedBinding(
            interaction_profile=xr.string_to_path(
                context.instance,
                "/interaction_profiles/oculus/touch_controller",
            ),
            count_suggested_bindings=len(suggested_bindings),
            suggested_bindings=suggested_bindings,
        ),
    )

    # 为左右手创建 Action Space（用来查询位姿）
    action_spaces = [
        xr.create_action_space(
            session=context.session,
            create_info=xr.ActionSpaceCreateInfo(
                action=controller_pose_action,
                subaction_path=controller_paths[0],  # 左手
            ),
        ),
        xr.create_action_space(
            session=context.session,
            create_info=xr.ActionSpaceCreateInfo(
                action=controller_pose_action,
                subaction_path=controller_paths[1],  # 右手
            ),
        ),
    ]

    # 渲染帧循环
    session_was_focused = False  # 检查是否进入过 FOCUSED 状态
    for frame_index, frame_state in enumerate(context.frame_loop()):
        if context.session_state == xr.SessionState.FOCUSED:
            # 会话已经处于 FOCUSED，可以同步输入
            session_was_focused = True

            active_action_set = xr.ActiveActionSet(
                action_set=context.default_action_set,
                subaction_path=xr.NULL_PATH,
            )

            # 同步输入 action
            xr.sync_actions(
                session=context.session,
                sync_info=xr.ActionsSyncInfo(
                    count_active_action_sets=1,
                    active_action_sets=ctypes.pointer(active_action_set),
                ),
            )

            found_count = 0
            for index, space in enumerate(action_spaces):
                space_location = xr.locate_space(
                    space=space,
                    base_space=context.space,
                    time=frame_state.predicted_display_time,
                )

                # 如果当前手柄的位置信息有效，就打印出来
                if space_location.location_flags & xr.SPACE_LOCATION_POSITION_VALID_BIT:
                    # index 0 = 左手，1 = 右手，这里打印成 1、2
                    if index == 0:
                        print(index + 1, space_location.pose)
                        found_count += 1

            if found_count == 0:
                print("no controllers active")

        # 放慢一点，反正也不真的渲染画面
        time.sleep(0.005)

        # 只跑 30 帧就退出
        if frame_index >= 3000:
            break

    if not session_was_focused:
        print(
            "This OpenXR session never entered the FOCUSED state. "
            "Did you wear the headset?"
        )
