from .panels.session_multi import SessionMultiDebugPanel

def includeme(config):
    """
    Pyramid API hook
    """
    config.registry.settings['debugtoolbar.panels'].append(SessionMultiDebugPanel)

    if 'mako.directories' not in config.registry.settings:
        config.registry.settings['mako.directories'] = []
