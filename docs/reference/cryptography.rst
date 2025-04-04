.. _reference_cryptography:

Cryptographic Documentation
===========================

Craft Store uses cryptographic processes to send files to and from the internet. It does
not directly implement its own cryptography, but it does depend on external libraries to
do so.

Authentication
--------------

Craft Store handles repeated authentication via macaroons, which are processed by the
`macaroonbakery <https://pypi.org/project/macaroonbakery/>`_ library. This library
validates and manages macaroons as returned by storefronts and simplifies the inclusion
of macaroons in further requests to storefronts.

Credentials may additionally be stored on-disk using the `keyring
<https://pypi.org/project/keyring/>`_ library, which will use the keyring service
provided by the host operating system. If the host OS does not have a keyring service,
they will instead be stored in a plain text file called :file:`credentials.json` under
the application's data storage directory. A warning is issued to the terminal when this
behavior is triggered. This behavior is available to ease the usage of Craft Store
within CI containers, but is generally discouraged.

Network connections
-------------------

Craft Store handles URLs using `urllib
<https://docs.python.org/3/library/urllib.html>`_. The use of this library both
simplifies and hardens the parsing of URLs provided by consuming applications.

Connections over the internet are done by the `requests
<https://requests.readthedocs.io/en/latest/>`_ or `httpx
<https://www.python-httpx.org/>`_ libraries, which are configured to always
attempt HTTPS connections first, but have the ability to communicate over HTTP
as a fallback. Canonical storefronts do not support HTTP, but this capability
is kept in to aid with local testing. The distinction of which library is used
depends on the request object provided by an application using this library.
These libraries handle cryptographic operations such as the TLS handshake that
are standard requirements for modern internet communication.
