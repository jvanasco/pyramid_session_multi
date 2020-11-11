# stdlib
import unittest

# pyramid
from pyramid import testing
from pyramid.exceptions import ConfigurationError

# package
from pyramid_session_multi import register_session_factory

# local
from ._utils import session_factory_1
from ._utils import session_factory_1_duplicate
from ._utils import session_factory_2
from ._utils import session_factory_3


# ==============================================================================


class Test_NotIncluded(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = config = testing.setUp(request=request)
        self.settings = settings = config.registry.settings

    def tearDown(self):
        testing.tearDown()

    def test_configure_one_fails(self):
        self.assertRaises(
            AttributeError,
            register_session_factory,
            self.config,
            "session_1",
            session_factory_1,
        )


class Test_Included(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = config = testing.setUp(request=request)
        config.include("pyramid_session_multi")
        self.settings = settings = config.registry.settings

    def tearDown(self):
        testing.tearDown()

    def test_configure_no_namespace_fails(self):
        """
        fail to register with a namespace of `None`
        """
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            None,
            session_factory_1,
        )

    def test_configure_no_factory_fails(self):
        """
        fail to register with a factory of `None`
        """
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_1",
            None,
        )

    def test_configure_one_success(self):
        """success to register a single namespace"""
        register_session_factory(self.config, "session_1", session_factory_1)

    def test_configure_two_success(self):
        """success to register two namespace"""
        register_session_factory(self.config, "session_1", session_factory_1)
        register_session_factory(self.config, "session_2", session_factory_2)

    def test_configure_three_success(self):
        """success to register three namespace"""
        register_session_factory(self.config, "session_1", session_factory_1)
        register_session_factory(self.config, "session_2", session_factory_2)
        register_session_factory(self.config, "session_3", session_factory_3)

    def test_configure_conflict_namespace_fails(self):
        """
        fail to register two different factories into the same namespace
        """
        register_session_factory(self.config, "session_1", session_factory_1)
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_1",
            session_factory_2,
        )

    def test_configure_conflict_factory_fails(self):
        """
        fail to register a single factory into two namespaces
        """
        register_session_factory(self.config, "session_1", session_factory_1)
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_2",
            session_factory_1,
        )

    def test_configure_conflict_cookiename_fails(self):
        """
        fail to register a two different factories which both use the same cookiename
        """
        register_session_factory(self.config, "session_1", session_factory_1)
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_1_duplicate",
            session_factory_1_duplicate,
        )
