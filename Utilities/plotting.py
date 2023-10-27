from typing import List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import ScalarFormatter

sns.set_style("whitegrid")
sns.set_context("talk")


class Plotting:
    """Class containing methods to plot various data distributions."""

    @staticmethod
    def plot_density_distribution(densities: List[float], threshold: float) -> None:
        """Plot density distribution with a given threshold.

        Args:
            densities (List[float]): List of densities.
            threshold (float): Value to differentiate high and low densities.
        """
        plt.figure(figsize=(12, 7))
        bin_edges = np.linspace(min(densities), max(densities), 51)

        # Plot densities below the threshold in blue
        sns.histplot(
            [d for d in densities if d <= threshold],
            bins=bin_edges,
            color="green",
            alpha=0.75,
            label="Densities <= threshold",
        )

        # Plot densities above the threshold in red
        sns.histplot(
            [d for d in densities if d > threshold],
            bins=bin_edges,
            color="red",
            alpha=0.75,
            label="Densities > threshold",
        )

        plt.axvline(x=threshold, color="grey", linestyle="--")
        plt.xlabel("Density (~vertices/m2)")
        plt.ylabel("Count")
        plt.title("Density Distribution")
        plt.legend()

        # Format the x-axis to avoid scientific notation
        ax = plt.gca()  # Get current axis
        ax.xaxis.set_major_formatter(ScalarFormatter(useMathText=False))
        ax.ticklabel_format(style="plain", axis="x")
        # plt.show()

    @staticmethod
    def plot_area_density_correlation(
        areas: List[float], densities: List[float], threshold: float
    ) -> None:
        """Plot correlation between area and density with a given threshold.

        Args:
            areas (List[float]): List of areas.
            densities (List[float]): List of densities.
            threshold (float): Value to differentiate high and low densities.
        """
        plt.figure(figsize=(12, 7))

        mask_below_threshold = np.array(densities) <= threshold
        mask_above_threshold = ~mask_below_threshold

        # Plot points below the threshold in blue
        sns.scatterplot(
            x=np.array(areas)[mask_below_threshold],
            y=np.array(densities)[mask_below_threshold],
            color="green",
            label=f"Densities <= {threshold}",
            edgecolor="w",
        )

        # Plot points above the threshold in red
        sns.scatterplot(
            x=np.array(areas)[mask_above_threshold],
            y=np.array(densities)[mask_above_threshold],
            color="red",
            label=f"Densities > {threshold}",
            edgecolor="w",
        )

        plt.axhline(y=threshold, color="grey", linestyle="--")
        plt.title("Correlation between Area and Density")
        plt.xlabel("Area")
        plt.ylabel("Density (~vertices/m2)")
        plt.legend(title="Density", loc="upper right")

        # Format the y-axis to avoid scientific notation
        ax = plt.gca()  # Get current axis
        ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
        ax.ticklabel_format(style="plain", axis="x")
        # plt.show()

    @staticmethod
    def plot_size_distribution(sizes: List[float]) -> None:
        """Plot distribution of sizes.

        Args:
            sizes (List[float]): List of sizes.
        """
        plt.figure()
        plt.hist(sizes, bins=10, alpha=0.75)
        plt.xlabel("Size")
        plt.ylabel("Count")
        plt.title("Size Distribution")
        plt.grid(True)
        # plt.show()

    @staticmethod
    def plot_area_distribution(areas: List[float]) -> None:
        """Plot distribution of areas.

        Args:
            areas (List[float]): List of areas.
        """
        plt.figure()
        plt.hist(areas, bins=10, alpha=0.75)
        plt.xlabel("Area")
        plt.ylabel("Count")
        plt.title("Area Distribution")
        plt.grid(True)
        # plt.show()
