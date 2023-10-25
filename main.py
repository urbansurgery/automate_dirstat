"""This module contains the business logic for a Speckle Automate function.

The purpose is to demonstrate how one can use the automation_context module
to process and analyze data in a Speckle project.
"""

from typing import List, Dict, Any
from pydantic import Field
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)
from specklepy.objects.other import RenderMaterial

from Utilities.reporting import Report
from Utilities.utilities import Utilities
from flatten import flatten_base
from specklepy.objects.base import Base
from Objects.objects import HealthObject
import matplotlib.pyplot as plt


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


## new render materials for objects passing/failing
## swap those into the original commit object


## send that back to the server

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


def colorise_densities(automate_context: AutomationContext,
                       health_objects: Dict[str, HealthObject]) -> None:
    """
    Create a color gradient based on density values for visualization.

    Args:
        automate_context (AutomationContext): Context for the automate function.
        health_objects (Dict[str, HealthObject]): Dictionary mapping object IDs
                                                  to their HealthObject.

    For each HealthObject, this function calculates a color based on its
    density. This color then is used to update the object's render material.
    """

    # Extracting densities for each HealthObject
    densities = {ho.id: ho.aggregate_density for ho in health_objects.values()}

    if len(densities.items()) == 0:
        return

    # Determine the range of densities for normalization
    min_density = min(densities.values())
    max_density = max(densities.values())

    # Get the colormap and normalize the densities
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(min_density, max_density)

    # Iterate through each HealthObject and update its render material
    for obj_id, density in densities.items():
        rgba_color = cmap(norm(density))

        # Convert RGBA to Hex
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(rgba_color[0] * 255),
            int(rgba_color[1] * 255),
            int(rgba_color[2] * 255)
        )

        # Convert hex color to ARBG integer format
        arbg_color = int(hex_color[1:], 16) - (1 << 32)

        # Attach color information for visualization
        automate_context.attach_info_to_objects(
            category="Density Visualization",
            metadata={"density": density},
            object_ids=obj_id,
            visual_overrides={"color": hex_color}
        )

        # Update the render material of the HealthObject
        health_objects[obj_id].render_material = RenderMaterial(diffuse=arbg_color)


class FunctionInputs(AutomateBase):
    """Definition of user inputs for this function.

    These fields define the parameters that users can adjust when triggering
    this function in the Speckle web application.
    """

    density_level: float = Field(
        title="Density Threshold",
        description=("Set a density value as the threshold. Objects with "
                     "densities exceeding this value will be highlighted.")
    )
    max_percentage_high_density_objects: float = Field(
        title="High Density Object Limit (%)",
        description=("Specify the maximum percentage (0-1) of objects you're "
                     "willing to allow above the set density threshold. "
                     "For instance, a value of 0.1 means you'll tolerate up "
                     "to 10% of the objects having a density above the threshold."),
        ge=0.0,
        le=1.0,
    )


def automate_function(automate_context: AutomationContext,
                      function_inputs: FunctionInputs) -> None:
    """
    Main function that processes and analyzes Speckle data.

    Fetches the version of the Speckle project, analyzes its objects based on
    density, and reports back with visual markers and notifications.

    Args:
        automate_context: Provides methods and data related to the current
                          run context, like fetching project data or sending
                          results back.
        function_inputs: User-defined parameters influencing analysis.
    """

    # Fetch the root object of the Speckle project version.
    version_root_object = automate_context.receive_version()

    # Filter objects to only those that are displayable and have valid IDs.
    displayable_bases = filter_displayable_bases(version_root_object)

    if len(displayable_bases) == 0:
        automate_context.mark_run_failed(
            f"No displayable mesh objects found."
        )
        return

    # Convert filtered objects into health objects to analyze density.
    health_objects = create_health_objects(displayable_bases)

    # Attach visual markers and notifications based on density analysis.
    attach_visual_markers(automate_context, health_objects,
                          function_inputs.density_level)

    colorise_densities(automate_context, health_objects)

    # Conclude analysis and mark the run as either successful or failed.
    total_displayable_count = len(displayable_bases)

    pass_rate_percentage = function_inputs.max_percentage_high_density_objects
    threshold = function_inputs.density_level

    data, all_densities, all_areas = Utilities.density_summary(health_objects, function_inputs.density_level)

    commit_details = {
        'stream_id': automate_context.automation_run_data.project_id,
        'commit_id': automate_context.automation_run_data.version_id,
        'server_url': automate_context.automation_run_data.server_url
    }

    summary_data = Report.generate_summary(threshold, pass_rate_percentage, health_objects, commit_details)

    high_density_count = summary_data['values']['fail_count']

    report_data = {'table_data': summary_data['table'], 'result': summary_data['values']['result']}

    report = Report.generate_pdf(all_densities=all_densities,
                                 all_areas=all_areas, data=data,
                                 threshold=threshold,
                                 summary_data=report_data)

    with open('output_filename.pdf', 'wb') as f:
        report.seek(0)  # Ensure the buffer's position is at the beginning
        f.write(report.read())

    if summary_data['values']['result'] == 'Fail':
        automate_context.mark_run_failed(
            f"Too many high-density objects. Allowed: "
            f"{function_inputs.max_percentage_high_density_objects * 100}%, "
            f"Found: "
            f"{(high_density_count / total_displayable_count) * 100}%."
        )
    else:
        automate_context.mark_run_success(
            "Analysis complete. High-density objects within acceptable limits."
        )


if __name__ == "__main__":
    # Entry point: Execute the automate function with defined inputs.
    execute_automate_function(automate_function, FunctionInputs)
