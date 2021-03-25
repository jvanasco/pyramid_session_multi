# stdlib
from types import FunctionType

# pyramid
from pyramid_debugtoolbar.panels import DebugPanel

# from pyramid_debugtoolbar.utils import dictrepr
import zope.interface.interfaces

# local
from ... import ISessionMultiManagerConfig


# ==============================================================================


def dictrepr(d):
    """
    a sort-safe version of pyramid_debugtoolbar.utils.dictrepr`
        from pyramid_debugtoolbar.utils import dictrepr

    consider migrating to the upstream library when fixed
    this will require version pinning.
    """
    out = {}
    for val in d:
        try:
            out[val] = repr(d[val])
        except Exception:
            # defensive
            out[val] = "<unknown>"
    try:
        return sorted(out.items())
    except TypeError:
        return sorted(out.items(), key=lambda k: str(k))


_ = lambda x: x


class NotInSession(object):
    pass


class SessionMultiDebugPanel(DebugPanel):
    """
    A panel to display the ``ISessionMulti`` data.
    """

    name = "session_multi"
    template = (
        "pyramid_session_multi.debugtoolbar.panels:templates/session_multi.dbtmako"
    )
    title = _("SessionMulti")
    nav_title = title
    user_activate = True

    @property
    def has_content(self):
        """
        This is too difficult to figure out under the following parameters:

        * Do not trigger the ``ISession`` interface.
        * The toolbar consults this attibute relatively early in the lifecycle
          to determine if ``.is_active`` should be ``True``.
        """
        return True

    # used to store the Request for processing
    _request = None

    def __init__(self, request):
        """
        Initial setup of the `data` payload.
        """

        self.data = data = {
            "configuration": None,
            "is_active": None,  # not known on `.__init__`
            "NotInSession": NotInSession,
            "session_multi_accessed": {
                "pre": None,  # pre-processing (toolbar)
                "panel_setup": None,  # during the panel setup?
                "main": None,  # during Request processing
            },
            "session_accessed": {},
            "session_data": {},
        }

        # we need this for processing in the response phase
        self._request = request
        # try to stash the configuration info
        try:
            config = request.registry.getUtility(ISessionMultiManagerConfig)
            data["configuration"] = {
                "config": config,
                "cookies": {},
                "discriminators": {},
                "namespaces": {},
            }
            for namespace in config.namespaces:
                data["configuration"]["cookies"][
                    namespace
                ] = config.get_namespace_cookiename(namespace)
                data["configuration"]["discriminators"][
                    namespace
                ] = config.get_namespace_discriminator(namespace)
                data["configuration"]["namespaces"][
                    namespace
                ] = config.get_namespace_config(namespace)
                data["session_accessed"][namespace] = {
                    "pre": None,  # pre-processing (toolbar)
                    "panel_setup": None,  # during the panel setup?
                    "main": None,  # during Request processing
                    "discriminator_fail": None,  # True if discriminator_fail
                }
                data["session_data"][namespace] = {
                    "ingress": {},  # in
                    "egress": {},  # out
                    "keys": set([]),
                    "changed": set([]),
                }

        except zope.interface.interfaces.ComponentLookupError:
            # the `ISessionFactory` is not configured
            pass

    def wrap_handler(self, handler):
        """
        ``wrap_handler`` allows us to monitor the entire lifecycle of
        the  ``Request``.

        Instead of using this hook to create a new wrapped handler, we can just
        do the required analysis right here, and then invoke the original
        handler.

        Request | "ingress"
        Pre-process the ``Request`` if the panel is active, or if the
        ``Session`` has already been accessed, as the ``Request`` requires
        activating the ``Session`` interface.
        If pre-processing does not happen, the ``.session_multi`` property will
        be replaced with a wrapped function which will invoke the ingress
        processing if the session is accessed.
        """
        data = self.data

        def _process_namespace(_namespace, _session):
            # helper function
            # a discriminator could return None for the session
            if _session is not None:
                for k, v in dictrepr(_session):
                    data["session_data"][_namespace]["ingress"][k] = v
                    data["session_data"][_namespace]["keys"].add(k)

        # define a wrapper for this session
        def new_wrapper_a(_namespace, _session):

            if _session is None:
                data["session_accessed"][_namespace]["discriminator_fail"] = True

            def session_wrapper():
                data["session_accessed"][_namespace]["main"] = True
                return _session

            return session_wrapper

        def new_wrapper_b(_namespace):
            def session_wrapper():
                # get the session
                _session = session_multi._discriminated_session(_namespace)

                if _session is None:
                    data["session_accessed"][_namespace]["discriminator_fail"] = True

                # process the inbound session data
                _process_namespace(_namespace, _session)
                # note the session was accessed during the main request
                data["session_accessed"][_namespace]["main"] = True
                return _session

            return session_wrapper

        # -- main logic --

        if self.is_active:
            # not known on `.__init__` due to the toolbar's design.
            # no problem, it can be updated on `.wrap_handler`
            data["is_active"] = True

        if "session_multi" in self._request.__dict__:
            # mark the ``SessionMulti`` as already accessed.
            # This can only happen if:
            #   * The ``.session_multi``` was accessed by another panel or higher tween
            data["session_multi_accessed"]["pre"] = True

        session_multi = None
        try:
            session_multi = self._request.session_multi
        except AttributeError:
            # the session_multi is not configured
            pass

        if session_multi is not None:
            for namespace in session_multi.namespaces:
                if (namespace in session_multi) or self.is_active:
                    if namespace in session_multi:
                        # mark the namespace as previously accessed
                        data["session_accessed"][namespace]["pre"] = True
                    else:
                        if self.is_active:
                            # mark the namespace as accessed here
                            data["session_accessed"][namespace]["panel_setup"] = True

                    # grab the session
                    # if not already loaded, it will become loaded
                    session = session_multi[namespace]

                    # process it
                    _process_namespace(namespace, session)

                    # delete it from the session_multi
                    dict.__delitem__(session_multi, namespace)

                    # generate a new wrapper
                    session_wrapper = new_wrapper_a(namespace, session)

                    # replace the namespaced session
                    dict.__setitem__(session_multi, namespace, session_wrapper)

                else:

                    # generate a new wrapper
                    session_wrapper = new_wrapper_b(namespace)

                    # Replace the existing ``ISession`` interface with our wrapper.
                    dict.__setitem__(session_multi, namespace, session_wrapper)

        return handler

    def process_response(self, response):
        """
        ``Response`` | "egress"

        Only process the ``Response``` if the panel is active OR if the
        session was accessed, as processing the ``Response`` requires
        opening the session.
        """
        if self._request is None:
            # this scenario can happen if there is an error in the toolbar
            return

        data = self.data
        session_multi = None

        def _process_namespace(_namespace, _session):
            # helper function
            # a discriminator could return None for the session
            if _session is not None:
                for k, v in dictrepr(_session):
                    data["session_data"][_namespace]["egress"][k] = v
                    data["session_data"][_namespace]["keys"].add(k)

                    if (k not in data["session_data"][_namespace]["ingress"]) or (
                        data["session_data"][_namespace]["ingress"][k] != v
                    ):
                        data["session_data"][_namespace]["changed"].add(k)

        if self.is_active or ("session_multi" in self._request.__dict__):
            try:
                # if we installed a wrapped load, accessing the session now
                # will trigger the "main" marker. to handle this, check the
                # current version of the marker then access the session
                # and then reset the marker
                _accessed_main = data["session_multi_accessed"]["main"]
                session_multi = self._request.session_multi
            except AttributeError:
                # the session_multi is not configured
                pass

            if session_multi is not None:
                data["session_multi_accessed"]["main"] = _accessed_main

                for (namespace, session) in session_multi.items():

                    if isinstance(session, FunctionType):
                        # skip wrapped loaders on egress if we haven't touched
                        # them yet
                        if not self.is_active:
                            continue

                    # accessing the session will grab it
                    _accessed_ns = data["session_accessed"][namespace]["main"]

                    # grab the session
                    # which can instantiate a session and affect 'accessed'
                    session = session_multi[namespace]

                    # process it
                    _process_namespace(namespace, session)

                    # move this value back in
                    data["session_accessed"][namespace]["main"] = _accessed_ns
