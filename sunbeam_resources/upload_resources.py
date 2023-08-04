"""Upload resource pointers for a charm on the charmhub."""

import click
import json
import yaml
import tempfile

from pathlib import Path
from charmcraft.commands.store import Store, ResourceType
from charmcraft.models.charmcraft import CharmhubConfig
from charmcraft.parts import setup_parts

from craft_cli import (
    EmitterMode,
    emit,
)


def charm_metadata() -> dict:
    """Read charm metadata from disk."""
    metadata_yaml = Path("metadata.yaml")
    if metadata_yaml.exists():
        with metadata_yaml.open("r") as f:
            return yaml.safe_load(f)


@click.command()
def main():
    """Upload all resources identitied in charm metadata as OCI references."""
    emit.init(
        EmitterMode.BRIEF,
        "sunbeam-resource-uploader",
        "sunbeam-resource-uploader",
        log_filepath=Path("/dev/stderr"),
    )
    setup_parts()
    charmhub_config = CharmhubConfig()

    store = Store(charmhub_config)

    metadata = charm_metadata()
    if not metadata:
        return
    charm = metadata["name"]

    revisions = {}

    for resource_name in metadata.get("resources"):
        resource = metadata["resources"][resource_name]
        upstream_source = resource.get("upstream-source")
        if not upstream_source:
            emit.message(f"No upstream source found for {resource_name}")
            continue
        emit.message(f"Uploading: {resource_name}:{upstream_source}")

        resource_metadata = {"ImageName": upstream_source}
        _, tname = tempfile.mkstemp(prefix="image-resource", suffix=".json")
        resource_filepath = Path(tname)
        resource_filepath.write_text(json.dumps(resource_metadata))
        result = store.upload_resource(
            charm, resource_name, ResourceType.oci_image, resource_filepath
        )
        emit.message(f"Uploaded {resource_name}:{result.revision}")
        revisions[resource_name] = result.revision
        resource_filepath.unlink()

    revisions_filepath = Path("revisions.json")
    revisions_filepath.write_text(json.dumps(revisions))


if __name__ == "__main__":
    main()
