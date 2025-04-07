.. _explanation_cryptographic-technology:

Cryptographic technology in Craft Store
=======================================

Craft Store uses cryptographic processes to send files between devices and endpoints
through the internet. It does not directly implement its own cryptography, but it does
depend on external libraries to do so.

Authentication
--------------

Craft Store uses `macaroons`_, as an authentication mechanism, which are processed by
the `macaroonbakery <https://pypi.org/project/macaroonbakery/>`_ library. This library
validates and manages macaroons as returned by stores and simplifies the inclusion of
macaroons in further requests to stores.

Credentials may additionally be stored on-disk using the `keyring
<https://pypi.org/project/keyring/>`_ library, which will use the keyring service
provided by the host operating system. If the host does not have a keyring service, they
will instead be stored in a plain text file called :file:`credentials.json` under the
application's data storage directory. A warning is issued to the terminal when this
behavior is triggered. This behavior is available to ease the usage of Craft Store
inside virtual machines and containers, but is generally discouraged.

Network connectivity
--------------------

Craft Store handles URLs using `urllib
<https://docs.python.org/3/library/urllib.html>`_. The use of this library both
simplifies and hardens the parsing of URLs provided by consuming applications.

Connections over the internet are mediated by the `requests
<https://requests.readthedocs.io/en/latest/>`_ or `httpx
<https://www.python-httpx.org/>`_ libraries. These libraries handle cryptographic
operations such as the TLS handshake that are standard requirements for modern internet
connections. These are configured to always attempt HTTPS connections first, but have
the ability to communicate over HTTP as a fallback. Canonical storefronts do not support
HTTP, but this capability is retained to aid with local testing. Between these two
libraries, Craft Store will use whichever of the two is invoked by the consuming
application.

.. _macaroons: https://research.google/pubs/macaroons-cookies-with-contextual-caveats-for-decentralized-authorization-in-the-cloud/
