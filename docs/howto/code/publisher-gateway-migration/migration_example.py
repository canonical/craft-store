#!/usr/bin/env python3
"""
Migration example: BaseClient to PublisherGateway

This example shows how to migrate common operations from the legacy BaseClient
API to the new PublisherGateway API.
"""

from pathlib import Path
from craft_store.publisher import (
    PublisherGateway,
    Permission,
    ResourceType,
    BaseDict,
)
from craft_store.auth import Auth


def legacy_approach():
    """Example of the old BaseClient approach."""

    from craft_store import StoreClient, endpoints

    client = StoreClient(
        base_url="https://api.charmhub.io",
        storage_base_url="https://storage.charmhub.io",
        endpoints=endpoints.CHARMHUB,
        application_name="my-app",
        user_agent="my-app/1.0",
    )

    credentials = client.login(
        permissions=["package-upload"],
        description="My app login",
        ttl=3600
    )
    print(f"Legacy login successful: {len(credentials)} credential items")

    upload_id = client.upload_file(filepath=Path("my-package.charm"))

    from craft_store.models.revisions_model import RevisionsRequestModel
    revision_request = RevisionsRequestModel(upload_id=upload_id)
    response = client.notify_revision(name="my-package", revision_request=revision_request)

    return response


def modern_approach():
    """Example of the new PublisherGateway approach."""

    auth = Auth(
        application_name="my-app",
        host="api.charmhub.io",
        environment_auth="CHARMCRAFT_AUTH"
    )

    gateway = PublisherGateway(
        base_url="https://api.charmhub.io",
        namespace="charm",
        auth=auth
    )

    macaroon_response = gateway.issue_macaroon(
        permissions=[Permission.PACKAGE_MANAGE],
        description="My app login",
        ttl=3600
    )
    print(f"Macaroon issued successfully: {macaroon_response.macaroon[:20]}...")

    upload_id = gateway.upload_file(Path("my-package.charm"))

    response = gateway.push_revision("my-package", upload_id=upload_id)

    return response


def complete_workflow_example():
    """Complete workflow using the new PublisherGateway API."""

    auth = Auth(
        application_name="craft-app",
        host="api.charmhub.io",
        environment_auth="CHARMCRAFT_AUTH"
    )

    gateway = PublisherGateway(
        base_url="https://api.charmhub.io",
        namespace="charm",
        auth=auth
    )

    package_name = "my-awesome-package"

    upload_id = gateway.upload_file(Path("my-package.charm"))

    push_response = gateway.push_revision(package_name, upload_id=upload_id)

    print(f"Revision pushed. Status URL: {push_response.status_url}")

    gateway.update_package_metadata(
        package_name,
        summary="An awesome package for doing awesome things",
        description="This package provides utilities for...",
        contact="maintainer@example.com",
        website="https://github.com/example/my-package"
    )
    print("Package metadata updated")

    resource_upload_id = gateway.upload_file(Path("my-resource.tar.gz"))

    resource_response = gateway.push_resource(
        package_name,
        "my-resource",
        upload_id=resource_upload_id,
        resource_type=ResourceType.FILE
    )
    print(f"Resource pushed. Status URL: {resource_response.status_url}")

    resources = gateway.list_resources(package_name)
    print(f"Package has {len(resources)} resources")

    revisions = gateway.list_resource_revisions(package_name, "my-resource")
    print(f"Resource has {len(revisions)} revisions")

    if revisions:
        updates: list[tuple[int, list[BaseDict]]] = [
            (revisions[0].revision, [
                {"name": "ubuntu", "channel": "20.04", "architectures": ["amd64"]},
                {"name": "ubuntu", "channel": "22.04", "architectures": ["amd64", "arm64"]}
            ])
        ]

        update_response = gateway.update_resource_revisions(
            package_name,
            "my-resource",
            updates
        )
        print(f"Updated {update_response.num_resource_revisions_updated} revisions")

    reviews = gateway.list_upload_reviews(package_name)
    for review in reviews:
        print(f"Upload {review.upload_id}: {review.status}")
        if review.errors:
            for error in review.errors:
                print(f"  Error: {error.message}")

    releases = gateway.list_releases(package_name)
    print(f"Package has {len(releases.channel_map)} channel mappings")
    print(f"Package has {len(releases.revisions)} total revisions")

    return "Workflow completed successfully!"


if __name__ == "__main__":
    print("=== PublisherGateway Migration Example ===")
    print("\nThis example shows the modern PublisherGateway API.")
    print("See the documentation for complete migration guide.")
    print("\nTo run this example, ensure you have valid credentials set up.")

    # Uncomment to run the examples:
    # modern_approach()
    # complete_workflow_example()
