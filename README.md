# pyramid_session_multi

Provides for making ad-hoc sessions binds of ISession compliant libraries.

This is just a quick first attempt.

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
    

# how does it work?

Instead of registering one session factory to `request.session`, the library creates a namespace `request.session_multi` and registers the session factories to namespaces provided in it.

`request.session_multi` is a special dict that maps the namespace keys to sessions.  sessions are lazily created on-demand, so you won't incur any costs/cookies/backend-data until you use them.

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
