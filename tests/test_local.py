# Importing necessary modules and packages
from typing import Any, Iterable

import pytest

# Speckle is a data platform for AEC; here we're importing essential modules from it
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.objects import Base
from specklepy.objects.graph_traversal.traversal import GraphTraversal, TraversalRule
from specklepy.transports.server import ServerTransport

# Import custom modules for handling objects and utilities
import Objects.objects
from Objects.objects import create_health_objects
from Utilities.utilities import Utilities

# Setting up some pytest fixtures for testing
# Fixtures are a way to provide consistent test data or configuration for each test

@pytest.fixture()
def speckle_token(request) -> str:
    """Get the Speckle token from test configuration."""
    return request.config.SPECKLE_TOKEN


@pytest.fixture()
def speckle_server_url(request) -> str:
    """Provide a speckle server URL for the test suite.
    Defaults to localhost if not specified.
    """
    return request.config.SPECKLE_SERVER_URL


@pytest.fixture()
def test_commit(speckle_server_url: str, speckle_token: str) -> Base:
    """Retrieve a specific commit from the Speckle server."""
    test_client = SpeckleClient(speckle_server_url, True)
    test_client.authenticate_with_token(speckle_token)

    # Sample stream and commit IDs
    stream_id = "d96e3f2579"
    commit_id = "3e4e274c56"

    transport = ServerTransport(client=test_client, stream_id=stream_id)
    commit = test_client.commit.get(stream_id, commit_id)
    commit_object = commit.referencedObject
    obj = operations.receive(obj_id=commit_object, remote_transport=transport)

    return obj


# Main test function
def test_real_displayable(test_commit: Any, speckle_server_url: str):
    """Test if the commit objects can be displayed and colorized."""
    # Ensure that the commit object is an instance of Base class from Speckle
    assert isinstance(test_commit, Base) == True

    # Set up a traversal rule and traverse the commit object
    traversal = GraphTraversal(
        [TraversalRule([lambda _: True], lambda o: o.get_member_names())]
    )
    traversal_contexts_collection = traversal.traverse(test_commit)

    # Filter out objects that can be displayed
    displayable_bases: list[Base] = Utilities.filter_displayable_bases(test_commit)
    assert displayable_bases is not None

    # Convert displayable objects to health objects for further analysis
    health_objects = create_health_objects(displayable_bases)
    Objects.objects.colorize(health_objects)

    # Ensure there are health objects to work with
    assert len(displayable_bases) >= len(health_objects) > 0

    # Traverse through the context collection to find and colorize displayable objects
    for context_object in traversal_contexts_collection:
        current_object = context_object.current

        # Check if the current object matches our criteria for colorization
        if (
                isinstance(current_object, Base)
                and hasattr(current_object, "displayValue")
                and hasattr(current_object, "id")
                and current_object.id in health_objects.keys()
        ):
            first_matching_object = current_object
            display_value = Utilities.try_get_display_value(first_matching_object)
            assert display_value is not None

            # Check if the display value is a collection (like a list)
            if isinstance(display_value, Iterable):
                for display_value_object in display_value:
                    # Apply the corresponding render material to each object in the collection
                    display_value_object.renderMaterial = health_objects[
                        current_object.id
                    ].render_material
            else:
                # Apply the corresponding render material directly to the object
                display_value.renderMaterial = health_objects[
                    current_object.id
                ].render_material
            break  # Stop the loop after finding and processing the first matching object
