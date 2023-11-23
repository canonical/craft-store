*********
Changelog
*********
2.5.0 (2023-11-23)
------------------

- Add a fallback mechanism for when the system keyring fails, such as
  the Secret Service keyring (gnome-keyring). The fallback is to write
  to a file based backend, provided by
  :class:`craft_store.auth.FileKeyring`
- Removed setup.cfg, fully using pyproject.toml

2.4.0 (2023-04-13)
------------------

- Add support for registering, unregistering, and listing names, with usage
  examples in `integration tests
  <https://github.com/canonical/craft-store/blob/main/tests/integration
  /test_register_unregister.py>`_.

  - :class:`craft_store.base_client.BaseClient.register_name`
  - :class:`craft_store.base_client.BaseClient.unregister_name`
  - :class:`craft_store.base_client.BaseClient.list_registered_names`
- Handle keyring unlocking errors

`Full Changelog
<https://github.com/canonical/craft-store/compare/2.3.0...v2.4.0>`_

2.3.0 (2022-10-07)
------------------

- Add support for exporting the new credentials format (which is backwards
  compatible with the existing one)

2.2.1 (2022-08-25)
------------------

- Export :class:`craft_store.models.SnapListReleasesModel` and
  :class:`craft_store.models.CharmListReleasesModel`
- Remove incorrectly exported ``SnapChannelMapModel`` and
  ``CharmChannelMapModel``
- Make bases optional in :class:`craft_store.models.SnapListReleasesModel`

2.2.0 (2022-08-11)
------------------

- Refactor common code in ``endpoints``
- Export new symbols in craft_store.models:

  - :class:`craft_store.models.CharmChannelMapModel`
  - :class:`craft_store.models.MarshableModel`
  - :class:`craft_store.models.ReleaseRequestModel`
  - :class:`craft_store.models.RevisionsRequestModel`
  - :class:`craft_store.models.RevisionsResponseModel`
  - :class:`craft_store.models.SnapChannelMapModel`

- Catch the correct :class:`JSONDecodeError`


2.1.1 (2022-04-26)
------------------

- Update macaroon refresh logic for :class:`craft_store.UbuntuOneStoreClient`

2.1.0 (2022-03-19)
------------------

- Support for ephemeral logins in :class:`craft_store.BaseClient`
- New endpoint to complete the upload experience
  :meth:`craft_store.BaseClient.notify_revision`
- New endpoint to release :meth:`craft_store.BaseClient.release` and retrieve
  release information :meth:`craft_store.BaseClient.get_list_releases`
- Support for Python 3.10

2.0.1 (2022-02-10)
------------------

- Convert login expiration to a ISO formatted datetime for Ubuntu endpoints
- Raise :class:`craft_store.errors.CredentialsNotParseable` on base64 decode
  errors
- Use network location as keyring storage location instead of full base url in
  :class:`craft_store.base_client.BaseClient`

2.0.0 (2022-02-07)
------------------

- New endpoint for uploads to storage,
  :class:`craft_store.StoreClient` and
  :class:`craft_store.UbuntuOneStoreClient` require a
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
  :class:`craft_store.UbuntuOneStoreClient`

1.1.0 (2021-11-19)
------------------

- Support for channels and packages in endpoints
- :class:`craft_store.store_client.StoreClient` support for retrieving
  credentials from an environment variable
- Login credentials now returned from
  :meth:`craft_store.BaseClient.login`


1.0.0 (2021-10-21)
------------------

- Initial release
