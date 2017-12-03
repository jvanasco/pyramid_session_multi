import logging
log = logging.getLogger(__name__)

# pyramid
from pyramid.decorator import reify
from pyramid.interfaces import IDict
from pyramid.exceptions import ConfigurationError
from pyramid.util import action_method
from zope.interface import implementer
from zope.interface import Interface

# ==============================================================================


__VERSION__ = '0.0'


# ==============================================================================
# ==============================================================================


class ISessionMultiManagerConfig(Interface):
    """
    An interface representing a factory which accepts a `config` instance and
    returns an ISessionMultiManagerConfig compliant object. There should be one and
    only one ISessionMultiManagerConfig per application.
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

    def register_session_factory(self, namespace, session_factory):
        if not all((namespace, session_factory)):
            raise ConfigurationError('must register namespace and session_factory')
        if namespace in self._session_factories.keys():
            raise ConfigurationError('namespace `%s` already registered to pyramid_session_multi' % namespace)
        if session_factory in self._session_factories.values():
            raise ConfigurationError('session_factory `%s` (%s) already registered another namespace' % (session_factory, namespace))
        self._session_factories[namespace] = session_factory
        return True

@implementer(IDict)
class SessionMultiManager(dict):
    """
    This is the per-request multiple session interface.
    It is mounted onto the request, and creates ad-hoc sessions on the mountpoints as needed.
    """

    def __init__(self, request):
        manager_config = request.registry.queryUtility(ISessionMultiManagerConfig)
        if manager_config is None:
            raise AttributeError('No session multi manager registered ')
        self.request = request
        self._namespaces = {}
        for (namespace, factory) in manager_config._session_factories.items():
            self._namespaces[namespace] = factory

    def __getitem__(self, k):
        """ Return the value for key ``k`` from the dictionary or raise a
        KeyError if the key doesn't exist"""
        if k not in self:
            if k in self._namespaces:
                _session = self._namespaces[k](self.request)
                dict.__setitem__(self, k, _session)
        try:
            return dict.__getitem__(self, k)
        except KeyError as e:
            raise KeyError("'%s' is not a valid session" % k)

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
        return True if k in self._namespaces else False

    @property
    def loaded_status(self):
        _status_all = {k: False for k in self._namespaces}
        _status_loaded = {k: True for k in self}
        _status_all.update(_status_loaded)
        return  _status_all


# ==============================================================================


def new_session_multi(request):
    """
    this is turned into a reified request property
    """
    manager = SessionMultiManager(request)
    return manager


def register_session_factory(config, namespace, session_factory):
    manager_config = config.registry.queryUtility(ISessionMultiManagerConfig)
    if manager_config is None:
        raise AttributeError('No session multi manager registered ')
    manager_config.register_session_factory(namespace, session_factory)


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
