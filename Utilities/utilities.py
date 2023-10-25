from typing import List, TypeVar, Iterable, Optional, Union
import re
from specklepy.objects.base import Base
import sys

import statistics

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from Objects.objects import HealthObject

T = TypeVar('T', bound=Base)


class Utilities:

    @staticmethod
    def is_displayable_object(speckle_object: Base) -> bool:
        return Utilities.try_get_display_value(speckle_object) is not None

    @staticmethod
    def try_get_display_value(speckle_object: Base) -> Optional[List[T]]:
        """Try fetching the display value from a Speckle object.

        Args:
            speckle_object (Base): The Speckle object to extract the display value from.

        Returns:
            Optional[List[T]]: A list containing the display values. If no display value is found,
                               returns None.
        """
        raw_display_value = getattr(speckle_object, 'displayValue', None) or getattr(speckle_object, '@displayValue',
                                                                                     None)

        if raw_display_value is None:
            return None

        if isinstance(raw_display_value, Iterable):
            display_values = list(filter(lambda x: isinstance(x, Base), raw_display_value))
            return display_values if display_values else None

    @staticmethod
    def get_byte_size(speckle_object: Base) -> int:
        """Calculate the total byte size of the display values of a Speckle object.

        Args:
            speckle_object (Base): The Speckle object for which to compute the byte size.

        Returns:
            int: The total byte size of all display values that have vertices.
        """
        if speckle_object is None:
            return 0

        display_values = Utilities.try_get_display_value(speckle_object)

        if display_values is None:
            display_values = speckle_object

        if isinstance(display_values, Iterable):
            return sum([sys.getsizeof(display_value) for display_value in display_values])

        if not hasattr(display_values, 'vertices'):
            return 0

        return sys.getsizeof(display_values['vertices'])

    @staticmethod
    def density_summary(health_objects: Dict[str, "HealthObject"], threshold) -> tuple[
        List[List[Union[str, float, int]]], list[float], list[int]]:
        filtered_health_objects = [ho for ho in health_objects.values() if
                                   any(area >= 0 for area in ho.areas.values())]

        # Extract all densities
        all_densities = [ho.aggregate_density for ho in filtered_health_objects]
        all_areas = [sum(ho.bounding_volumes.values()) for ho in filtered_health_objects]  # Adjust this line if needed
        # all_sizes = [sum(ho.sizes.values()) for ho in filtered_health_objects]  # Adjust this line if needed

        # Calculate the statistics
        count = len(filtered_health_objects)
        avg_density = round(sum(all_densities) / count if count else 0, 3)
        median_density = round(statistics.median(all_densities), 3)
        max_density = round(max(all_densities), 3)
        min_density = round(min(all_densities), 3)
        std_dev_density = round(statistics.stdev(all_densities) if count > 1 else 0, 3)
        q1_density = round(statistics.quantiles(all_densities, n=4)[0], 3)  # First quartile
        q3_density = round(statistics.quantiles(all_densities, n=4)[2], 3)  # Third quartile

        data = [
            ["Metric", "Value"],
            ["Count", count],
            ["Average Density", avg_density],
            ["Median Density", median_density],
            ["Max Density", max_density],
            ["Min Density", min_density],
            ["Standard Deviation", std_dev_density],
            ["First Quartile", q1_density],
            ["Third Quartile", q3_density]
        ]

        return data, all_densities, all_areas

    @staticmethod
    def parse_percentage(s: str) -> float:
        # Extract percentage using regex
        match = re.search(r'(\d+(\.\d+)?)%', s)

        # If found, convert to float
        if match:
            percentage = float(match.group(1))
            return percentage / 100  # Convert to fraction
        else:
            raise ValueError("No percentage value found in the string")
