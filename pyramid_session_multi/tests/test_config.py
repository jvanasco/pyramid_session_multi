from __future__ import print_function
from __future__ import unicode_literals

# stdlib
import re
import unittest

# pyramid testing requirements
from pyramid import testing
from pyramid.session import SignedCookieSessionFactory
from pyramid.exceptions import ConfigurationError
from pyramid.response import Response
from pyramid.request import Request

# local
from .. import register_session_factory


# ------------------------------------------------------------------------------


# used to ensure the toolbar link is injected into requests
re_toolbar_link = re.compile('(?:href="http://localhost)(/_debug_toolbar/[\d]+)"')


class Test_NotIncluded(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.settings = self.config.registry.settings

    def tearDown(self):
        testing.tearDown()

    def test_configure_one_fails(self):
        factory_1 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_1")
        self.assertRaises(
            AttributeError,
            register_session_factory,
            self.config,
            "session_1",
            factory_1,
        )


class Test_Included(unittest.TestCase):
    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)
        self.config.include("pyramid_session_multi")
        self.settings = self.config.registry.settings

    def tearDown(self):
        testing.tearDown()

    def test_configure_no_namespace_fails(self):
        factory_1 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_1")
        self.assertRaises(
            ConfigurationError, register_session_factory, self.config, None, factory_1
        )

    def test_configure_no_factory_fails(self):
        factory_none = None
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_1",
            factory_none,
        )

    def test_configure_one_success(self):
        factory_1 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_1")
        register_session_factory(self.config, "session_1", factory_1)

    def test_configure_two_success(self):
        factory_1 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_1")
        register_session_factory(self.config, "session_1", factory_1)
        factory_2 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_2")
        register_session_factory(self.config, "session_2", factory_2)

    def test_configure_conflict_namespace_fails(self):
        factory_1 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_1")
        register_session_factory(self.config, "session_1", factory_1)
        factory_2 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_2")
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_1",
            factory_2,
        )

    def test_configure_conflict_factory_fails(self):
        factory_1 = SignedCookieSessionFactory("aaaaa", cookie_name="factory_1")
        register_session_factory(self.config, "session_1", factory_1)
        self.assertRaises(
            ConfigurationError,
            register_session_factory,
            self.config,
            "session_2",
            factory_1,
        )


class TestDebugtoolbarPanel(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_settings(
            {"debugtoolbar.includes": "pyramid_session_multi.debugtoolbar"}
        )
        self.config.include("pyramid_session_multi")
        self.config.include("pyramid_debugtoolbar")
        self.settings = self.config.registry.settings

        # create a view
        def empty_view(request):
            return Response(
                "<html><head></head><body>OK</body></html>", content_type="text/html"
            )

        self.config.add_view(empty_view)

    def tearDown(self):
        testing.tearDown()

    def test_panel_injected__no_configuration(self):

        # make the app
        app = self.config.make_wsgi_app()
        # make a request
        req1 = Request.blank("/")
        req1.remote_addr = "127.0.0.1"
        resp1 = req1.get_response(app)
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp1.text)

        # check the toolbar
        links = re_toolbar_link.findall(resp1.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp2 = req2.get_response(app)
        self.assertEqual(resp2.status_code, 200)

        self.assertIn('<li class="" id="pDebugPanel-SessionMulti">', resp2.text)
        self.assertIn(
            '<div id="pDebugPanel-SessionMulti-content" class="panelContent"',
            resp2.text,
        )
        self.assertIn('<div class="pDebugPanelTitle">', resp2.text)
        self.assertIn("<h3>SessionMulti</h3>", resp2.text)

        # this is configured badly on purpose
        self.assertIn(
            "No configuration detected. The package has not been configured properly.",
            resp2.text,
        )

    def test_panel_injected__configured(self):

        session_factory_1 = SignedCookieSessionFactory(
            "secret1", cookie_name="session1"
        )
        register_session_factory(self.config, "session1", session_factory_1)

        session_factory_2 = SignedCookieSessionFactory(
            "secret2", cookie_name="session1"
        )
        register_session_factory(self.config, "session2", session_factory_2)

        # make the app
        app = self.config.make_wsgi_app()
        # make a request
        req1 = Request.blank("/")
        req1.remote_addr = "127.0.0.1"
        resp1 = req1.get_response(app)
        self.assertEqual(resp1.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp1.text)

        # check the toolbar
        links = re_toolbar_link.findall(resp1.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp2 = req2.get_response(app)
        self.assertEqual(resp2.status_code, 200)

        self.assertIn('<li class="" id="pDebugPanel-SessionMulti">', resp2.text)
        self.assertIn(
            '<div id="pDebugPanel-SessionMulti-content" class="panelContent"',
            resp2.text,
        )
        self.assertIn('<div class="pDebugPanelTitle">', resp2.text)
        self.assertIn("<h3>SessionMulti</h3>", resp2.text)

        # this one was configured
        # note that Python2 and Python3 show a different class for the session cookie
        self.assertIn(
            '\t<table class="table table-striped table-condensed">\n\t\t<thead>\n\t\t\t<tr>\n\t\t\t\t<th>namespace</th>\n\t\t\t\t<th>cookie_name</th>\n\t\t\t\t<th>has discriminators?</th>\n\t\t\t\t<th>info</th>\n\t\t\t</tr>\n\t\t</thead>\n\t\t<tbody>\n\t\t\t\t<tr>\n\t\t\t\t\t<th>session1</th>\n\t\t\t\t\t<td><code>session1</code></td>\n\t\t\t\t\t<td></td>\n\t\t\t\t\t<td>\n\t\t\t\t\t\t\t&lt;class &#39;pyramid.session',
            resp2.text,
        )
