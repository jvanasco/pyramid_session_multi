import logging
log = logging.getLogger(__name__)

# pyramid
from pyramid.interfaces import IDict
from pyramid.exceptions import ConfigurationError
# from pyramid.util import action_method
from zope.interface import implementer
from zope.interface import Interface

# ==============================================================================


__VERSION__ = '0.1.0'


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
        self._cookienames = {}

    def register_session_factory(self, namespace, session_factory, discriminator=None, cookie_name=None):
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
        
        # session_factory._cookie_name
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
        if cookie_name is None:
            if hasattr(session_factory, '_cookie_name'):
                cookie_name = session_factory._cookie_name
        self._cookienames[namespace] = cookie_name
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

    def _discriminated_session(self, k):
        """private method. this was part of __get_item__ but was pulled out for the debugging panel
        """
        _session = None
        try:
            _discriminator = self._manager_config._discriminators.get(k)
            if _discriminator:
                if not _discriminator(self.request):
                    raise _SessionDiscriminated()
            _session = self._manager_config._session_factories[k](self.request)
        except _SessionDiscriminated:
            pass
        return _session

    def __getitem__(self, k):
        """
        Return the value for key ``k`` from the dictionary or raise a
        KeyError if the key doesn't exist
        """
        if k not in self:
            if k in self._manager_config._session_factories:
                _session = self._discriminated_session(k)
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
    # for debugging and debugging_toolbar
    #

    def _debug_incoming(self):
        """
        this is a private method used only by the toolbar.
        please don't rely on it.
        this will not be supported as the toolbar may migrate to another system.
        this simply reads all the session data into a dict, without binding it to this interface.
        """
        all_incoming = {k: self._discriminated_session(k)
                        for k in self._manager_config._session_factories.keys()
                        }
        return all_incoming

    def has_namespace(self, k):
        """is this a valid namespace/session?"""
        return True if k in self._manager_config._session_factories else False

    @property
    def loaded_status(self):
        """list what was loaded or not"""
        _status_all = {k: False for k in self._manager_config._session_factories.keys()}
        _status_loaded = {k: True for k in self}
        _status_all.update(_status_loaded)
        return _status_all

    @property
    def namespaces(self):
        """list all possible namespaces"""
        return list(self._manager_config._session_factories.keys())

    @property
    def discriminators(self):
        """list all namespaces with discriminators"""
        return list(self._manager_config._discriminators.keys())


# ==============================================================================


def new_session_multi(request):
    """
    this is turned into a reified request property
    """
    manager = SessionMultiManager(request)
    return manager


def register_session_factory(config, namespace, session_factory, discriminator=None, cookie_name=None):
    manager_config = config.registry.queryUtility(ISessionMultiManagerConfig)
    if manager_config is None:
        raise AttributeError('No session multi manager registered ')
    manager_config.register_session_factory(namespace, session_factory, discriminator=discriminator, cookie_name=cookie_name, )


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
