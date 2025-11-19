import ctypes
import xr


class XRSystem:
    """管理 instance / system / session / state"""

    def __init__(self, extensions):
        self.instance = xr.create_instance(
            xr.InstanceCreateInfo(enabled_extension_names=extensions)
        )
        self.system = xr.get_system(
            self.instance,
            xr.SystemGetInfo(form_factor=xr.FormFactor.HEAD_MOUNTED_DISPLAY),
        )
        self.session = xr.create_session(
            self.instance,
            xr.SessionCreateInfo(system_id=self.system)
        )
        self.state = xr.SessionState.UNKNOWN

    def poll_events(self):
        """事件轮询 + 自动状态管理"""
        while True:
            try:
                evbuf = xr.poll_event(self.instance)
            except xr.EventUnavailable:
                break

            etype = xr.StructureType(evbuf.type)

            if etype == xr.StructureType.EVENT_DATA_SESSION_STATE_CHANGED:
                event = ctypes.cast(
                    ctypes.byref(evbuf),
                    ctypes.POINTER(xr.EventDataSessionStateChanged)
                ).contents

                self.state = xr.SessionState(event.state)

                if self.state == xr.SessionState.READY:
                    xr.begin_session(
                        self.session,
                        xr.SessionBeginInfo(
                            primary_view_configuration_type=xr.ViewConfigurationType.PRIMARY_MONO
                        ),
                    )
                elif self.state == xr.SessionState.STOPPING:
                    xr.end_session(self.session)
