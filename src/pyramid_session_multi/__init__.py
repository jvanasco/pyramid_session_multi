# stdlib
from types import FunctionType
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import TYPE_CHECKING

# pypi
from pyramid.decorator import reify
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import IDict
from pyramid.interfaces import ISession
from zope.interface import Attribute
from zope.interface import implementer
from zope.interface import Interface

# typing
if TYPE_CHECKING:
    from pyramid.config import Configurator
    from pyramid.request import Request

# ==============================================================================


__VERSION__ = "0.4.0dev"


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
    returns an ISessionMultiManagerConfig compliant object.
    There should be one and only one ISessionMultiManagerConfig per application.
    """

    def register_session_factory(
        self,
        namespace: str,
        session_factory: Callable,
        discriminator: Optional[Callable] = None,
        cookie_name: Optional[str] = None,
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

    discriminators = Attribute(
        """list all namespaces with discriminators""" """:returns: list of strings"""
    )

    namespaces = Attribute(
        """list all possible namespaces""" """:returns: list of strings"""
    )

    namespaces_to_cookienames = Attribute(
        """dict of namespaces to cookienames""" """:returns: dict"""
    )

    def has_namespace(self, namespace: str):
        """
        is this a valid namespace/session?
        :returns: bool
        """

    def get_namespace_config(self, namespace: str):
        """
        is this a valid namespace/session?
        :returns: a session factory or None
        """

    def get_namespace_cookiename(self, namespace: str):
        """
        get the namespace cookiename
        :returns: str or None
        """

    def get_namespace_discriminator(self, namespace: str):
        """
        get the namespace discriminator
        :returns: str or None
        """


@implementer(ISessionMultiManagerConfig)
class SessionMultiManagerConfig(object):
    """
    This is the core configuration object.
    It is built up during the pyramid app configuration phase.
    It is used to create new managers on each request.
    """

    def __init__(self, config: "Configurator"):
        self._session_factories: Dict[str, Callable] = {}
        self._discriminators: Dict[str, Callable] = {}
        self._cookienames: Dict[str, str] = {}

    def register_session_factory(
        self,
        namespace: str,
        session_factory: Callable,
        discriminator: Optional[Callable] = None,
        cookie_name: Optional[str] = None,
    ) -> bool:
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
    def discriminators(self) -> Iterable[str]:
        """list all namespaces with discriminators"""
        return list(self._discriminators.keys())

    @property
    def namespaces(self) -> Iterable[str]:
        """list all possible namespaces"""
        return list(self._session_factories.keys())

    @property
    def namespaces_to_cookienames(self) -> Dict[str, str]:
        """dict of namespaces to cookienames"""
        return dict(self._cookienames)

    def has_namespace(self, namespace: str) -> bool:
        """is this a valid namespace/session?"""
        return True if namespace in self._session_factories else False

    # got      "Union[Callable[..., Any], Dict[str, Callable[..., Any]], None]"
    # expected "Optional[Dict[str, Callable[..., Any]]]"
    # expected "Union[                    Dict[str, Callable[..., Any]], None]"

    def get_namespace_config(self, namespace: str) -> Optional[Callable]:
        """get the namespace config"""
        return self._session_factories.get(namespace, None)

    def get_namespace_cookiename(self, namespace: str) -> Optional[str]:
        """get the namespace cookiename"""
        return self._cookienames.get(namespace, None)

    def get_namespace_discriminator(self, namespace: str) -> Optional[Callable]:
        """get the namespace discriminator"""
        return self._discriminators.get(namespace, None)


@implementer(IDict)
class SessionMultiManager(dict):
    """
    This is the per-request multiple session interface.
    It is mounted onto the request, and creates ad-hoc sessions on the
    mountpoints as needed.
    """

    def __init__(self, request: "Request"):
        self.request = request
        manager_config = request.registry.queryUtility(ISessionMultiManagerConfig)
        if manager_config is None:
            raise AttributeError("No session multi manager registered")
        self._manager_config = manager_config

    def _discriminated_session(self, namespace: str) -> ISession:
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

    def __getitem__(self, namespace: str) -> ISession:
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
        except KeyError as exc:  # noqa: F841
            raise UnregisteredSession("'%s' is not a valid session" % namespace)

    #
    # turn off some public methods
    #

    def __setitem__(self, namespace: str, value: Any):
        raise ValueError("May not `set` on a `SessionMultiManager`")

    def __delitem__(self, namespace: str):
        raise ValueError("May not `del` on a `SessionMultiManager`")

    @reify
    def discriminators(self) -> List[Callable]:
        """list all namespaces with discriminators"""
        return self._manager_config.discriminators

    @reify
    def namespaces_to_cookienames(self) -> Dict[str, str]:
        """dict of namespaces to cookienames"""
        return self._manager_config.namespaces_to_cookienames

    @reify
    def namespaces(self) -> List[str]:
        """list all possible namespaces"""
        return self._manager_config.namespaces

    def has_namespace(self, namespace: str) -> bool:
        """is this a valid namespace/session?"""
        return self._manager_config.has_namespace(namespace)

    def get_namespace_config(self, namespace: str) -> Optional[Callable]:
        """get the namespace config"""
        return self._manager_config.get_namespace(namespace)

    def get_namespace_cookiename(self, namespace: str) -> Optional[str]:
        """get the namespace cookiename"""
        return self._manager_config.get_namespace_cookiename(namespace)

    def get_namespace_discriminator(self, namespace: str) -> Optional[Callable]:
        """get the namespace discriminator"""
        return self._manager_config.get_discriminator(namespace)

    def invalidate(self) -> None:
        """invalidate all possible namespaces"""
        for namespace in self.namespaces:
            self[namespace].invalidate()


def new_session_multi(request: "Request") -> SessionMultiManager:
    """
    this is turned into a reified request property
    """
    manager = SessionMultiManager(request)
    return manager


def register_session_factory(
    config: "Configurator",
    namespace: str,
    session_factory: Callable,
    discriminator: Optional[Callable] = None,
    cookie_name: Optional[str] = None,
) -> None:
    manager_config = config.registry.queryUtility(ISessionMultiManagerConfig)
    if manager_config is None:
        raise AttributeError("No session multi manager registered")
    manager_config.register_session_factory(
        namespace, session_factory, discriminator=discriminator, cookie_name=cookie_name
    )


def includeme(config: "Configurator") -> None:
    # Step 1 - set up a ``SessionMultiManagerConfig``
    manager_config = SessionMultiManagerConfig(config)
    config.registry.registerUtility(manager_config, ISessionMultiManagerConfig)

    # Step 2 - setup custom `session_managed` property
    config.add_request_method(new_session_multi, "session_multi", reify=True)
