# pyramid_session_multi

Build Status: ![Python package](https://github.com/jvanasco/pyramid_session_multi/workflows/Python%20package/badge.svg)

Provides for making multiple ad-hoc binds of `ISession` compliant Sessions onto
a `request.session_multi` namespace.

# Usage

Include `pyramid_session_multi`, then register some `ISessionFactory` factories
that are compliant with the `ISession` interface -- just like you would with 
Pyramid's built-in `.session` system.


	from pyramid.session import SignedCookieSessionFactory

	session_factory_a = SignedCookieSessionFactory(
		'secret', cookie_name='session_a'
	)
	session_factory_b = SignedCookieSessionFactory(
		'secret', cookie_name='session_b'
	)

    def main(global_config, **settings):
        config = Configurator(settings=settings)
        config.include('pyramid_session_multi')
        pyramid_session_multi.register_session_factory(
        	config, 'session1', session_factory_a
        )
        pyramid_session_multi.register_session_factory(
        	config, 'session2', session_factory_b
        )
        return config.make_wsgi_app()

Note: The second argument to `pyramid_session_multi.register_session_factory`
is a namespace, which we then use to access Session data in views/etc:

    request.session_multi['session1']['foo'] = "bar"
    request.session_multi['session2']['bar'] = "foo"

`pyramid_session_multi` lazily evaluates each Session namespace independently of
each other, so accessing `request.session_multi` will not instantiate any of the
component Sessions.

`pyramid_session_multi` is completely independent of Pyramid's built-in Session
support, so you can still use `request.session` alongside this library!


# Advanced Usage

`register_session_factory` accepts an optional argument: "discriminator".

A "discriminator" is a callable function that will receive a single argument:
the active request.

If the discriminator function returns `True`, the SessionFactory will be invoked
and a Session object will be mounted onto the namespace.

If the discriminator function returns a non-`True` value (e.g. `False` or `None`),
the SessionFactory will NOT be invoked, and `None` will be mounted onto the
session's namespace.

Consider an application that is run on both http and https protocols.  In the
following example, `.session_multi["weak"]` can always be accessed, but
`.session_multi["https_only"]` will only be available on https connections.

	from pyramid.session import SignedCookieSessionFactory

	session_factory_a = SignedCookieSessionFactory(
		'secret', cookie_name='weak_cookie'
	)
	session_factory_b = SignedCookieSessionFactory(
		'secret', cookie_name='secure_cookie', secure=True, httponly=True
	)

	def session_b_discriminator(request):
		if request.scheme == 'https'
			return True
		return False

    def main(global_config, **settings):
        config = Configurator(settings=settings)
        config.include('pyramid_session_multi')
        pyramid_session_multi.register_session_factory(
        	config, 'weak', session_factory_a
        )
        pyramid_session_multi.register_session_factory(
        	config, 'https_only', session_factory_b, discriminator=session_b_discriminator
        )
        return config.make_wsgi_app()
        
With this discriminator in place, `.session_multi["https_only"]` will only be
a Pyramid `ISession` on https connections; on http connections it will be `None`.


# why?

Pyramid ships with support for a single Session, which is bound to
`request.session`. That design is great for many/most web applications, but as
your applications scale, your needs may grow:

* If you have a HTTP site that uses HTTPS for account management, you may need
  to support separate Sessions for HTTP and HTTPS, otherwise a 
  "man in the middle" or network traffic spy could use HTTP cookie to access the
  HTTPS endpoints.
* Client-side Sessions and signed cookies are usually faster, but sometimes you
  have data that needs to be saved as server-side Sessions because it has
  security implications (like a third-party oAuth token) or is too big.
* You may have multiple interconnected apps that each need to save/share
  isolated bits of Session data.

# built-in pyramid_debugtoolbar support!

Just add to your "development.ini" or equivalent configuration method

	debugtoolbar.includes = pyramid_session_multi.debugtoolbar

The debugtoolbar will now have a `SessionMulti` panel which has the following
info:

* configuration data on all Session namespaces
* ingress Request values of all accessed Sessions
* egress Response values of all accessed Sessions

The `SessionMulti` panel can also be enabled to track Sessions on every Request,
regardless of the Sessions being accessed or not.

There are two ways to enable the extended Session display used by the
:guilabel:`SessionMulti` panel.

#.  Under the :guilabel:`Settings` tab in the navigation bar, click the red
    :guilabel:`X` mark. When there is a green :guilabel:`check` mark, each
    request will have the ingress and egress data tracked and displayed on the
    :guilabel:`Settings` panel output regardless of the Session being accessed
    during the request. When there is a red :guilabel:`X` mark, only requests
    which accessed the Session will have the ingress and egress data displayed.

#.  Send a ``pdtb_active`` cookie on a per-request basis.
    This panel's name for cookie activation is "session_multi".


## What does the Panel look like?

![Python package](https://raw.githubusercontent.com/jvanasco/pyramid_session_multi/master/docs/debugtoolbar_panel.png)


# How does this library work?

Instead of registering one Session factory to `request.session`, this library
creates a Request attribute `request.session_multi` and registers the various
session factories to namespaces provided within it.

`request.session_multi` is a special dict that maps the namespace keys to your
`ISession` compliant Sessions.  Sessions are lazily created on-demand, so you
won't incur any costs/cookies/backend-data until you use them.

This should work with most Session libraries written for Pyramid. Pyramid's
session support *mostly* just binds a Session factory to the `request.session`
property.  Most libraries and implementations of Pyramid's `ISession` interface
act completely independent of the framework and implement of their own logic for
detecting changes and deciding what to do when something changes.

This library has been used in production for several years with:

* Pyramid's `SignedCookieSessionFactory`
* [pyramid_session_redis](https://github.com/jvanasco/pyramid_session_redis)


# Miscellaneous

There are a few "safety" checks for conflicts.

1. A `pyramid.exceptions.ConfigurationError` will be raised if a namespace of
   Session factory is null
2. A `pyramid.exceptions.ConfigurationError` will be raised if a namespace or
   factory or cookie name is re-used. 

A given **factory** instance can not be re-used, because that can cause conflicts
with cookies or backend storage keys.

You can re-use a single cookie library/type multiple times by creating a factory
for each setting (see the example above, which re-uses 
`SignedCookieSessionFactory` twice).

If you do not register a factory with a `cookie_name`, this library will
try to derive one based on a `._cooke_name` attribute.  If neither option is
available, an Exception will be raised on configuration.

# What if Sessions should only run in certain situations?

`register_session_factory` accepts a kwarg for `discriminator`, which is a
function that expects a single argument of a `Request` object.

If provided and the discriminator function returns an non-``True`` value, the
`.session_multi` namespace will be set to `None`, otherwise the namespace will be
populated with the result of the factory.

License
=======

MIT
