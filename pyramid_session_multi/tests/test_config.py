import unittest
from pyramid import testing
from pyramid.threadlocal import get_current_request
from pyramid.session import SignedCookieSessionFactory
from pyramid.exceptions import ConfigurationError

from .. import register_session_factory

# ------------------------------------------------------------------------------


class Test_NotIncluded(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.settings = self.config.registry.settings

    def tearDown(self):
        testing.tearDown()

    def test_configure_one_fails(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        self.assertRaises(AttributeError, 
                          register_session_factory,
                          self.config, 'session_1', factory_1,
                          )


class Test_Included(unittest.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.include('pyramid_session_multi')
        self.settings = self.config.registry.settings

    def tearDown(self):
        testing.tearDown()

    def test_configure_no_namespace_fails(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        self.assertRaises(ConfigurationError, 
                          register_session_factory,
                          self.config, None, factory_1,
                          )

    def test_configure_no_factory_fails(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        self.assertRaises(ConfigurationError, 
                          register_session_factory,
                          self.config, 'session_1', None,
                          )

    def test_configure_one_success(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        register_session_factory(self.config, 'session_1', factory_1)

    def test_configure_two_success(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        register_session_factory(self.config, 'session_1', factory_1)
        factory_2 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_2')
        register_session_factory(self.config, 'session_2', factory_2)

    def test_configure_conflict_namespace_fails(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        register_session_factory(self.config, 'session_1', factory_1)
        factory_2 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_2')
        self.assertRaises(ConfigurationError, 
                          register_session_factory,
                          self.config, 'session_1', factory_2,
                          )

    def test_configure_conflict_factory_fails(self):
        factory_1 = SignedCookieSessionFactory('aaaaa', cookie_name='factory_1')
        register_session_factory(self.config, 'session_1', factory_1)
        self.assertRaises(ConfigurationError, 
                          register_session_factory,
                          self.config, 'session_2', factory_1,
                          )
