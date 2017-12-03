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



License
=======

MIT
