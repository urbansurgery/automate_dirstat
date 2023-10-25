from typing import List, TypeVar, Iterable, Optional, Union
from matplotlib import pyplot as plt
from speckle_automate import AutomationContext
from specklepy.objects.base import Base
import sys

import statistics

from typing import TYPE_CHECKING, Dict

from specklepy.objects.other import RenderMaterial

from flatten import flatten_base

if TYPE_CHECKING:
    from Objects.objects import HealthObject

T = TypeVar('T', bound=Base)


class Utilities:

    @staticmethod
    def is_displayable_object(speckle_object: Base) -> bool:
        """
        Determines if a given Speckle object is displayable.

        This function checks if the speckle_object has a display value
        and returns True if it does, otherwise it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.

        Returns:
            bool: True if the object has a display value, False otherwise.
        """
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
            Keeps drilling down until it gets to vertices, or it returns 0 if it can't find any.

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
    def density_summary(
            health_objects: Dict[str, 'HealthObject']) -> tuple[
        List[List[Union[str, float, int]]], List[float], List[int]]:
        """
        Generate a density summary for the provided health objects.

        This method filters health objects based on their areas, computes
        various statistical metrics on their densities, and prepares a summary
        table of these metrics.

        Args:
            health_objects (Dict[str, 'HealthObject']): A dictionary of health
                objects to compute the summary for.

        Returns:
            tuple: A tuple containing the summary table, all densities, and
                all areas.
        """
        # Filter objects with any area value greater than or equal to 0
        filtered_health_objects = [
            ho for ho in health_objects.values()
            if any(area >= 0 for area in ho.areas.values())
        ]

        # Extract relevant data
        all_densities = [ho.aggregate_density for ho in filtered_health_objects]
        all_areas = [sum(ho.bounding_volumes.values()) for ho in filtered_health_objects]

        # Compute statistical metrics
        count = len(filtered_health_objects)
        avg_density = round(sum(all_densities) / count if count else 0, 3)
        median_density = round(statistics.median(all_densities), 3)
        max_density = round(max(all_densities), 3)
        min_density = round(min(all_densities), 3)
        std_dev_density = round(statistics.stdev(all_densities) if count > 1 else 0, 3)
        q1_density = round(statistics.quantiles(all_densities, n=4)[0], 3)
        q3_density = round(statistics.quantiles(all_densities, n=4)[2], 3)

        # Prepare the summary table
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
    def attach_visual_markers(automate_context: AutomationContext,
                              health_objects: Dict[str, HealthObject],
                              density_level: float) -> None:
        """
        Attach visual markers and notifications based on density.

        Args:
            automate_context: Context for the automate function.
            health_objects: Dictionary of health objects.
            density_level: Threshold for high density.
        """
        for ho in health_objects.values():
            if any(value > density_level for value in ho.densities.values()):
                count_exceeding = sum(1 for value in ho.densities.values() if value > density_level)
                automate_context.attach_error_to_objects(
                    category="Density Check",
                    object_ids=ho.id,
                    message=(
                        f"{count_exceeding} mesh{'es' if count_exceeding != 1 else ''} "
                        f"of this object {'have' if count_exceeding != 1 else 'has'} a density, "
                        f"that exceeds the threshold of {density_level}."
                    ),
                    visual_overrides={"color": "#ff0000"}
                )
            else:
                automate_context.attach_info_to_objects(
                    category="Density Check",
                    object_ids=ho.id,
                    message=f"This object has an acceptable density of {ho.aggregate_density}.",
                    visual_overrides={"color": "#00ff00"},
                )

    @staticmethod
    def create_health_objects(bases: List[Base]) -> Dict[str, HealthObject]:
        """
        Converts bases into health objects for further analysis.

        Args:
            bases: List of base objects.

        Returns:
            Dictionary mapping IDs to corresponding health objects.
        """
        health_objects = {b.id: HealthObject(id=b.id) for b in bases}
        for b in bases:
            health_objects[b.id].convert_from_base(b)

        return health_objects

    @staticmethod
    def filter_displayable_bases(root_object: Base) -> List[Base]:
        """
        Filters out objects that are not displayable or don't have valid IDs.

        Args:
            root_object: The root object to start the filtering from.

        Returns:
            List of displayable bases with valid IDs.
        """
        return [
            b for b in flatten_base(root_object)
            if Utilities.is_displayable_object(b) and b.id
        ]
