.. _migrate-to-publisher-gateway:

Migrating from BaseClient to PublisherGateway
**********************************************

This guide shows how to migrate from the legacy BaseClient API to the new
PublisherGateway API, which provides a modern, type-safe interface to the
Canonical Publisher Gateway.

Overview
========

The new PublisherGateway API offers several advantages over the legacy BaseClient:

- **Modern HTTP client**: Uses httpx instead of requests
- **Type safety**: Full Pydantic model validation for requests and responses
- **Complete API coverage**: All Publisher Gateway endpoints are now available
- **Minimal interface**: Hides unnecessary dict manipulation from users
- **Better error handling**: Consistent error patterns across all endpoints

Setting up PublisherGateway
===========================

Basic Setup
-----------

.. code-block:: python

    from craft_store.publisher import PublisherGateway
    from craft_store.auth import Auth

    # Initialize authentication
    auth = Auth(
        application_name="my-craft-app",
        host="api.charmhub.io",
        environment_auth="CHARMCRAFT_AUTH"
    )

    # Create publisher gateway instance
    gateway = PublisherGateway(
        base_url="https://api.charmhub.io",
        namespace="charm",  # or "snap" for snap store
        auth=auth
    )

Authentication Migration
========================

Macaroon Operations
-------------------

**Legacy BaseClient approach:**

.. code-block:: python

    # Old way - using BaseClient.login()
    client = StoreClient(...)
    credentials = client.login(
        permissions=["package-upload"],
        description="My app",
        ttl=3600
    )

**New PublisherGateway approach:**

.. code-block:: python

    from craft_store.publisher import MacaroonRequest

    # New way - explicit macaroon management
    # Get existing macaroons
    existing_macaroons = gateway.get_macaroon(include_inactive=False)

    # Or issue a new macaroon
    request = MacaroonRequest(
        permissions=["package-upload"],
        description="My app",
        ttl=3600
    )
    macaroon_response = gateway.issue_macaroon(request)

**Additional macaroon operations now available:**

.. code-block:: python

    from craft_store.publisher import ExchangeMacaroonRequest

    # Exchange macaroons
    exchange_request = ExchangeMacaroonRequest(macaroon="discharged-macaroon")
    exchanged = gateway.exchange_macaroons(exchange_request)

    # Revoke macaroons - simplified to pass session ID directly
    gateway.revoke_macaroon("session-123")

    # Get macaroon info
    info = gateway.macaroon_info()

    # Exchange dashboard SSO macaroons - simplified with optional description
    developer_token = gateway.exchange_dashboard_macaroons(
        "dashboard-sso-macaroons",
        description="My CLI Tool"
    )

    # Offline macaroon exchange (for local publishing) - simplified
    offline_token = gateway.offline_exchange_macaroon("macaroon-to-exchange")

Package Management Migration
============================

Upload Operations
-----------------

**Legacy BaseClient approach:**

.. code-block:: python

    # Old way
    upload_id = client.upload_file(filepath=Path("my-package.charm"))

    # Push revision
    revision_response = client.notify_revision(
        name="my-package",
        revision_request=RevisionsRequestModel(upload_id=upload_id)
    )

**New PublisherGateway approach:**

.. code-block:: python

    from craft_store.publisher import PushRevisionRequest
    from pathlib import Path

    # New way - with type safety
    upload_id = gateway.upload_file(Path("my-package.charm"))

    request = PushRevisionRequest(upload_id=upload_id)
    response = gateway.push_revision("my-package", request)

Resource Management Migration
=============================

Resource Operations
-------------------

**Legacy BaseClient approach:**

.. code-block:: python

    # Old way
    status_url = client.push_resource(
        name="my-package",
        resource_name="my-resource",
        upload_id=upload_id,
        resource_type="file"
    )

    # List resource revisions
    revisions = client.list_resource_revisions("my-package", "my-resource")

**New PublisherGateway approach:**

.. code-block:: python

    from craft_store.publisher import PushResourceRequest

    # New way - with structured requests
    request = PushResourceRequest(
        upload_id=upload_id,
        type="file"
    )
    response = gateway.push_resource("my-package", "my-resource", request)

    # List all resources for a package - returns a list directly
    resources = gateway.list_resources("my-package")
    for resource in resources:
        print(f"{resource.name}: {resource.type}")

    # List resources for a specific revision
    resources = gateway.list_resources("my-package", revision=123)

    # List specific resource revisions
    revisions = gateway.list_resource_revisions("my-package", "my-resource")

**Resource revision updates:**

.. code-block:: python

    from craft_store.publisher import ResourceRevisionUpdateRequest

    # Update resource revisions with new bases
    updates = [
        ResourceRevisionUpdateRequest(
            revision=1,
            bases=[{"name": "ubuntu", "channel": "20.04"}]
        ),
        ResourceRevisionUpdateRequest(
            revision=2,
            bases=[{"name": "ubuntu", "channel": "22.04"}]
        )
    ]

    result = gateway.update_resource_revisions(
        "my-package",
        "my-resource",
        updates
    )
    print(f"Updated {result.num_resource_revisions_updated} revisions")

New Features Available
======================

Package Metadata Updates
-------------------------

The new API provides direct package metadata management:

.. code-block:: python

    from craft_store.publisher import UpdatePackageMetadataRequest, PackageLinks

    # Simple metadata update
    metadata_request = UpdatePackageMetadataRequest(
        summary="Updated package summary",
        description="Updated package description",
        default_track="latest"
    )

    # Or with complex links structure
    metadata_request = UpdatePackageMetadataRequest(
        summary="Updated package summary",
        description="Updated package description",
        links=PackageLinks(
            website=["https://example.com"],
            contact=["maintainer@example.com"],
            docs=["https://docs.example.com"]
        )
    )

    gateway.update_package_metadata("my-package", metadata_request)

Upload Reviews
--------------

Monitor upload review status:

.. code-block:: python

    # List upload reviews for a package - returns a list directly
    reviews = gateway.list_upload_reviews("my-package")

    for review in reviews:
        print(f"Upload {review.upload_id}: {review.status}")
        if review.errors:
            for error in review.errors:
                print(f"  Error: {error.message}")

    # Or check a specific upload
    specific_reviews = gateway.list_upload_reviews("my-package", upload_id="upload-123")

OCI Image Resources
-------------------

New support for OCI image resources:

.. code-block:: python

    # Get upload credentials for OCI images (no request needed)
    credentials = gateway.oci_image_resource_upload_credentials(
        "my-package",
        "my-resource"
    )
    print(f"Image: {credentials.image_name}")
    print(f"Username: {credentials.username}")
    # Use credentials.password for authentication

    # Handle OCI image blobs - simplified to pass digest directly
    blob_response = gateway.oci_image_resource_blob(
        "my-package",
        "my-resource",
        "sha256:abc123..."
    )
    print(f"Access image: {blob_response.image_name}")

Error Handling
==============

The PublisherGateway maintains the same error handling patterns:

.. code-block:: python

    from craft_store import errors

    try:
        response = gateway.push_revision("my-package", request)
    except errors.CraftStoreError as e:
        print(f"Store error: {e}")
        if hasattr(e, 'store_errors') and e.store_errors:
            for error_code, error_info in e.store_errors.items():
                print(f"  {error_code}: {error_info}")
    except errors.NetworkError as e:
        print(f"Network error: {e}")

Migration Checklist
===================

When migrating your code:

1. **✓ Replace StoreClient/BaseClient imports** with PublisherGateway
2. **✓ Update authentication** to use explicit macaroon requests
3. **✓ Replace direct dict usage** with Pydantic request models
4. **✓ Update upload workflows** to use new structured approaches
5. **✓ Take advantage of new features** like metadata updates and OCI support
6. **✓ Update error handling** if you were catching specific exceptions
7. **✓ Update tests** to use the new API patterns
