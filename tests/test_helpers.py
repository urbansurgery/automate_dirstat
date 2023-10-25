from typing import Any

import pytest
from specklepy.objects.base import Base
from specklepy.transports.server import ServerTransport

from Utilities.reporting import Report
from main import (
    filter_displayable_bases,
    create_health_objects
)
from Objects.objects import HealthObject
from specklepy.api.client import SpeckleClient

from specklepy.api import operations

from Utilities.utilities import Utilities


@pytest.fixture
def mock_base():
    base = Base()
    base.id = "12345"

    # Nested children
    child_1 = Base()
    child_1.id = "child1"
    child_1.displayValue = [Base()]

    child_2 = Base()
    child_2.id = "child2"
    child_2.displayValue = [Base()]

    base.elements = [child_1, child_2]

    return base


@pytest.fixture()
def speckle_token(request) -> str:
    return request.config.SPECKLE_TOKEN


@pytest.fixture()
def speckle_server_url(request) -> str:
    """Provide a speckle server url for the test suite, default to localhost."""
    return request.config.SPECKLE_SERVER_URL


# @pytest.fixture()
# def test_commit(speckle_server_url: str, speckle_token: str) -> Base:
#     test_client = SpeckleClient(speckle_server_url, True)
#     test_client.authenticate_with_token(speckle_token)
#
#     stream_id = '8e9d85d65b'
#     commit_id = '9b8c58cf13'
#
#     transport = ServerTransport(client=test_client, stream_id=stream_id)
#
#     commit = test_client.commit.get(stream_id, commit_id)
#
#     commit_object = commit.referencedObject
#
#     obj = operations.receive(obj_id=commit_object, remote_transport=transport)
#
#     return obj


# def test_filter_real_displayable_bases(test_commit: Any, speckle_server_url: str):
#     assert isinstance(test_commit, Base) == True
#     displayable_bases = filter_displayable_bases(test_commit)
#
#     commit_details = {'stream_id': '8e9d85d65b',
#                       'commit_id': '9b8c58cf13',
#                       'server_url': speckle_server_url
#                       }
#     threshold = 13000
#
#     health_objects = create_health_objects(displayable_bases)
#
#     data, all_densities, all_areas = Utilities.density_summary(health_objects, threshold)
#
#     pass_rate_percentage = 0.15
#
#     summary_data = Report.generate_summary(threshold, pass_rate_percentage, health_objects, commit_details)
#
#     report_data = {'table_data': summary_data, 'result': summary_data[6][1]}
#
#     report = Report.generate_pdf(all_densities=all_densities,
#                                  all_areas=all_areas, data=data,
#                                  threshold=threshold,
#                                  summary_data=report_data)
#
#     with open('output_filename.pdf', 'wb') as f:
#         report.seek(0)  # Ensure the buffer's position is at the beginning
#         f.write(report.read())
#
#     assert report is not None


def test_filter_displayable_bases(mock_base):
    displayable_bases = filter_displayable_bases(mock_base)
    assert len(displayable_bases) == 2  # Only child_1 and child_2 should be considered displayable


def test_convert_from_base_with_nested_elements(mock_base):
    health_obj = HealthObject(id="12345")
    health_obj.convert_from_base(mock_base)
    assert health_obj.id == "12345"
    assert health_obj.speckle_type is 'Base'  # Assuming no speckle_type was set in the mock_base


def test_density_with_nested_elements(mock_base):
    health_obj = HealthObject(id="12345")
    health_obj.convert_from_base(mock_base)
    densities = health_obj.densities
    # Since the bounding_volumes and sizes in the mock_base are default (0 and [0] respectively), density should be 0
    assert all(density == 0 for density in densities)


if __name__ == "__main__":
    pytest.main()
