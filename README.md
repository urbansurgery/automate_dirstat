# Speckle Density Analysis Tool

This tool is designed for the AEC (Architecture, Engineering, and Construction) industry to analyze and report on the
density of mesh objects in Speckle projects. The goal is to help identify potentially problematic objects that might
impact model performance, based on a presumed relationship between heavy mesh objects and poor model health.

## Introduction

Heavy mesh objects can often be a sign of poor model health and can detrimentally affect performance. This tool provides
a comprehensive analysis of Speckle projects to identify and report on the density of these objects. The report
generated can then be used to take corrective measures, ensuring optimal model health.

**Note**: The absolute value of the density is unitless and is used for comparative purposes. It's essential to
interpret the results in the context of the specific project.

## Getting Started

1. **Setup**: Clone this repository to your local machine or development environment.
2. **Dependencies**: Install the required dependencies using `poetry` with the command `$ poetry add pandas`.
3. **Configuration**: Edit the `launch.json` as required for your setup.
4. **Local Development**: For local development and testing, refer to the "Local dev environment" section.

## How to Use

1. **Initialization**: Create a new Speckle Automation.
2. **Configuration**:
    - Select your Speckle Project and Speckle Model.
    - Choose the Speckle Function named "Density Analysis Tool".
    - Set the desired density threshold and pass rate percentage.
3. **Execution**: Click on "Create Automation". The tool will analyze the project and provide a comprehensive report.

## Developing Your Own Tool

If you're looking to create a custom function based on this template:

1. **Clone**: Fork this repository and clone it to your development environment.
2. **Register**: Register your function with Speckle Automate to obtain a Function Publish Token and a Function ID.
3. **Configure**: Save your Token and ID as GitHub Action Secrets, named `SPECKLE_AUTOMATE_FUNCTION_PUBLISH_TOKEN`
   and `SPECKLE_AUTOMATE_FUNCTION_ID` respectively.
4. **Development**: Modify `main.py` as per your requirements. Remember to test your changes.
5. **Deployment**: Committing to the main branch will create a new version of your Speckle Function.

## Developer Requirements

- Python 3
- Poetry

After installation, run `poetry shell && poetry install` to install the necessary Python packages.

## Building and Testing

Test the code locally using the command `poetry run pytest`. Ensure that the code is packaged into a Docker Container
Image format required by Speckle Automate and test the container as well.

## Resources

To learn more about interacting with Speckle from Python, refer to the
official [SpecklePy documentation](<link_to_docs>).
