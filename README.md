# pyramid_session_multi

Provides for making ad-hoc sessions binds of ISession compliant libraries.

This was just a quick first attempt, but it's working well

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

Note how the second argument to `pyramid_session_multi.register_session_factory` is a namespace, which we then use to access session data in views/etc...

    request.session_multi['session1']['foo'] = "bar"
    request.session_multi['session1']['bar'] = "foo"

# why?

pyramid ships with support for a single session that is bound to `request.session`. that design is great for many/most web applications, but as you scale your needs may grow:

* if you have a HTTP site that uses HTTPS for account management, you need to support separate sessions for HTTP and HTTPS, otherwise a "man in the middle" or network traffic spy could use HTTP cookie to access the HTTPS endpoints.
* clientside sessions and signed cookies are usually faster, but sometimes you have data that needs to be saved serverside sessions because it has security implications (like a 3rd party oAuth token) or is too big.
* you may have multiple interconnected apps that each need to save/share isolated bits of session data.


# debugtoolbar support!

just add to your development.ini

	debugtoolbar.includes = pyramid_session_multi.debugtoolbar

the debugtoolbar will now have a `SessionMulti` panel that has the following info:

* configuration data on all namespaces
* incoming request values of all available sessions
* outgoing response values of accessed sessions (not necessarily updated)

WARNING- the in/out functionality is supported by reading the session info WITHOUT binding it to the request.  for most implementations, this is fine and will go unnoticed.  some session implementations will trigger an event on the "read" of the session (such as updating a timestamp, setting callbacks, etc).  those events will be triggered by the initial read.

if possible, register sessions with a cookie_name paramter for the toolbar. if omitted, the manager will try to pull a name from the factory - but that is not always possible.


# how does it work?

Instead of registering one session factory to `request.session`, the library creates a namespace `request.session_multi` and registers the session factories to namespaces provided in it.

`request.session_multi` is a special dict that maps the namespace keys to sessions.  sessions are lazily created on-demand, so you won't incur any costs/cookies/backend-data until you use them.

this should work with most session libraries for Pyramid. pyramid's session support *mostly* just binds a session factory to the `request.session` property.  most libraries and implementations of pyramid's ISession interface act completely independent of the framework and implement of their own logic for detecting changes and deciding what to do when something changes.

# misc

There are a few "safety" checks for conflicts.

1. A `pyramid.exceptions.ConfigurationError` will be raised if a namespace of session factory is null
2. A `pyramid.exceptions.ConfigurationError` will be raised if a namespace or factory is re-used. 

the **factory** can not be re-used, because that can cause conflicts with cookies or backend storage keys.
you can use a single cookie library/type multiple times by creating a factory for each setting (see the example above, which re-uses `SignedCookieSessionFactory` twice).

# what if sessions should only run in certain situations?

`register_session_factory` accepts a kwarg for `discriminator`, which is a function that expects a `request` object.
if provided and the discriminator function returns an non-True value, the session_multi namespace will be set to None
otherwise, the namespace will be populated with the result of the factory

License
=======

MIT
