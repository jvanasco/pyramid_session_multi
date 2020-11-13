# stdlib
import unittest

# pyramid
from pyramid import testing
from pyramid.threadlocal import get_current_request

# package
from pyramid_session_multi import new_session_multi
from pyramid_session_multi import register_session_factory
from pyramid_session_multi import SessionMultiManager
from pyramid_session_multi import UnregisteredSession

# local
from ._utils import discriminator_True
from ._utils import discriminator_False
from ._utils import PY3
from ._utils import session_factory_1
from ._utils import session_factory_2
from ._utils import session_factory_3


# ==============================================================================


class Test_Session(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        config = self.config
        config.include("pyramid_session_multi")
        register_session_factory(config, "session_1", session_factory_1)
        register_session_factory(config, "session_2", session_factory_2)
        register_session_factory(config, "session_3", session_factory_3)

        # create a session_multi object
        request.session_multi = new_session_multi(request)

    def tearDown(self):
        testing.tearDown()

    def test_is_instance(self):
        request = get_current_request()
        # this is an anonymous type, impossible to test otherwise
        self.assertIsInstance(request.session_multi, SessionMultiManager)
        session_type_string = (
            "<class 'pyramid.session.BaseCookieSessionFactory.<locals>.CookieSession'>"
            if PY3
            else "<class 'pyramid.session.CookieSession'>"
        )
        self.assertEqual(
            str(type(request.session_multi["session_1"])), session_type_string
        )
        self.assertEqual(
            str(type(request.session_multi["session_2"])), session_type_string
        )
        self.assertEqual(
            str(type(request.session_multi["session_3"])), session_type_string
        )

    def test_invalids(self):
        request = get_current_request()
        self.assertRaises(KeyError, lambda: request.session_multi["invalid"])
        self.assertRaises(UnregisteredSession, lambda: request.session_multi["invalid"])

    def test_disallow_set_del(self):
        """set/del on a multi-key will raise a ValueError"""
        request = get_current_request()

        def f_del():
            del request.session_multi["session_1"]

        def f_set():
            request.session_multi["session_1"] = 1

        self.assertRaises(ValueError, f_del)
        self.assertRaises(ValueError, f_set)

    def test_lazyops(self):
        """
        the library self-reports, but don't trust it
        """
        request = get_current_request()

        # lazy-op a session
        request.session_multi["session_1"]["foo"] = "bar"

        # but don't trust it
        self.assertIn("session_1", request.session_multi)
        self.assertNotIn("session_2", request.session_multi)
        self.assertNotIn("session_3", request.session_multi)

        registered_namespaces = request.session_multi.namespaces
        for _namespace in ("session_1", "session_2", "session_3"):
            self.assertIn(_namespace, registered_namespaces)

    def test_instantiated_correctly(self):
        request = get_current_request()
        self.assertIsInstance(request.session_multi["session_1"], dict)
        self.assertIsInstance(request.session_multi["session_2"], dict)
        self.assertIsInstance(request.session_multi["session_3"], dict)


class Test_Discriminator(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        config = self.config
        config.include("pyramid_session_multi")

        # pass
        register_session_factory(
            config, "session_1", session_factory_1, discriminator=discriminator_True
        )
        register_session_factory(
            config, "session_2", session_factory_2, discriminator=discriminator_True
        )
        # fail
        register_session_factory(
            config, "session_3", session_factory_3, discriminator=discriminator_False
        )

        # create a session_multi object
        request.session_multi = new_session_multi(request)

    def tearDown(self):
        testing.tearDown()

    def test_instantiated_correctly(self):
        request = get_current_request()
        self.assertIsInstance(request.session_multi["session_1"], dict)
        self.assertIsInstance(request.session_multi["session_2"], dict)
        self.assertIsNone(request.session_multi["session_3"])
