.. meta::
    :description: Reference for the attenuations module, which enumerates permissions for macaroons. Craft apps can use these constants in account queries to artifact stores.

.. _reference-attenuations:

Attenuations
************

Attenuations are permissions that restrict what a discharged macaroon token can do. When
an app makes an account request, with credentials, to the Snap Store or Charmhub, it
passes a list of attenuations that limits the capabilities of those credentials.

All constants are available in the ``craft_store.attenuations`` module.

.. currentmodule:: craft_store.attenuations

Read-write attenuations
=======================

.. autodata:: ACCOUNT_MANAGE_KEYS
.. autodata:: ACCOUNT_MANAGE_METADATA
.. autodata:: ACCOUNT_REGISTER_PACKAGE
.. autodata:: PACKAGE_MANAGE
.. autodata:: PACKAGE_MANAGE_ACL
.. autodata:: PACKAGE_MANAGE_LIBRARY
.. autodata:: PACKAGE_MANAGE_METADATA
.. autodata:: PACKAGE_MANAGE_RELEASES
.. autodata:: PACKAGE_MANAGE_REVISIONS
.. autodata:: STORE_MANAGE

Read-only attenuations
======================

.. autodata:: ACCOUNT_VIEW_PACKAGES
.. autodata:: PACKAGE_VIEW
.. autodata:: PACKAGE_VIEW_ACL
.. autodata:: PACKAGE_VIEW_METADATA
.. autodata:: PACKAGE_VIEW_METRICS
.. autodata:: PACKAGE_VIEW_RELEASES
.. autodata:: PACKAGE_VIEW_REVISIONS
.. autodata:: STORE_VIEW
