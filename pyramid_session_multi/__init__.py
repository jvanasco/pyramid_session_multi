import logging
log = logging.getLogger(__name__)

# pyramid
from pyramid.decorator import reify
from pyramid.interfaces import IDict
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

    def __init__(self, config):
        self.session_factories = {}


@implementer(IDict)
class SessionMultiManager(dict):

    def __init__(self, request):
        manager_config = request.registry.queryUtility(ISessionMultiManagerConfig)
        if manager_config is None:
            raise AttributeError('No session multi manager registered ')
        self.request = request
        for (namespace, factory) in manager_config.session_factories.items():
            self[namespace] = factory(request)


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
    manager_config.session_factories[namespace] = session_factory


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
