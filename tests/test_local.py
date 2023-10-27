from typing import Any, Iterable

import pytest
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.objects import Base
from specklepy.objects.graph_traversal.traversal import GraphTraversal, TraversalRule
from specklepy.transports.server import ServerTransport

import Objects.objects
from Objects.objects import create_health_objects
from Utilities.utilities import Utilities


@pytest.fixture()
def speckle_token(request) -> str:
    return request.config.SPECKLE_TOKEN


@pytest.fixture()
def speckle_server_url(request) -> str:
    """Provide a speckle server url for the test suite, default to localhost."""
    return request.config.SPECKLE_SERVER_URL


@pytest.fixture()
def test_commit(speckle_server_url: str, speckle_token: str) -> Base:
    test_client = SpeckleClient(speckle_server_url, True)
    test_client.authenticate_with_token(speckle_token)

    stream_id = "d96e3f2579"
    commit_id = "3e4e274c56"

    transport = ServerTransport(client=test_client, stream_id=stream_id)

    commit = test_client.commit.get(stream_id, commit_id)

    commit_object = commit.referencedObject

    obj = operations.receive(obj_id=commit_object, remote_transport=transport)

    return obj


def test_real_displayable(test_commit: Any, speckle_server_url: str):
    # The commit object should always be a Base object from the SDK
    assert isinstance(test_commit, Base) == True

    traversal = GraphTraversal(
        [TraversalRule([lambda _: True], lambda o: o.get_member_names())]
    )

    traversal_contexts_collection = traversal.traverse(test_commit)

    displayable_bases: list[Base] = Utilities.filter_displayable_bases(test_commit)

    assert displayable_bases is not None

    # Transform filtered objects to health objects for density analysis.
    health_objects = create_health_objects(displayable_bases)

    Objects.objects.colorize(health_objects)

    assert len(displayable_bases) >= len(health_objects) > 0

    for context_object in traversal_contexts_collection:
        current_object = context_object.current

        # check current object is type Base and has a displayValue property and has an id that exists in the health objects map
        if (
                isinstance(current_object, Base)
                and hasattr(current_object, "displayValue")
                and hasattr(current_object, "id")
                and current_object.id in health_objects.keys()
        ):
            first_matching_object = current_object

            display_value = Utilities.try_get_display_value(first_matching_object)

            assert display_value is not None

            if display_value:
                # if display_value is an iterable
                if isinstance(display_value, Iterable):
                    for display_value_object in display_value:
                        # Apply the render material to the object
                        display_value_object.renderMaterial = health_objects[
                            current_object.id
                        ].render_material
                else:
                    # Apply the render material to the object
                    display_value.renderMaterial = health_objects[
                        current_object.id
                    ].render_material

            break
