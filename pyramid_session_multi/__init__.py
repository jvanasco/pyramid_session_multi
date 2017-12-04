import logging
log = logging.getLogger(__name__)

# pyramid
from pyramid.interfaces import IDict
from pyramid.exceptions import ConfigurationError
# from pyramid.util import action_method
from zope.interface import implementer
from zope.interface import Interface

# ==============================================================================


__VERSION__ = '0.0.5'


# ==============================================================================
# ==============================================================================


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
    def __call__(config):
        """ Return an ISession object """


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

    def register_session_factory(self, namespace, session_factory, discriminator=None):
        """
            namespace:
                the namespace within `request.session_multi[]` for the session
            session_factory:
                an ISession compatible factory
            discriminator:
                a discriminator function to run on the request.
                The discriminator should accept a request and return `True` (pass) or `False`/`None` (fail)
                if the discriminator fails, the `request.session` will be set to `None`
                if the discriminator passes, the `request.session` will be the output of `factory(request)`
        """
        if not all((namespace, session_factory)):
            raise ConfigurationError('must register namespace and session_factory')
        if namespace in self._session_factories.keys():
            raise ConfigurationError('namespace `%s` already registered to pyramid_session_multi' % namespace)
        if session_factory in self._session_factories.values():
            raise ConfigurationError('session_factory `%s` (%s) already registered another namespace' % (session_factory, namespace))
        self._session_factories[namespace] = session_factory
        if discriminator:
            self._discriminators[namespace] = discriminator
        return True


@implementer(IDict)
class SessionMultiManager(dict):
    """
    This is the per-request multiple session interface.
    It is mounted onto the request, and creates ad-hoc sessions on the mountpoints as needed.
    """

    def __init__(self, request):
        self.request = request
        manager_config = request.registry.queryUtility(ISessionMultiManagerConfig)
        if manager_config is None:
            raise AttributeError('No session multi manager registered ')
        self._manager_config = manager_config

    def __getitem__(self, k):
        """
        Return the value for key ``k`` from the dictionary or raise a
        KeyError if the key doesn't exist"""
        if k not in self:
            if k in self._manager_config._session_factories:
                _session = None
                try:
                    _discriminator = self._manager_config._discriminators.get(k)
                    if _discriminator:
                        if not _discriminator(self.request):
                            raise _SessionDiscriminated()
                    _session = self._manager_config._session_factories[k](self.request)
                except _SessionDiscriminated:
                    pass
                dict.__setitem__(self, k, _session)
        try:
            return dict.__getitem__(self, k)
        except KeyError as e:
            raise UnregisteredSession("'%s' is not a valid session" % k)

    #
    # turn off some public methods
    #

    def __setitem__(self, k, value):
        raise ValueError("May not set on a SessionMultiManager")

    def __delitem__(self, k):
        raise ValueError("May not del on a SessionMultiManager")

    #
    # for debugging tools
    #

    def has_namespace(self, k):
        return True if k in self._manager_config._session_factories else False

    @property
    def loaded_status(self):
        _status_all = {k: False for k in self._manager_config._session_factories}
        _status_loaded = {k: True for k in self}
        _status_all.update(_status_loaded)
        return _status_all

    @property
    def namespaces(self):
        return self._manager_config._session_factories.keys()

    @property
    def discriminators(self):
        return self._manager_config._discriminators.keys()


# ==============================================================================


def new_session_multi(request):
    """
    this is turned into a reified request property
    """
    manager = SessionMultiManager(request)
    return manager


def register_session_factory(config, namespace, session_factory, discriminator=None):
    manager_config = config.registry.queryUtility(ISessionMultiManagerConfig)
    if manager_config is None:
        raise AttributeError('No session multi manager registered ')
    manager_config.register_session_factory(namespace, session_factory, discriminator=discriminator)


def includeme(config):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # step 1 - set up a SessionMultiManagerConfig
    manager_config = SessionMultiManagerConfig(config)
    config.registry.registerUtility(manager_config, ISessionMultiManagerConfig)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # step 2 - setup custom `session_managed` property
    config.add_request_method(new_session_multi,
                              'session_multi',
                              reify=True,
                              )
