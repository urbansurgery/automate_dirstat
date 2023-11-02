import json
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, TypeVar, Union

from matplotlib import pyplot as plt
from speckle_automate import AutomationContext
from specklepy.objects.base import Base
from specklepy.objects.geometry import Mesh
from specklepy.objects.graph_traversal.traversal import GraphTraversal, TraversalRule
from specklepy.objects.other import RenderMaterial
from specklepy.objects.primitive import Interval

from Utilities.utilities import Utilities

T = TypeVar("T", bound=Base)


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
                f"{key}: (dimension={dimension}, size={size}, volume={volume}, area={area}, density={density})"
            )

        entries_str = ", ".join(entries)
        return (
            f"HealthObject(id={self.id!r}, parent_type={self.parent_type!r}, "
            f"entries={{{entries_str}}})"
        )

    @property
    def densities(self) -> Dict[str, float]:
        """Compute the density of each object.

        Density is defined as:
        - For all objects: size divided by the area.
        If the area is zero, density defaults to zero.
        """
        return {
            key: (self.sizes.get(key, 1) / self.areas.get(key, 1))
            if self.areas.get(key, 0) != 0
            else 0
            for key in self.sizes
        }

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
        self.parent_type = getattr(
            base_object, "parent_type", None
        )  # Fetch the parent_type attribute
        self.speckle_type = base_object.speckle_type
        self.units = base_object.units
        display_value = Utilities.try_get_display_value(base_object)

        if display_value:
            self.display_values = display_value
            self.compute_bounding_volume_from_display_values(display_value)
            self.compute_byte_size_from_display_values(display_value)

    def compute_bounding_volume_from_display_values(
        self, display_value: List[T]
    ) -> None:
        """Compute volume from a mesh representation.

        Currently, this is a placeholder and returns 0. Actual volume
        computation logic can be added in the future.

        Args:
            display_value: The representation(s) of the object.

        Returns:
            float: The computed volume.
        """
        for index, dv in enumerate(display_value):
            # if hasattr(dv, "bbox") and dv.bbox:
            #     self.bounding_volumes[dv.id] = dv.bbox.volume
            #     self.areas[dv.id] = dv.bbox.xSize.length * dv.bbox.ySize.length
            # elif isinstance(dv, Mesh):
            if isinstance(dv, Mesh):
                x_interval = self.interval_from_coordinates_by_offset(dv.vertices, 0)
                y_interval = self.interval_from_coordinates_by_offset(dv.vertices, 1)
                z_interval = self.interval_from_coordinates_by_offset(dv.vertices, 2)

                self.bounding_volumes[dv.id] = (
                    x_interval.length() * y_interval.length() * z_interval.length()
                )
                self.bounding_volumes[dv.id] /= 1000000000  # Convert to m^3

                self.areas[dv.id] = (
                    x_interval.length() * y_interval.length()
                ) / 1000000

                if z_interval.length() == 0:
                    self.dimension = "2D"

            else:
                self.bounding_volumes[
                    dv.id
                ] = 0.0  # TODO: Handle other types of display values
                self.areas[dv.id] = 0.0

    def compute_byte_size_from_display_values(self, display_values: List[T]) -> None:
        """Compute the byte size of a list of display values.

        Args:
            display_values (List[T]): A list of display values.

        Returns:
            int: The computed byte size.
        """
        self.sizes.update({dv.id: Utilities.get_byte_size(dv) for dv in display_values})

    @staticmethod
    def interval_from_coordinates_by_offset(
        vertices: List[float], offset: int = 0
    ) -> Interval:
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


# def colorise_densities(
#         automate_context: AutomationContext, health_objects: Dict[str, HealthObject]
# ) -> None:
#     """
#     Create a color gradient based on density values for visualization.
#
#     Args:
#         automate_context (AutomationContext): Context for the automate function.
#         health_objects (Dict[str, HealthObject]): Dictionary mapping object IDs
#                                                   to their HealthObject.
#
#     For each HealthObject, this function calculates a color based on its
#     density. This color then is used to update the object's render material.
#     """
#
#     # Extracting densities for each HealthObject
#     densities = {ho.id: ho.aggregate_density for ho in health_objects.values()}
#
#     if len(densities.items()) == 0:
#         return
#
#     # Determine the range of densities for normalization
#     min_density = min(densities.values())
#     max_density = max(densities.values())
#
#     # Get the colormap and normalize the densities
#     cmap = plt.get_cmap("viridis")
#     norm = plt.Normalize(min_density, max_density)
#
#     # Iterate through each HealthObject and update its render material
#     for obj_id, density in densities.items():
#         rgba_color = cmap(norm(density))
#
#         # Convert RGBA to Hex
#         hex_color = "#{:02x}{:02x}{:02x}".format(
#             int(rgba_color[0] * 255), int(rgba_color[1] * 255), int(rgba_color[2] * 255)
#         )
#
#         # Convert hex color to ARBG integer format
#         arbg_color = int(hex_color[1:], 16) - (1 << 32)
#
#         # Attach color information for visualization
#         automate_context.attach_info_to_objects(
#             category="Density Visualization",
#             metadata={"density": density},
#             message="density visualization",
#             object_ids=obj_id,
#             visual_overrides={"color": hex_color},
#         )
#
#         # Update the render material of the HealthObject
#         health_objects[obj_id].render_material = RenderMaterial(diffuse=arbg_color)
def colorise_densities(
    automate_context: AutomationContext, health_objects: Dict[str, HealthObject]
) -> None:
    """Create a color gradient based on density values for visualization.

    Args:
        automate_context (AutomationContext): Context for the automate function.
        health_objects (Dict[str, HealthObject]): Dictionary mapping object IDs
                                                  to their HealthObject.

    For each HealthObject, this function calculates a color based on its
    density. This color then is used to update the object's render material.
    """
    # Extracting densities for each HealthObject
    gradient_values, all_object_ids, all_colors = colorize(health_objects)

    # Attach color information for visualization for all objects in a single call
    automate_context.attach_info_to_objects(
        category="Density Visualization",
        metadata={"gradient": True, "gradientValues": gradient_values},
        message="Density visualization",
        object_ids=all_object_ids,
    )


def colorize(
    health_objects
) -> tuple[dict[Any, dict[str, Any]], list[Any], dict[Any, str]]:
    densities = {ho.id: ho.aggregate_density for ho in health_objects.values()}

    if not densities:
        return

    # Determine the range of densities for normalization
    min_density = min(densities.values())
    max_density = max(densities.values())

    # Get the colormap and normalize the densities
    cmap = plt.get_cmap("viridis")
    norm = plt.Normalize(min_density, max_density)

    gradient_values = {}
    all_object_ids = []
    all_colors = {}

    for object_id, density in densities.items():
        rgba_color = cmap(norm(density))

        # Convert RGBA to Hex
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba_color[0] * 255), int(rgba_color[1] * 255), int(rgba_color[2] * 255)
        )

        gradient_values[object_id] = {"gradientValue": density}
        all_object_ids.append(object_id)
        all_colors[object_id] = hex_color

        # Convert hex color to ARBG integer format and register a render material
        arbg_color = int(hex_color[1:], 16) - (1 << 32)

        render_material = RenderMaterial()

        render_material.name = "Density"
        render_material.diffuse = arbg_color
        render_material.opacity = 1
        render_material.metalness = 0
        render_material.roughness = 1
        render_material.emissive = -16777216  # black arbg

        health_objects[object_id].render_material = render_material

    return gradient_values, all_object_ids, all_colors


def attach_visual_markers(
    automate_context: AutomationContext,
    health_objects: Dict[str, HealthObject],
    density_level: float,
) -> None:
    """Attach visual markers and notifications based on density.

    Args:
        automate_context: Context for the automate function.
        health_objects: Dictionary of health objects.
        density_level: Threshold for high density.
    """
    failing_ids = []
    non_failing_ids = []

    for ho in health_objects.values():
        if any(value > density_level for value in ho.densities.values()):
            failing_ids.append(ho.id)
        else:
            non_failing_ids.append(ho.id)

    if failing_ids:
        automate_context.attach_error_to_objects(
            category="Density Check",
            object_ids=failing_ids,
            message=f"This object has a density that exceeds the set threshold ({density_level}).",
            visual_overrides={"color": "#ff0000"},
        )

    if non_failing_ids:
        automate_context.attach_info_to_objects(
            category="Density Check",
            object_ids=non_failing_ids,
            message=f"This object has a density below the set threshold. ({density_level}).",
            visual_overrides={"color": "#00ff00"},
        )


def create_health_objects(bases: List[Base]) -> Dict[str, HealthObject]:
    """Converts bases into health objects for further analysis.

    Args:
        bases: List of base objects.

    Returns:
        Dictionary mapping IDs to corresponding health objects.
    """
    health_objects = {b.id: HealthObject(id=b.id) for b in bases}
    for b in bases:
        health_objects[b.id].convert_from_base(b)

    return health_objects


def density_summary(
    health_objects: Dict[str, "HealthObject"]
) -> tuple[List[List[Union[str, float, int]]], List[float], List[int]]:
    """Generate a density summary for the provided health objects.

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
        ho
        for ho in health_objects.values()
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
        ["Third Quartile", q3_density],
    ]

    return data, all_densities, all_areas


def transport_recolorized_commit(
    automate_context: AutomationContext,
    health_objects: Dict[str, HealthObject],
    root_object: Base,
) -> None:
    # traverse the speckle commit object and find the display meshes that have entries in the health objects map
    # return the commit id of the new commit
    # create a new commit on a specific branch - we'll use "dirstat" for now

    if automate_context.automation_run_data.branch_name == "density":
        # commits on the density branch cannot be recolored
        print("------------------------------------------------")
        print("| CANNOT RECOLOR COMMITS ON THE DENSITY BRANCH |")
        print("------------------------------------------------")
        return

    # Traverse the root object to find display meshes
    speckle_data = get_data_traversal()
    traversal_contexts_collection = speckle_data.traverse(root_object)

    # Iterate over each context in the traversal contexts collection.
    # Each context represents an object (or a nested part of an object) within
    # the data structure that was traversed.
    # The goal of this loop is to identify mesh objects represented as HealthObjects and apply the
    # render material already calculated.
    for context in traversal_contexts_collection:
        current_object = context.current

        # check current object is type Base and has a displayValue property and has an id that exists in the health objects map
        if (
            isinstance(current_object, Base)
            and hasattr(current_object, "displayValue")
            and hasattr(current_object, "id")
            and current_object.id in health_objects.keys()
        ):
            display_value = Utilities.try_get_display_value(current_object)

            if display_value:
                # if display_value is an iterable
                if isinstance(display_value, Iterable):
                    for display_value_object in display_value:
                        # Apply the render material to the object
                        display_value_object.renderMaterial = health_objects[
                            current_object.id
                        ].render_material

                    # concatenate the names of all the render materials
                    render_material_names = [
                        display_value_object.renderMaterial.name
                        for display_value_object in display_value
                    ]

                else:
                    # Apply the render material to the object
                    display_value.renderMaterial = health_objects[
                        current_object.id
                    ].render_material

                    # concatenate the names of all the render materials
                    render_material_names = [display_value.renderMaterial.name]

                current_object["density_rendered"] = True
                current_object["densities"] = health_objects[
                    current_object.id
                ].densities

    new_version_id = automate_context.create_new_version_in_project(
        root_object=root_object,
        model_name="density",
        version_message="Colored Densities",
    )

    if not new_version_id:
        raise Exception("Failed to create a new commit on the server.")

    return


def custom_encoder(obj):
    if isinstance(obj, Mesh):
        return None
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def get_data_traversal() -> GraphTraversal:
    """This function is responsible for navigating through the Speckle data  # noqa: D205
    hierarchy and providing contexts to be checked and acted upon.

    Returns: traversal rule function
    """
    display_value_property_aliases = {"displayValue", "@displayValue"}
    elements_property_aliases = {"elements", "@elements"}

    display_value_rule = TraversalRule(
        [
            lambda o: any(
                getattr(o, alias, None) for alias in display_value_property_aliases
            ),
            lambda o: "Geometry" in o.speckle_type,
        ],
        lambda o: elements_property_aliases,
    )

    default_rule = TraversalRule([lambda _: True], lambda o: o.get_member_names())

    return GraphTraversal([display_value_rule, default_rule])
