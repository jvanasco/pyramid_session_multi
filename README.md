# pyramid_session_multi

Provides for making multiple ad-hoc binds of `ISession` compliant sessions onto a `request.session_multi` namespace

This was just a quick first attempt, but it's working well!

# usage

include pyramid_session_multi, then register some factories

    def main(global_config, **settings):
        config = Configurator(settings=settings)
        config.include('pyramid_session_multi')

        my_session_factory = SignedCookieSessionFactory('itsaseekreet', cookie_name='a_session')
        pyramid_session_multi.register_session_factory(config, 'session1', my_session_factory)

        my_session_factory2 = SignedCookieSessionFactory('esk2', cookie_name='another_session')
        pyramid_session_multi.register_session_factory(config, 'session2', my_session_factory2)
        return config.make_wsgi_app()

Note: The second argument to `pyramid_session_multi.register_session_factory` is a namespace, which we then use to access session data in views/etc:

    request.session_multi['session1']['foo'] = "bar"
    request.session_multi['session1']['bar'] = "foo"

# why?

Pyramid ships with support for a single session, which is bound to `request.session`. That design is great for many/most web applications, but as you scale your needs may grow:

* If you have a HTTP site that uses HTTPS for account management, you may need to support separate sessions for HTTP and HTTPS, otherwise a "man in the middle" or network traffic spy could use HTTP cookie to access the HTTPS endpoints.
* Client-side sessions and signed cookies are usually faster, but sometimes you have data that needs to be saved as server-side sessions because it has security implications (like a third-party oAuth token) or is too big.
* You may have multiple interconnected apps that each need to save/share isolated bits of session data.


# pyramid_debugtoolbar support!

Just add to your "development.ini" or equivalent configuration method

	debugtoolbar.includes = pyramid_session_multi.debugtoolbar

The debugtoolbar will now have a `SessionMulti` panel that has the following info:

* configuration data on all namespaces
* incoming request values of all available sessions
* outgoing response values of accessed sessions (not necessarily updated)

WARNING- the in/out functionality is supported by reading the session info WITHOUT binding it to the request.  For most implementations, this is fine and will go unnoticed.  Some session implementations will trigger an event on the "read" of the session (such as updating a timestamp, setting callbacks, etc); those events will be triggered by the initial read.

If possible, register sessions with a `cookie_name` parameter for the toolbar.  If omitted, the manager will try to pull a name from the factory - but that is not always possible.


# how does it work?

Instead of registering one session factory to `request.session`, this library creates a namespace `request.session_multi` and registers the session factories to namespaces provided witin it.

`request.session_multi` is a special dict that maps the namespace keys to your `ISession` sessions.  Sessions are lazily created on-demand, so you won't incur any costs/cookies/backend-data until you use them.

This should work with most session libraries written for Pyramid. Pyramid's session support *mostly* just binds a session factory to the `request.session` property.  Most libraries and implementations of Pyramid's `ISession` interface act completely independent of the framework and implement of their own logic for detecting changes and deciding what to do when something changes.

# misc

There are a few "safety" checks for conflicts.

1. A `pyramid.exceptions.ConfigurationError` will be raised if a namespace of session factory is null
2. A `pyramid.exceptions.ConfigurationError` will be raised if a namespace or factory is re-used. 

The **factory** can not be re-used, because that can cause conflicts with cookies or backend storage keys.
You can use a single cookie library/type multiple times by creating a factory for each setting (see the example above, which re-uses `SignedCookieSessionFactory` twice).

# what if sessions should only run in certain situations?

`register_session_factory` accepts a kwarg for `discriminator`, which is a function that expects a `request` object.
If provided and the discriminator function returns an non-True value, the session_multi namespace will be set to `None`, otherwise the namespace will be populated with the result of the factory.

License
=======

MIT
