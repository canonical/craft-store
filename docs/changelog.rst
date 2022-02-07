*********
Changelog
*********

2.0.0 (2022-02-07)
------------------

- New endpoint for uploads to storage,
  :class:`craft_store.store_client.StoreClient` and
  :class:`craft_store.ubuntu_one_store_client.UbuntuOneStoreClient` require a
  new initialization new parameter
- Setting credentials while credentials are already set is no longer allowed
  :class:`craft_store.errors.CredentialsAlreadyAvailable` is raised if
  credentials already exist
- NotLoggedIn exception renamed to
  :class:`craft_store.errors.CredentialsUnavailable`
- Early checks are now in place for keyring availability before a login attempt
  takes place

1.2.0 (2021-12-09)
------------------

- New whoami endpoint for :class:`craft_store.endpoints.CHARMHUB`
- New class to provide login support for Ubuntu One SSO
  :class:`craft_store.ubuntu_one_store_client.UbuntuOneStoreClient`

1.1.0 (2021-11-19)
------------------

- Support for channels and packages in endpoints
- :class:`craft_store.store_client.StoreClient` support for retrieving
  credentials from an environment variable
- Login credentials now returned from
  :meth:`craft_store.store_client.StoreClient.login()`


1.0.0 (2021-10-21)
------------------

- Initial release
