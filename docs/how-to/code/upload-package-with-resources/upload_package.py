#!/usr/bin/env python3
"""Demo code for uploading a charm to Charmhub."""
import argparse
import pathlib
import sys
import time
from typing import Any

from craft_store import endpoints, StoreClient
from craft_store.models import (
    RevisionsRequestModel,
    ReleaseRequestModel,
    ResourceModel,
    CharmResourceType,
)


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="upload_package",
        description="Uploads a charm and its resource",
    )
    parser.add_argument(
        "charm_name",
        help="The name of the charm in the store",
    )
    parser.add_argument(
        "resource_name",
        help="The name of the resource in the store",
    )
    parser.add_argument(
        "--charm",
        type=pathlib.Path,
        required=True,
        help="The path of the charm to upload",
    )
    parser.add_argument(
        "--resource",
        type=pathlib.Path,
        required=True,
        help="The path of the resource file to upload",
    )
    return parser.parse_args(argv)


def check_status(client: StoreClient, status_url: str) -> list[dict[str, Any]]:
    """Check the status of an upload."""
    timeout = time.monotonic() + 120
    while time.monotonic() < timeout:
        resource_status = client.request("GET", status_url).json()
        done = True
        for resource_revision_status in resource_status["revisions"]:
            if resource_revision_status["status"] not in ("approved", "rejected"):
                done = False
        if done:
            return resource_status["revisions"]
        time.sleep(3)
    raise TimeoutError("Status was neither approved nor rejected after 120s")


def main(argv: list[str]):
    args = parse_args(argv)
    charm_path = args.charm.expanduser().resolve()
    resource_path = args.resource.expanduser().resolve()
    charm_name = args.charm_name
    resource_name = args.resource_name

    # [docs:get-client]
    base_url: str = "https://api.staging.charmhub.io"
    storage_base_url: str = "https://storage.staging.snapcraftcontent.com"
    client = StoreClient(
        application_name="craft-store-demo",
        base_url=base_url,
        storage_base_url=storage_base_url,
        endpoints=endpoints.CHARMHUB,
        user_agent="craft-store-demo-app",
        environment_auth="CRAFT_STORE_CHARMCRAFT_CREDENTIALS",
    )
    # [docs:get-client-end]
    # [docs:upload-resource]
    resource_upload_id = client.upload_file(filepath=resource_path)
    resource_status_url = client.push_resource(
        name=charm_name,
        resource_name=resource_name,
        upload_id=resource_upload_id,
        resource_type=CharmResourceType.FILE,
    )
    resource_status = check_status(client, base_url + resource_status_url)[0]
    resource_revision = int(resource_status["revision"])
    # [docs:upload-resource-end]
    # [docs:upload-charm]
    charm_upload_id = client.upload_file(filepath=charm_path)
    charm_status_url = client.notify_revision(
        name=charm_name,
        revision_request=RevisionsRequestModel(upload_id=charm_upload_id),
    ).status_url
    charm_status = check_status(client, base_url + charm_status_url)[0]
    charm_revision = charm_status["revision"]
    # [docs:upload-charm-end]

    # [docs:release]
    client.release(
        name=charm_name,
        release_request=[
            ReleaseRequestModel(
                channel="edge",
                resources=[
                    ResourceModel(name=resource_name, revision=resource_revision)
                ],
                revision=charm_revision,
            )
        ],
    )
    # [docs:release-end]


if __name__ == "__main__":
    main(sys.argv[1:])
