# stdlib
from types import FunctionType

# pyramid
from pyramid.decorator import reify
from pyramid.interfaces import IDict
from pyramid.exceptions import ConfigurationError
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Attribute


# ==============================================================================


__VERSION__ = "0.3.1"


# ------------------------------------------------------------------------------


class UnregisteredSession(KeyError):
    """raised when an unregistered session is attempted access"""

    pass


class _SessionDiscriminated(Exception):
    """internal use only; raised when a session should not issue for a request"""

    pass


class ISessionMultiManagerConfig(Interface):
    """
    An interface representing a factory which accepts a `config` instance and
    returns an ISessionMultiManagerConfig compliant object. There should be one
    and only one ISessionMultiManagerConfig per application.
    """

    def register_session_factory(
        self, namespace, session_factory, discriminator=None, cookie_name=None
    ):
        """
        Register an ISessionFactory compliant factory.

        :param namespace:
            The namespace within `request.session_multi[]` for the session
        :param session_factory:
            an ISession compatible factory
        :param discriminator:
            a discriminator function to run on the request.
            The discriminator should accept a request and return `True` (pass)
            or `False`/`None` (fail).
            If the discriminator fails, the namespace in `request.session_multi`
            will be set to `None`.
            If the discriminator passes, the namespace in `request.session_multi`
            will be the output of `factory(request)`
        :param cookie_name: stashed as `_cookie_name`
        """

    discriminators = Attribute("""list all namespaces with discriminators""")

    namespaces = Attribute("""list all possible namespaces""")

    namespaces_to_cookienames = Attribute("""dict of namespaces to cookienames""")

    def has_namespace(self, namespace):
        """is this a valid namespace/session?"""

    def get_namespace_config(self, namespace):
        """is this a valid namespace/session?"""

    def get_namespace_cookiename(self, namespace):
        """get the namespace cookiename"""

    def get_namespace_discriminator(self, namespace):
        """get the namespace discriminator"""


@implementer(ISessionMultiManagerConfig)
class SessionMultiManagerConfig(object):
    """
    This is the core configuration object.
    It is built up during the pyramid app configuration phase.
    It is used to create new managers on each request.
    """

    def __init__(self, config):
        self._session_factories = {}
        self._discriminators = {}
        self._cookienames = {}

    def register_session_factory(
        self, namespace, session_factory, discriminator=None, cookie_name=None
    ):
        """
        See `ISessionMultiManagerConfig.register_session_factory` for docs
        """
        if not all((namespace, session_factory)):
            raise ConfigurationError("must register namespace and session_factory")
        if namespace in self._session_factories.keys():
            raise ConfigurationError(
                "namespace `%s` already registered to pyramid_session_multi" % namespace
            )
        if session_factory in self._session_factories.values():
            raise ConfigurationError(
                "session_factory `%s` (%s) already registered another namespace"
                % (session_factory, namespace)
            )
        if cookie_name is None:
            if hasattr(session_factory, "_cookie_name"):
                cookie_name = session_factory._cookie_name
        if not cookie_name:
            raise ConfigurationError(
                "session_factory `%s` does not have a cookie_name" % (session_factory,)
            )
        if cookie_name in self._cookienames.values():
            raise ConfigurationError(
                "session_factory `%s` (%s) already registered another cookie"
                % (session_factory, cookie_name)
            )

        self._cookienames[namespace] = cookie_name
        self._session_factories[namespace] = session_factory
        if discriminator:
            self._discriminators[namespace] = discriminator
        return True

    @property
    def discriminators(self):
        """list all namespaces with discriminators"""
        return list(self._discriminators.keys())

    @property
    def namespaces(self):
        """list all possible namespaces"""
        return list(self._session_factories.keys())

    @property
    def namespaces_to_cookienames(self):
        """dict of namespaces to cookienames"""
        return dict(self._cookienames)

    def has_namespace(self, namespace):
        """is this a valid namespace/session?"""
        return True if namespace in self._session_factories else False

    def get_namespace_config(self, namespace):
        """get the namespace config"""
        return self._session_factories.get(namespace, None)

    def get_namespace_cookiename(self, namespace):
        """get the namespace cookiename"""
        return self._cookienames.get(namespace, None)

    def get_namespace_discriminator(self, namespace):
        """get the namespace discriminator"""
        return self._discriminators.get(namespace, None)


@implementer(IDict)
class SessionMultiManager(dict):
    """
    This is the per-request multiple session interface.
    It is mounted onto the request, and creates ad-hoc sessions on the
    mountpoints as needed.
    """

    def __init__(self, request):
        self.request = request
        manager_config = request.registry.queryUtility(ISessionMultiManagerConfig)
        if manager_config is None:
            raise AttributeError("No session multi manager registered")
        self._manager_config = manager_config

    def _discriminated_session(self, namespace):
        """
        private method. this was part of __get_item__ but was pulled out
        for the debugging panel
        """
        _session = None
        try:
            _discriminator = self._manager_config._discriminators.get(namespace)
            if _discriminator:
                if not _discriminator(self.request):
                    raise _SessionDiscriminated()
            _session = self._manager_config._session_factories[namespace](self.request)
        except _SessionDiscriminated:
            pass
        return _session

    def __getitem__(self, namespace):
        """
        Return the value for key ``namespace`` from the dictionary or raise a
        KeyError if the key doesn't exist
        """
        if namespace not in self:
            if namespace in self._manager_config._session_factories:
                session = self._discriminated_session(namespace)
                dict.__setitem__(self, namespace, session)
                return session
        try:
            session = dict.__getitem__(self, namespace)
            if isinstance(session, FunctionType):
                # this can happen if the debugtoolbar panel wraps the session
                session = session()
                dict.__setitem__(self, namespace, session)
            return session
        except KeyError as exc:
            raise UnregisteredSession("'%s' is not a valid session" % namespace)

    #
    # turn off some public methods
    #

    def __setitem__(self, namespace, value):
        raise ValueError("May not `set` on a `SessionMultiManager`")

    def __delitem__(self, namespace):
        raise ValueError("May not `del` on a `SessionMultiManager`")

    @reify
    def discriminators(self):
        """list all namespaces with discriminators"""
        return self._manager_config.discriminators

    @reify
    def namespaces_to_cookienames(self):
        """dict of namespaces to cookienames"""
        return self._manager_config.namespaces_to_cookienames

    @reify
    def namespaces(self):
        """list all possible namespaces"""
        return self._manager_config.namespaces

    def has_namespace(self, namespace):
        """is this a valid namespace/session?"""
        return self._manager_config.has_namespace(namespace)

    def get_namespace_config(self, namespace):
        """get the namespace config"""
        return self._manager_config.get_namespace(namespace)

    def get_namespace_cookiename(self, namespace):
        """get the namespace cookiename"""
        return self._manager_config.get_namespace_cookiename(namespace)

    def get_namespace_discriminator(self, namespace):
        """get the namespace discriminator"""
        return self._manager_config.get_discriminator(namespace)

    def invalidate(self):
        """invalidate all possible namespaces"""
        for namespace in self.namespaces:
            self[namespace].invalidate()


def new_session_multi(request):
    """
    this is turned into a reified request property
    """
    manager = SessionMultiManager(request)
    return manager


def register_session_factory(
    config, namespace, session_factory, discriminator=None, cookie_name=None
):
    manager_config = config.registry.queryUtility(ISessionMultiManagerConfig)
    if manager_config is None:
        raise AttributeError("No session multi manager registered")
    manager_config.register_session_factory(
        namespace, session_factory, discriminator=discriminator, cookie_name=cookie_name
    )


def includeme(config):
    # Step 1 - set up a ``SessionMultiManagerConfig``
    manager_config = SessionMultiManagerConfig(config)
    config.registry.registerUtility(manager_config, ISessionMultiManagerConfig)

    # Step 2 - setup custom `session_managed` property
    config.add_request_method(new_session_multi, "session_multi", reify=True)
