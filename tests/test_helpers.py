import pytest
from specklepy.objects.base import Base

from Objects.objects import HealthObject
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


def test_filter_displayable_bases(mock_base):
    displayable_bases = Utilities.filter_displayable_bases(mock_base)
    assert (
        len(displayable_bases) == 2
    )  # Only child_1 and child_2 should be considered displayable


def test_convert_from_base_with_nested_elements(mock_base):
    health_obj = HealthObject(id="12345")
    health_obj.convert_from_base(mock_base)
    assert health_obj.id == "12345"
    assert (
        health_obj.speckle_type == "Base"
    )  # Assuming no speckle_type was set in the mock_base


def test_density_with_nested_elements(mock_base):
    health_obj = HealthObject(id="12345")
    health_obj.convert_from_base(mock_base)
    densities = health_obj.densities
    # Since the bounding_volumes and sizes in the mock_base are default (0 and [0] respectively), density should be 0
    assert all(density == 0 for density in densities)


if __name__ == "__main__":
    pytest.main()
