from pyramid_debugtoolbar.panels import DebugPanel

_ = lambda x: x


class SessionMultiDebugPanel(DebugPanel):
    """
    Sample debug panel
    """

    name = "SessionMulti"
    has_content = True
    template = (
        "pyramid_session_multi.debugtoolbar.panels:templates/session_multi.dbtmako"
    )

    # used to store the request for response processing
    __request = None

    def __init__(self, request):

        self.data = {
            "configuration": None,
            "session_data": {"namespaces": [], "in": {}, "out": {}},
        }

        if hasattr(request, "session_multi"):
            namespace_2_discriminator = {
                k: None for k in request.session_multi.namespaces
            }
            discriminators = {k: True for k in request.session_multi.discriminators}
            namespace_2_discriminator.update(discriminators)

            # turn this into a list...
            configuration = []
            for (namespace, discriminator) in namespace_2_discriminator.items():
                config = [
                    namespace,
                    request.session_multi._manager_config._cookienames.get(namespace),
                    discriminator,
                ]
                factory_info = request.session_multi._manager_config._session_factories[
                    namespace
                ]
                config.append(factory_info)
                configuration.append(config)

            # this collects all the incoming data without binding to the request
            session_data__in = request.session_multi._debug_incoming()
            self.data["configuration"] = configuration
            self.data["session_data"]["namespaces"] = request.session_multi.namespaces
            self.data["session_data"]["in"] = session_data__in

        # we need this for processing in the response phase
        self.__request = request

    def process_response(self, response):

        # this bit handles the session_multi stuff
        if hasattr(self.__request, "session_multi"):
            session_multi__out = dict(self.__request.session_multi.items())
            self.data["session_data"]["out"] = session_multi__out

    @property
    def nav_title(self):
        return _(self.name)

    @property
    def title(self):
        return _(self.name)

    @property
    def url(self):
        return ""

    def render_content(self, request):
        return DebugPanel.render_content(self, request)
