from .panels.session_multi import SessionMultiDebugPanel


def includeme(config):
    """
    Pyramid API hook
    """
    config.add_debugtoolbar_panel(SessionMultiDebugPanel)
