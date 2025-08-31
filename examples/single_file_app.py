"""
Directions:

Install the required libraries:

    pip install pyramid
    pip install pyramid_session_multi
    pip install pyramid_session_redis

Run the app:

    python single_file_app.py

In another window, make some requests:

    curl http://0.0.0.0:6543 -I
    curl http://0.0.0.0:6543 -I
    curl http://0.0.0.0:6543 -I
    curl http://0.0.0.0:6543 -I

You should see some lines pop up in the first window:

    Incoming request
    Session Values
    ('clientside', 1)
    ('serverside', 2)

These will not change between requests, because we don't pass in the Session
identifiers, so state does not increase.

Look back at the first window.

Note there are two set-cookie values:

    Set-Cookie: client_cookie=vMfpxvLwGD9OkGO1Wwek_jke_eohqLOg0fUfCrdJYr0DtTXth3r74CMvvn2chreEGGxokL7gLUyRexCcpEdcrIACSgRetF9HQdftF4EjDa59cQFVAmlkcQJLAXOHcQMu; Path=/; SameSite=Lax
    Set-Cookie: server_cookie=8ae9bf114ddd46d6d20cfe17345f5500f8218febgAJVQEQxNjk2aHZhV252ZDZmUS1mck9rYTUzdUlxcGxXODJtbVcxaDN4OWRUTzYwZ1BkamYyZm8wdE1lMVBqOUVWQU1xAS4=; Path=/; HttpOnly
    Vary: Cookie

Try sending in the values on the next request for the clientside cookie

    curl http://0.0.0.0:6543 -I -H "Cookie: client_cookie=vMfpxvLwGD9OkGO1Wwek_jke_eohqLOg0fUfCrdJYr0DtTXth3r74CMvvn2chreEGGxokL7gLUyRexCcpEdcrIACSgRetF9HQdftF4EjDa59cQFVAmlkcQJLAXOHcQMu"
    curl http://0.0.0.0:6543 -I -H "Cookie: client_cookie=vMfpxvLwGD9OkGO1Wwek_jke_eohqLOg0fUfCrdJYr0DtTXth3r74CMvvn2chreEGGxokL7gLUyRexCcpEdcrIACSgRetF9HQdftF4EjDa59cQFVAmlkcQJLAXOHcQMu"
    curl http://0.0.0.0:6543 -I -H "Cookie: client_cookie=vMfpxvLwGD9OkGO1Wwek_jke_eohqLOg0fUfCrdJYr0DtTXth3r74CMvvn2chreEGGxokL7gLUyRexCcpEdcrIACSgRetF9HQdftF4EjDa59cQFVAmlkcQJLAXOHcQMu"

Note that you always see these lines in the first window:

    ('clientside', 1)
    ...
    ('clientside', 1)
    ...
    ('clientside', 1)

This is because the clientside cookie's data is all contained within the cookie.
To see the state change, you need to take the response's `Set-Cookie: ` value for
each request, and send it into the next request as a `Cookie: ` header.

Now let's do that with the serverside cookie:

    curl http://0.0.0.0:6543 -I -H "Cookie: server_cookie=8ae9bf114ddd46d6d20cfe17345f5500f8218febgAJVQEQxNjk2aHZhV252ZDZmUS1mck9rYTUzdUlxcGxXODJtbVcxaDN4OWRUTzYwZ1BkamYyZm8wdE1lMVBqOUVWQU1xAS4"
    curl http://0.0.0.0:6543 -I -H "Cookie: server_cookie=8ae9bf114ddd46d6d20cfe17345f5500f8218febgAJVQEQxNjk2aHZhV252ZDZmUS1mck9rYTUzdUlxcGxXODJtbVcxaDN4OWRUTzYwZ1BkamYyZm8wdE1lMVBqOUVWQU1xAS4"
    curl http://0.0.0.0:6543 -I -H "Cookie: server_cookie=8ae9bf114ddd46d6d20cfe17345f5500f8218febgAJVQEQxNjk2aHZhV252ZDZmUS1mck9rYTUzdUlxcGxXODJtbVcxaDN4OWRUTzYwZ1BkamYyZm8wdE1lMVBqOUVWQU1xAS4"

You should see two very different behaviors:

1. The serverside value increments

    ('serverside', 2)
    ...
    ('serverside', 4)
    ...
    ('serverside', 8)

2. The response only includes a `Set-Cookie:` header for the client cookie

Both of these results are because the ServerSide cookie only contains a signed
version of the session id. The session data is all contained on the server.
Because of this, the server_side cookie will not change value unless the
cookie receives an updated timeout value or an invalidation.
"""

# pypi
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.response import Response
from pyramid.session import SignedCookieSessionFactory
import pyramid_session_redis
from waitress import serve

# local
import pyramid_session_multi


def func_invalid_logger(
    request: Request,
    raised_exception: Exception,
):
    """called by func_invalid_logger"""
    print("func_invalid_logger")
    print(request, raised_exception)


factory_clientside = SignedCookieSessionFactory("secret", cookie_name="client_cookie")
factory_serverside = pyramid_session_redis.session_factory_from_settings(
    {
        "redis.sessions.secret": "secret",
        "redis.sessions.cookie_name": "server_cookie",
        "redis.sessions.func_invalid_logger": func_invalid_logger,
    }
)


def hello_world(request: Request) -> Response:
    print("Incoming request")
    if "id" not in request.session_multi["clientside"]:
        request.session_multi["clientside"]["id"] = 0
    request.session_multi["clientside"]["id"] += 1
    if "id" not in request.session_multi["serverside"]:
        request.session_multi["serverside"]["id"] = 0
    request.session_multi["serverside"]["id"] += 2

    print("Session Values:")
    print("\tclientside", request.session_multi["clientside"]["id"])
    print("\tserverside", request.session_multi["serverside"]["id"])

    return Response("<body><h1>Hello World!</h1></body>")


if __name__ == "__main__":
    with Configurator() as config:
        config.add_route("hello", "/")
        config.add_view(hello_world, route_name="hello")

        config.include("pyramid_session_multi")
        pyramid_session_multi.register_session_factory(
            config, "clientside", factory_clientside
        )
        pyramid_session_multi.register_session_factory(
            config, "serverside", factory_serverside, cookie_name="server_cookie"
        )
        app = config.make_wsgi_app()
    serve(app, host="0.0.0.0", port=6543)
