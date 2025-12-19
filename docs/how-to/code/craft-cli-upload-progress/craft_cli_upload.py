#!/usr/bin/env python
from pathlib import Path
import sys

from craft_cli import emit, EmitterMode
from craft_store import StoreClient, endpoints
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


emit.init(EmitterMode.BRIEF, "craft.store-howto", "Starting howto app.")

store_client = StoreClient(
    base_url="https://dashboard.staging.snapcraft.io",
    storage_base_url="https://upload.apps.staging.ubuntu.com",
    endpoints=endpoints.SNAP_STORE,
    user_agent="Craft Store Howto Agent",
    application_name="craft-store-upload",
    environment_auth="SNAPCRAFT_STORE_CREDENTIALS",
)


def create_callback(encoder: MultipartEncoder):
    with emit.progress_bar("Uploading...", encoder.len, delta=False) as progress:

        def progress_callback(monitor: MultipartEncoderMonitor):
            progress.advance(monitor.bytes_read)

    return progress_callback


upload_id = store_client.upload_file(
    monitor_callback=create_callback,
    filepath=Path(sys.argv[1]),
)

emit.message(f"upload-id: {upload_id}")
emit.ended_ok()
