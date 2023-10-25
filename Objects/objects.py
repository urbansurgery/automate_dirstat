from dataclasses import dataclass, field

from specklepy.objects.base import Base
from specklepy.objects.geometry import Mesh
from typing import Optional, TypeVar, List, Dict

from specklepy.objects.other import RenderMaterial
from specklepy.objects.primitive import Interval

from Utilities.utilities import Utilities

T = TypeVar('T', bound=Base)


@dataclass
class HealthObject:
    """Data structure representing the health of a Speckle object.

    This class captures various metrics of a Speckle object, including size,
    area, volume, and density. It also captures the type of the parent object
    in the Speckle object hierarchy.
    """
    id: str
    sizes: Dict[str, int] = field(default_factory=dict)  # Size of the object in bytes
    bounding_volumes: Dict[str, float] = field(default_factory=dict)
    areas: Dict[str, float] = field(default_factory=dict)
    parent_type: Optional[str] = None  # Type of the parent Speckle object
    speckle_type: Optional[str] = None  # Type of the Speckle object
    display_values: List[T] = field(default_factory=list)
    units: str = None
    dimension: str = "3D"
    render_material: Optional[RenderMaterial] = None

    def __repr__(self):
        entries = []
        for key in self.sizes:
            size = self.sizes.get(key, 0)
            density = self.densities.get(key, 0)
            volume = self.bounding_volumes.get(key, 0)
            area = self.areas.get(key, 0)
            dimension = self.dimension
            entries.append(
                f"{key}: (dimension={dimension}, size={size}, volume={volume}, area={area}, density={density})")

        entries_str = ', '.join(entries)
        return (f"HealthObject(id={self.id!r}, parent_type={self.parent_type!r}, "
                f"entries={{{entries_str}}})")

    @property
    def densities(self) -> Dict[str, float]:
        """Compute the density of each object.

        Density is defined as:
        - For all objects: size divided by the area.
        If the area is zero, density defaults to zero.
        """
        return {key: (self.sizes[key] / self.areas[key]) if self.areas[key] != 0 else 0 for key in self.sizes}

    @property
    def aggregate_density(self) -> float:
        """Compute the aggregate density of the object.

        Aggregate density is defined as the sum of all sizes divided by the sum of all areas. If the total area is zero, density defaults to zero.
        """
        total_size = sum(self.sizes.values())
        total_area = sum(self.areas.values())
        return total_size / total_area if total_area != 0 else 0

    def convert_from_base(self, base_object: Base) -> None:
        """Populate the HealthObject attributes from a Speckle Base object.

        Args:
            base_object (Base): The Speckle Base object to convert from.

        Raises:
            ValueError: If no bounding volume information is found for the object.
        """
        self.id = base_object.id
        self.parent_type = getattr(base_object, 'parent_type', None)  # Fetch the parent_type attribute
        self.speckle_type = base_object.speckle_type
        self.units = base_object.units
        display_value = Utilities.try_get_display_value(base_object)

        if display_value:
            self.compute_bounding_volume_from_display_values(display_value)

        if display_value:
            self.display_values = display_value
            self.compute_byte_size_from_display_values(display_value)

    def compute_bounding_volume_from_display_values(self, display_value: List[T]) -> None:
        """Compute volume from a mesh representation.

        Currently, this is a placeholder and returns 0. Actual volume
        computation logic can be added in the future.

        Args:
            display_value: The representation(s) of the object.

        Returns:
            float: The computed volume.
        """
        for index, dv in enumerate(display_value):
            if hasattr(dv, 'bbox') and dv.bbox:
                self.bounding_volumes[dv.id] = dv.bbox.volume
            elif isinstance(dv, Mesh):
                x_interval = self.interval_from_coordinates_by_offset(dv.vertices, 0)
                y_interval = self.interval_from_coordinates_by_offset(dv.vertices, 1)
                z_interval = self.interval_from_coordinates_by_offset(dv.vertices, 2)

                self.bounding_volumes[dv.id] = (x_interval.length() * y_interval.length() * z_interval.length())
                self.bounding_volumes[dv.id] /= 1000000000  # Convert to m^3

                self.areas[dv.id] = (x_interval.length() * y_interval.length()) / 1000000

                if z_interval.length() == 0:
                    self.dimension = "2D"


            else:
                self.bounding_volumes[dv.id] = 0.0  # TODO: Handle other types of display values

    def compute_byte_size_from_display_values(self, display_values: List[T]) -> None:

        """Compute the byte size of a list of display values.

        Args:
            display_values (List[T]): A list of display values.

        Returns:
            int: The computed byte size.
        """

        self.sizes.update({dv.id: Utilities.get_byte_size(dv) for dv in display_values})

    @staticmethod
    def interval_from_coordinates_by_offset(vertices: List[float], offset: int = 0) -> Interval:
        """Compute interval from coordinates by offset.

        Args:
            vertices (List[float]): List of vertex coordinates.
            offset (int, optional): Offset to start from. Defaults to 0.

        Returns:
            Interval: Computed interval.
        """
        axis_coordinates = vertices[offset::3]
        axis_interval = Interval(start=min(axis_coordinates), end=max(axis_coordinates))
        return axis_interval
