import io
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Dict, List, Union

import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.lib.colors import green, red
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from Objects.objects import HealthObject
from Utilities.plotting import Plotting


class Report:
    @staticmethod
    def generate_pdf(
        all_densities: List[float],
        all_areas: List[float],
        data: List[List[Union[str, float, int]]],
        threshold: float,
        summary_data=None,
    ) -> IO[bytes]:
        """
        Generate a PDF report summarizing the density data and return as a BytesIO object.

        Args:
            all_densities (List[float]): List of all density values.
            all_areas (List[float]): List of all area values.
            data (List[List[Union[str, float, int]]]): Data to be tabulated in the PDF.
            threshold (float): The threshold for density.
            summary_data: Data to be tabulated in the summary table.

        Returns:
            IO[bytes]: BytesIO object containing the PDF data.
        """
        # Create a buffer to store the PDF
        pdf_buffer = io.BytesIO()

        # Create a buffer to store the plots
        plot_buffer_density = io.BytesIO()
        plot_buffer_correlation = io.BytesIO()

        # Determine the available width for the image, considering 1-inch margins on both sides
        available_width = (
            A4[0] - 2 * 72
        )  # A4[0] gives the width of the A4 page in points

        # Plot density distribution and save to buffer
        plt.figure(figsize=(12, 7))
        Plotting.plot_density_distribution(all_densities, threshold)
        plt.savefig(plot_buffer_density, format="png")
        plot_buffer_density.seek(0)

        # Plot area-density correlation and save to buffer
        plt.figure(figsize=(12, 7))
        Plotting.plot_area_density_correlation(all_areas, all_densities, threshold)
        plt.savefig(plot_buffer_correlation, format="png")
        plot_buffer_correlation.seek(0)

        # Initialize PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=portrait(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=128,
        )
        story = []
        styles = getSampleStyleSheet()

        story.append(Paragraph("Model Health", styles["Title"]))

        # Introduction paragraph
        intro_paragraph = (
            "The performance and health of a digital model in the AEC "
            "(Architecture, Engineering, and Construction) domain can be significantly "
            "impacted by the complexity and density of the mesh objects within it. Heavy "
            "mesh objects, characterized by a high density of vertices and polygons, often "
            "result in slower rendering times, increased computational resource consumption, "
            "and potential crashes or lags in visualization tools. Such objects can be a "
            "primary contributor to poor model health and can degrade the user experience, "
            "especially in real-time rendering or simulation scenarios. It's important to note "
            "that the absolute value of the density, while indicative of object complexity, "
            "is without meaningful units (~vertices/m2) in and of itself and should be interpreted in the "
            "context of the model and its intended use. This report analyzes the densities of "
            "various mesh objects within the model to identify potential performance "
            "bottlenecks and provide actionable insights for optimization."
        )

        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(intro_paragraph, styles["Normal"]))
        story.append(Spacer(1, 0.25 * inch))

        result_color = green

        # Summary Table
        if summary_data is not None:
            summary_table = Table(summary_data["table_data"])

            # if summary_data['result'] contains "Fail", set the result color to red
            if "Fail" in summary_data["result"]:
                result_color = red

            summary_table.setStyle(
                TableStyle(
                    [
                        (
                            "TEXTCOLOR",
                            (1, 6),
                            (1, 7),
                            result_color,
                        )  # Targeting only the "Result" cell
                    ]
                )
            )

            story.append(summary_table)
            story.append(Spacer(1, 0.25 * inch))

        # Append elements to the story (PDF content)
        story.append(Paragraph("Density Summary", styles["Heading2"]))
        story.append(Spacer(1, 0.25 * inch))

        # Add data table
        table = Table(data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), "#eeeeee"),
                    ("TEXTCOLOR", (0, 0), (-1, 0), "#333333"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), "#f3f3f3"),
                    ("GRID", (0, 0), (-1, -1), 1, "#aaaaaa"),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 0.25 * inch))
        story.append(PageBreak())  # Insert a page break

        # For the density distribution plot:
        story.append(Paragraph("Density Distribution Plot:", styles["Heading2"]))
        plot_buffer_density.seek(0)
        width, height = Report.get_resized_dimensions(
            plot_buffer_density,
            target_width=available_width,
            max_height=available_width,
        )
        img_density = Image(plot_buffer_density, width=width, height=height)
        img_density.hAlign = "CENTER"
        story.append(img_density)
        story.append(Spacer(1, 0.25 * inch))

        # For the area-density correlation plot:
        story.append(
            Paragraph("Correlation between Area and Density:", styles["Heading2"])
        )
        plot_buffer_correlation.seek(0)
        width, height = Report.get_resized_dimensions(
            plot_buffer_correlation,
            target_width=available_width,
            max_height=available_width,
        )
        img_correlation = Image(plot_buffer_correlation, width=width, height=height)
        img_correlation.hAlign = "CENTER"
        story.append(img_correlation)

        # Build the PDF document
        doc.build(story)

        # Reset the buffer position to the beginning
        pdf_buffer.seek(0)

        return pdf_buffer

    @staticmethod
    def get_resized_dimensions(buffer, target_width, max_height):
        """Get resized width and height for an image while maintaining aspect ratio."""
        with PILImage.open(buffer) as img:
            original_width, original_height = img.size
            aspect_ratio = original_height / original_width
            new_height = target_width * aspect_ratio
            if new_height > max_height:
                new_height = max_height
                new_width = new_height / aspect_ratio
            else:
                new_width = target_width
        return new_width, new_height

    @staticmethod
    def generate_summary(
        threshold: float,
        pass_rate_percentage: float,
        health_objects: Dict[str, HealthObject],
        commit_details: Dict[str, str],
    ) -> Dict[str, Any]:
        # Calculate the number of objects above the threshold
        above_threshold_count = sum(
            1 for ho in health_objects.values() if ho.aggregate_density > threshold
        )

        # Calculate the percentage of objects above the threshold
        above_threshold_percentage = above_threshold_count / len(health_objects)

        # Determine if the result is a pass or fail
        result_state = (
            "Pass" if above_threshold_percentage <= pass_rate_percentage else "Fail"
        )
        result = f"{result_state} ({above_threshold_percentage * 100:.2f}%)"

        # Create the summary table
        data = {
            "table": [
                ["Metric", "Value"],
                ["Server URL", commit_details["server_url"]],
                ["Project ID", commit_details["stream_id"]],
                ["Version ID", commit_details["commit_id"]],
                ["Threshold", threshold],
                ["Pass Rate Percentage", f"{pass_rate_percentage * 100}%"],
                ["Assessment Result", result],
            ],
            "values": {
                "pass_rate": pass_rate_percentage,
                "result": result_state,
                "fail_count": above_threshold_count,
            },
        }

        return data

    @staticmethod
    def write_pdf_to_temp(report: IO[bytes]) -> str:
        temp_file = Path(
            tempfile.gettempdir(),
            f"automate_tiles_{datetime.now().timestamp():.0f}",
            "report.pdf",
        )
        temp_file.parent.mkdir(parents=True, exist_ok=True)

        report.seek(0)
        temp_file.write_bytes(report.read())

        return str(temp_file)
