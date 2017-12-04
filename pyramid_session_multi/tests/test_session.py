import unittest
import webtest
from pyramid import testing
from pyramid.threadlocal import get_current_request
from pyramid.session import SignedCookieSessionFactory
from pyramid.exceptions import ConfigurationError
from pyramid.config import Configurator
from pyramid.response import Response

from .. import register_session_factory
from .. import new_session_multi
from .. import SessionMultiManager
from .. import UnregisteredSession

import sys
PY3 = sys.version_info[0] == 3

# ------------------------------------------------------------------------------


class Test_Session(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        config = self.config
        config.include('pyramid_session_multi')
        factory_1 = SignedCookieSessionFactory('session_1', cookie_name='factory_1')
        register_session_factory(config, 'session_1', factory_1)
        factory_2 = SignedCookieSessionFactory('session_2', cookie_name='factory_2')
        register_session_factory(config, 'session_2', factory_2)
        factory_3 = SignedCookieSessionFactory('session_3', cookie_name='factory_3')
        register_session_factory(config, 'session_3', factory_3)

        # create a session_multi object
        request.session_multi = new_session_multi(request)

    def tearDown(self):
        testing.tearDown()

    def test_is_instance(self):
        request = get_current_request()
        # this is an anonymous type, impossible to test otherwise
        self.assertIsInstance(request.session_multi, SessionMultiManager)
        session_type_string = "<class 'pyramid.session.BaseCookieSessionFactory.<locals>.CookieSession'>" if PY3 else "<class 'pyramid.session.CookieSession'>"
        self.assertEqual(str(type(request.session_multi['session_1'])), session_type_string)
        self.assertEqual(str(type(request.session_multi['session_2'])), session_type_string)
        self.assertEqual(str(type(request.session_multi['session_3'])), session_type_string)

    def test_invalids(self):
        request = get_current_request()
        self.assertRaises(KeyError,
                          lambda: request.session_multi['invalid']
                          )
        self.assertRaises(UnregisteredSession,
                          lambda: request.session_multi['invalid']
                          )

    def test_disallow_set_del(self):
        """set/del on a multi-key will raise a ValueError"""
        request = get_current_request()
        def f_del():
            del request.session_multi['session_1']
        def f_set():
            request.session_multi['session_1'] = 1
        self.assertRaises(ValueError, f_del)
        self.assertRaises(ValueError, f_set)

    def test_lazyops(self):
        """
        the library self-reports, but don't trust it
        """
        request = get_current_request()
        
        # lazy-op a session
        request.session_multi['session_1']['foo'] = 'bar'
        
        # check the self-report
        _status = request.session_multi.loaded_status
        self.assertEqual(_status['session_1'], True)
        self.assertEqual(_status['session_2'], False)
        self.assertEqual(_status['session_3'], False)

        # but don't trust it
        self.assertIn('session_1', request.session_multi)
        self.assertNotIn('session_2', request.session_multi)
        self.assertNotIn('session_3', request.session_multi)
        
        registered_namespaces = request.session_multi.namespaces
        for _namespace in ('session_1', 'session_2', 'session_3'):
            self.assertIn(_namespace, registered_namespaces)

    def test_instantiated_correctly(self):
        request = get_current_request()
        self.assertIsInstance(request.session_multi['session_1'], dict)
        self.assertIsInstance(request.session_multi['session_2'], dict)
        self.assertIsInstance(request.session_multi['session_3'], dict)


class Test_Discriminator(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        config = self.config
        config.include('pyramid_session_multi')
        
        def _f_True(_req):
            return True

        def _f_False(_req):
            return False
        
        discriminator_1 = _f_True  # pass
        discriminator_2 = _f_True  # pass
        discriminator_3 = _f_False  # fail
        
        factory_1 = SignedCookieSessionFactory('session_1', cookie_name='factory_1')
        register_session_factory(config, 'session_1', factory_1, discriminator=discriminator_1, )
        factory_2 = SignedCookieSessionFactory('session_2', cookie_name='factory_2')
        register_session_factory(config, 'session_2', factory_2, discriminator=discriminator_2, )
        factory_3 = SignedCookieSessionFactory('session_3', cookie_name='factory_3')
        register_session_factory(config, 'session_3', factory_3, discriminator=discriminator_3, )

        # create a session_multi object
        request.session_multi = new_session_multi(request)

    def tearDown(self):
        testing.tearDown()

    def test_instantiated_correctly(self):
        request = get_current_request()
        self.assertIsInstance(request.session_multi['session_1'], dict)
        self.assertIsInstance(request.session_multi['session_2'], dict)
        self.assertIsNone(request.session_multi['session_3'])

