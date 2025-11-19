import xr


class XRControllerTracker:
    """负责 locate_space"""

    def __init__(self, actions, time_provider):
        self.actions = actions
        self.time = time_provider

    def poll(self):
        xr.sync_actions(
            session=self.actions.session,
            sync_info=xr.ActionsSyncInfo(
                active_action_sets=[self.actions.active_set]
            ),
        )

        now = self.time.now()
        poses = []

        for space in self.actions.spaces:
            loc = xr.locate_space(
                space=space,
                base_space=self.actions.ref_space,
                time=now,
            )
            if loc.location_flags & xr.SPACE_LOCATION_POSITION_VALID_BIT:
                poses.append(loc.pose)
            else:
                poses.append(None)

        return poses  # [left_pose, right_pose]
