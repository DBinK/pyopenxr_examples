import xr


class XRButtonActions:
    """
    管理所有手柄按键（Boolean / Float / Vector2）
    """

    def __init__(self, instance, action_set):
        self.instance = instance
        self.action_set = action_set

        # ------ 创建 Actions ------
        self.trigger = self._make_float_action("trigger")
        self.grip = self._make_float_action("grip")
        self.a_click = self._make_bool_action("a_click")
        self.b_click = self._make_bool_action("b_click")
        self.thumbstick = self._make_vec2_action("thumbstick")

        # ------ 绑定路径 ------
        self._bind_oculus_touch()

    # -------------------- 工具：创建 action --------------------

    def _make_bool_action(self, name):
        return xr.create_action(
            action_set=self.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.BOOLEAN_INPUT,
                action_name=name,
                localized_action_name=name,
            ),
        )

    def _make_float_action(self, name):
        return xr.create_action(
            action_set=self.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.FLOAT_INPUT,
                action_name=name,
                localized_action_name=name,
            ),
        )

    def _make_vec2_action(self, name):
        return xr.create_action(
            action_set=self.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.VECTOR2F_INPUT,
                action_name=name,
                localized_action_name=name,
            ),
        )

    # -------------------- 绑定 Oculus Touch --------------------

    def _bind_oculus_touch(self):
        binds = []

        # ------ Trigger 扳机 ------
        binds.append(self._binding(self.trigger, "/user/hand/right/input/trigger/value"))
        binds.append(self._binding(self.trigger, "/user/hand/left/input/trigger/value"))

        # ------ Grip 扳机 ------
        binds.append(self._binding(self.grip, "/user/hand/right/input/squeeze/value"))
        binds.append(self._binding(self.grip, "/user/hand/left/input/squeeze/value"))

        # ------ A/B 按钮 ------
        binds.append(self._binding(self.a_click, "/user/hand/right/input/a/click"))
        binds.append(self._binding(self.b_click, "/user/hand/right/input/b/click"))

        # ------ 摇杆（vector2） ------
        binds.append(self._binding(self.thumbstick, "/user/hand/right/input/thumbstick"))

        xr.suggest_interaction_profile_bindings(
            instance=self.instance,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance,
                    "/interaction_profiles/oculus/touch_controller",
                ),
                count_suggested_bindings=len(binds),
                suggested_bindings=(xr.ActionSuggestedBinding * len(binds))(*binds),
            ),
        )

    def _binding(self, action, path):
        return xr.ActionSuggestedBinding(
            action=action,
            binding=xr.string_to_path(self.instance, path),
        )
