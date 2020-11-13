# stdlib
import random
import unittest

# pyramid
from pyramid import testing
from pyramid.request import Request
import webob.cookies

# package
from pyramid_session_multi import ISessionMultiManagerConfig
from pyramid_session_multi import register_session_factory

# local
from ._utils import discriminator_False
from ._utils import discriminator_True
from ._utils import empty_view
from ._utils import ok_response_factory
from ._utils import PY3
from ._utils import re_toolbar_link
from ._utils import session_factory_1
from ._utils import session_factory_2
from ._utils import session_factory_3

# ==============================================================================


class SessionConfigMixin(object):
    """
    Mixin Class for configuring our sessions
    """

    # class setup; boolean. should sessions be enabled?
    enable_sessions = True

    # class setup; None or list of session namespaces to discriminate
    discriminate_sessions = None

    # class setup; dict of session namespace to factory
    session_to_factory = {
        "session_a": session_factory_1,
        "session_b": session_factory_2,
        "session_c": session_factory_3,
    }

    # class setup; dict of session namespace to discriminator
    session_to_discriminator = {
        "session_a": discriminator_True,  # pass
        "session_b": discriminator_True,  # pass
        "session_c": discriminator_False,  # fail
    }

    # set within `.setup`; pyramid config object; `testing.setUp()`
    config = None

    # set within `.configure_sessions`, set this to a list of the enabled namespaces
    sessions_enabled = None

    def configure_sessions(self):
        if self.enable_sessions:
            self.config.include("pyramid_session_multi")
            for _namespace, _factory in self.session_to_factory.items():
                # register_session_factory(self.config, "session_a", session_factory_1)
                _discriminator = None
                if (
                    self.discriminate_sessions
                    and _namespace in self.discriminate_sessions
                ):
                    _discriminator = self.session_to_discriminator[_namespace]
                register_session_factory(
                    self.config, _namespace, _factory, discriminator=_discriminator
                )
                self.sessions_enabled = self.session_to_factory.keys()
        else:
            self.sessions_enabled = []


class _TestPanelConfiguration(unittest.TestCase, SessionConfigMixin):
    """
    this was the original test

    """

    config = None
    app = None
    re_toolbar_link = re_toolbar_link

    def setUp(self):
        self.config = config = testing.setUp()
        config.add_settings(
            {"debugtoolbar.includes": "pyramid_session_multi.debugtoolbar"}
        )
        config.include("pyramid_debugtoolbar")
        self.configure_sessions()
        config.add_view(empty_view)
        # make the app
        self.settings = config.registry.settings
        self.app = config.make_wsgi_app()

    def tearDown(self):
        testing.tearDown()


class TestPanelConfiguration_NotConfigured(_TestPanelConfiguration):
    def test_panel_injected(self):
        # make a request
        req1 = Request.blank("/")
        req1.remote_addr = "127.0.0.1"
        resp1 = req1.get_response(self.app)
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
        resp2 = req2.get_response(self.app)
        self.assertEqual(resp2.status_code, 200)

        self.assertIn('<li class="" id="pDebugPanel-session_multi">', resp2.text)
        self.assertIn(
            '<div id="pDebugPanel-session_multi-content" class="panelContent"',
            resp2.text,
        )
        self.assertIn('<div class="pDebugPanelTitle">', resp2.text)
        self.assertIn("<h3>SessionMulti</h3>", resp2.text)


class TestPanelConfiguration_Configured(_TestPanelConfiguration):
    def test_panel_injected(self):
        # make a request
        req1 = Request.blank("/")
        req1.remote_addr = "127.0.0.1"
        resp1 = req1.get_response(self.app)
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
        resp2 = req2.get_response(self.app)
        self.assertEqual(resp2.status_code, 200)

        self.assertIn('<li class="" id="pDebugPanel-session_multi">', resp2.text)
        self.assertIn(
            '<div id="pDebugPanel-session_multi-content" class="panelContent"',
            resp2.text,
        )
        self.assertIn('<div class="pDebugPanelTitle">', resp2.text)
        self.assertIn("<h3>SessionMulti</h3>", resp2.text)


class _TestDebugtoolbarPanel(unittest.TestCase, SessionConfigMixin):

    config = None
    app = None
    re_toolbar_link = re_toolbar_link

    def _session_view(self, context, request):
        """
        This function should define a Pyramid view.
        * (potentially) invoke ``ISession``
        * return a ``Response``
        """
        raise NotImplementedError()

    def _session_view_two(self, context, request):
        """
        This function should define a Pyramid view.
        * (potentially) invoke ``ISession``
        * return a ``Response``
        """
        raise NotImplementedError()

    def setUp(self):
        self.config = config = testing.setUp()
        config.add_settings(
            {"debugtoolbar.includes": "pyramid_session_multi.debugtoolbar"}
        )
        config.include("pyramid_debugtoolbar")
        self.configure_sessions()
        config.add_route("session_view", "/session-view")
        config.add_route("session_view_two", "/session-view-two")
        config.add_view(self._session_view, route_name="session_view")
        config.add_view(self._session_view_two, route_name="session_view_two")
        # make the app
        self.settings = config.registry.settings
        self.app = config.make_wsgi_app()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, is_active=None, sessions_invalid=None):
        """
        Makes a request to the main application
        * which invokes `self._session_view`
        * make a request to the toolbar
        * return the toolbar ``Response``

        :param is_active:
            Default ``None``
            If ``True``, a ``pdbt_active`` cookie will be sent to activate
            additional features in the "Session" panel.
        :param sessions_invalid: iterable of invalid namespaces to create the
            view with
        """
        # make a request
        req1 = Request.blank("/session-view")
        req1.remote_addr = "127.0.0.1"
        _cookies = []
        if is_active:
            _cookies.append("pdtb_active=session_multi")
        if sessions_invalid:
            manager_config = self.app.registry.queryUtility(ISessionMultiManagerConfig)
            for ns, ckname in manager_config.namespaces_to_cookienames.items():
                if ns in sessions_invalid:
                    # create an invalid cookie
                    _cookies.append("%s=123123123123" % ns)
        if _cookies:
            _cookies = "; ".join(_cookies)
            if not PY3:
                _cookies = _cookies.encode()
            req1.headers["Cookie"] = _cookies
        resp_app = req1.get_response(self.app)
        self.assertEqual(resp_app.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp_app.text)

        # check the toolbar
        links = self.re_toolbar_link.findall(resp_app.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp_toolbar = req2.get_response(self.app)

        return (resp_app, resp_toolbar)

    def _makeAnother(self, resp_app, is_active=None):
        """
        Makes a second request to the main application
        * which invokes ``self._session_view_two``
        * Make a request to the toolbar
        * return the toolbar ``Response``

        :param resp_app:
            The ``Response`` object of the Pyramid application view
            returned from ``_makeOne``.
        :param is_active:
            Default ``None``
            If ``True``, a ``pdbt_active`` cookie will be sent to activate
            additional features in the "Session" panel.
        """
        # make a secondary request
        req1 = Request.blank("/session-view-two")
        req1.remote_addr = "127.0.0.1"
        _cookies = []
        if is_active:
            _cookies.append("pdtb_active=session_multi")
        if "Set-Cookie" in resp_app.headers:
            for _set_cookie_header in resp_app.headers.getall("Set-Cookie"):
                _cks = webob.cookies.parse_cookie(_set_cookie_header)
                for _ck in _cks:
                    _cookies.append("%s=%s" % (_ck[0].decode(), _ck[1].decode()))
        if _cookies:
            _cookies = "; ".join(_cookies)
            if not PY3:
                _cookies = _cookies.encode()
            req1.headers["Cookie"] = _cookies
        resp_app2 = req1.get_response(self.app)
        self.assertEqual(resp_app2.status_code, 200)
        self.assertIn("http://localhost/_debug_toolbar/", resp_app2.text)

        # check the toolbar
        links = self.re_toolbar_link.findall(resp_app2.text)
        self.assertIsNotNone(links)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 1)
        toolbar_link = links[0]

        req2 = Request.blank(toolbar_link)
        req2.remote_addr = "127.0.0.1"
        resp_toolbar = req2.get_response(self.app)

        return (resp_app2, resp_toolbar)

    def _check_rendered__panel(
        self,
        resp,
        is_configured=None,
        sessions_accessed=None,
        sessions_discriminator_fail=None,
    ):
        """
        Ensure the rendered panel exists with statements.

        :param resp: a ``Response`` object with a ``.text`` attribute for html
        :param is_configured: is an ``ISessionFactory`` configured for the app?
        :param sessions_accessed: iterable of namespaces accessed during the view
        :param sessions_discriminator_fail: iterable of namespaces with failed
            discriminators
        """
        self.assertIn('<li class="" id="pDebugPanel-session_multi">', resp.text)
        self.assertIn(
            '<div id="pDebugPanel-session_multi-content" class="panelContent" '
            'style="display: none;">',
            resp.text,
        )
        if is_configured:
            self.assertIn("<p>Using `ISessionMultiConfiguration`: <code>", resp.text)
        else:
            self.assertIn(
                "<p>No `ISessionMultiConfiguration` Configured</p>", resp.text
            )
        for namespace in self.sessions_enabled:
            if sessions_accessed and (namespace in sessions_accessed):
                self.assertIn(
                    """<code>request.session_multi["%s"]</code>\n\t\t\t\t\t"""
                    """<span class="label label-success">accessed during the main `Request` handler</span>"""
                    % namespace,
                    resp.text,
                )
            else:
                self.assertIn(
                    """<code>request.session_multi["%s"]</code>\n\t\t\t\t\t"""
                    """<span class="label label-warning">not accessed during the main `Request` handler</span>"""
                    % namespace,
                    resp.text,
                )
            if sessions_discriminator_fail and (
                namespace in sessions_discriminator_fail
            ):
                self.assertIn(
                    """<code>request.session_multi["%s"]</code>\n\t\t\t\t\t"""
                    """<span class="label label-success">accessed during the main `Request` handler</span>\n\t\t\t\t\t"""
                    """<span class="label label-danger">Session Discriminator Fail</span>"""
                    % namespace,
                    resp.text,
                )


class TestNoSessionConfigured(_TestDebugtoolbarPanel):
    """
    Ensure the panel works when:
    * no "Session" panel is configured
    * no "Session" data is accessed
    """

    enable_sessions = False

    def _session_view(self, context, request):
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=False, sessions_accessed=[]
        )


class TestSessionConfiguredNoAccess(_TestDebugtoolbarPanel):
    """
    Ensure the panel works when:
    * the "Session" panel is configured
    * no "Session" data is accessed
    """

    def _session_view(self, context, request):
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, sessions_accessed=[]
        )

    def test_panel_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar, is_configured=True, sessions_accessed=[]
        )


class TestSimpleSession(_TestDebugtoolbarPanel):
    """
    Ensure the panel works when:
    * the "Session" panel is configured
    * "Session" data is accessed
    """

    def _session_view(self, context, request):
        request.session_multi["session_a"]["foo"] = "bar"
        return ok_response_factory()

    def _session_view_two(self, context, request):
        request.session_multi["session_a"]["foo"] = "barbar"
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )

    def test_panel_invalid_session(self):
        (resp_app, resp_toolbar) = self._makeOne(
            sessions_invalid=[
                "session_a",
            ],
        )
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )

    def test_panel_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )

    def test_panel_twice(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(resp_app)
        self._check_rendered__panel(
            resp_toolbar2,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )
        # we should see the INGRESS and EGRESS value for session["foo"]
        self.assertIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertIn("<code>'barbar'</code>", resp_toolbar2.text)

    def test_panel_twice_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(resp_app, is_active=True)
        self._check_rendered__panel(
            resp_toolbar2,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )
        # we should see the INGRESS and EGRESS value for session["foo"]
        self.assertIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertIn("<code>'barbar'</code>", resp_toolbar2.text)


class TestSessionAlt(_TestDebugtoolbarPanel):
    """
    Ensure the panel works when:
    * the "Session" panel is configured
    * "Session" data is accessed
    """

    def _session_view(self, context, request):
        # touches the session
        request.session_multi["session_a"]["foo"] = "bar"
        request.session_multi["session_b"]["biz"] = "bang"
        return ok_response_factory()

    def _session_view_two(self, context, request):
        # no session interaction
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
                "session_b",
            ],
        )

    def test_panel_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
                "session_b",
            ],
        )

    def test_panel_twice(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
                "session_b",
            ],
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(resp_app)
        self._check_rendered__panel(
            resp_toolbar2, is_configured=True, sessions_accessed=[]
        )
        # we should NOT see the INGRESS and EGRESS value for session["foo"]
        self.assertNotIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertNotIn("<code>'bang'</code>", resp_toolbar2.text)

    def test_panel_twice_active(self):
        (resp_app, resp_toolbar) = self._makeOne(is_active=True)
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
                "session_b",
            ],
        )
        (resp_app2, resp_toolbar2) = self._makeAnother(resp_app, is_active=True)
        self._check_rendered__panel(
            resp_toolbar2, is_configured=True, sessions_accessed=[]
        )

        # we should see the INGRESS and EGRESS value for session["foo"]
        self.assertIn("<code>'bar'</code>", resp_toolbar2.text)
        self.assertEqual(2, resp_toolbar2.text.count("<code>'bar'</code>"))
        self.assertIn("<code>'bang'</code>", resp_toolbar2.text)
        self.assertEqual(2, resp_toolbar2.text.count("<code>'bang'</code>"))


class TestSortingErrorsSession(_TestDebugtoolbarPanel):
    """
    Previous toolbars could encounter a fatal exception from ``TypeError`` when
    trying to sort session variables. One way to raise a ``TypeError`` is trying
    to sort a float and a string under Python3.
    """

    def _session_view(self, context, request):
        rand = random.random()
        request.session_multi["session_a"][rand] = True
        request.session_multi["session_a"]["foo"] = "bar"
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
            ],
        )


class TestDiscriminatedSessions(_TestDebugtoolbarPanel):
    """
    Test the session discriminator works properly
    """

    discriminate_sessions = [
        "session_a",  # pass
        "session_c",  # fail
    ]

    def _session_view(self, context, request):
        # touches the session
        # discriminated session: pass
        request.session_multi["session_a"]["foo"] = "bar"
        # no discriminator
        request.session_multi["session_b"]["biz"] = "bang"
        # discriminated session: fail
        self.assertEqual(request.session_multi["session_c"], None)
        return ok_response_factory()

    def test_panel(self):
        (resp_app, resp_toolbar) = self._makeOne()
        self.assertEqual(resp_toolbar.status_code, 200)
        self._check_rendered__panel(
            resp_toolbar,
            is_configured=True,
            sessions_accessed=[
                "session_a",
                "session_b",
                "session_c",  # although a fail, we accessed it
            ],
            sessions_discriminator_fail=[
                "session_c",
            ],
        )
