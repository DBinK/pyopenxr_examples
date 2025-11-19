import xr
import ctypes


class XRControllerActions:
    """ActionSet、ActionSpace、绑定、ReferenceSpace"""

    def __init__(self, instance, session):
        self.instance = instance
        self.session = session

        self.action_set = self._make_action_set()
        self.paths = self._make_paths()
        self.pose_action = self._make_pose_action()

        self._bind_oculus_touch()
        self._attach()

        self.spaces = self._make_spaces()
        self.ref_space = self._make_ref_space()

        self.active_set = xr.ActiveActionSet(
            action_set=self.action_set,
            subaction_path=xr.NULL_PATH, # type: ignore
        )

    def _make_action_set(self):
        return xr.create_action_set(
            instance=self.instance,
            create_info=xr.ActionSetCreateInfo(
                action_set_name="controller_set",
                localized_action_set_name="Controller Set",
                priority=0,
            ),
        )

    def _make_paths(self):
        return [
            xr.string_to_path(self.instance, "/user/hand/left"),
            xr.string_to_path(self.instance, "/user/hand/right"),
        ]

    def _make_pose_action(self):
        return xr.create_action(
            action_set=self.action_set,
            create_info=xr.ActionCreateInfo(
                action_type=xr.ActionType.POSE_INPUT,
                action_name="hand_pose",
                localized_action_name="Hand Pose",
                count_subaction_paths=2,
                subaction_paths=(xr.Path * 2)(*self.paths),
            )
        )

    def _bind_oculus_touch(self):
        binds = []
        for side in ["left", "right"]:
            binds.append(
                xr.ActionSuggestedBinding(
                    action=self.pose_action,
                    binding=xr.string_to_path(
                        self.instance,
                        f"/user/hand/{side}/input/grip/pose",
                    ),
                )
            )

        xr.suggest_interaction_profile_bindings(
            instance=self.instance,
            suggested_bindings=xr.InteractionProfileSuggestedBinding(
                interaction_profile=xr.string_to_path(
                    self.instance,
                    "/interaction_profiles/oculus/touch_controller",
                ),
                count_suggested_bindings=2,
                suggested_bindings=(xr.ActionSuggestedBinding * 2)(*binds),
            ),
        )

    def _attach(self):
        xr.attach_session_action_sets(
            session=self.session,
            attach_info=xr.SessionActionSetsAttachInfo(action_sets=[self.action_set]),
        )

    def _make_spaces(self):
        return [
            xr.create_action_space(
                session=self.session,
                create_info=xr.ActionSpaceCreateInfo(
                    action=self.pose_action,
                    subaction_path=self.paths[0],
                ),
            ),
            xr.create_action_space(
                session=self.session,
                create_info=xr.ActionSpaceCreateInfo(
                    action=self.pose_action,
                    subaction_path=self.paths[1],
                ),
            ),
        ]

    def _make_ref_space(self):
        return xr.create_reference_space(
            session=self.session,
            create_info=xr.ReferenceSpaceCreateInfo(
                reference_space_type=xr.ReferenceSpaceType.STAGE
            ),
        )
