# stdlib
import re
import sys

# pyramid
from pyramid.response import Response
from pyramid.session import SignedCookieSessionFactory


# ==============================================================================


PY3 = sys.version_info[0] == 3


# ------------------------------------------------------------------------------


def discriminator_False(request):
    return False


def discriminator_True(request):
    return True


def ok_response_factory():
    return Response(
        "<html><head></head><body>OK</body></html>",
        content_type="text/html",
    )


def empty_view(request):
    return ok_response_factory()


# used to ensure the toolbar link is injected into requests
re_toolbar_link = re.compile(r'(?:href="http://localhost)(/_debug_toolbar/[\d]+)"')


session_factory_1 = SignedCookieSessionFactory("secret1", cookie_name="session1")
session_factory_1_duplicate = SignedCookieSessionFactory(
    "secret1", cookie_name="session1"
)
session_factory_2 = SignedCookieSessionFactory("secret2", cookie_name="session2")
session_factory_3 = SignedCookieSessionFactory("secret3", cookie_name="session3")
