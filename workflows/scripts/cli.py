#!/usr/bin/env python3
"""
Command Line Interface for Raster2Sensor

This module provides the command-line interface for the Raster2Sensor application,
which enables processing of raster imagery data and integration with OGC SensorThings API.

The CLI supports various operations including:
- Managing trial plots in SensorThings API
- Processing raster images with vegetation indices
- Executing OGC API Processes
- Configuration management

Author: Joseph Gitahi
Created: 2025
License: MIT License
Repository: https://github.com/joemureithi/raster2sensor

Key Dependencies:
    - typer: Modern CLI framework
    - rich: Rich text and beautiful formatting

Usage:
    python -m raster2sensor --help
    python -m raster2sensor plots create --config config.yml --file-path plots.geojson
    python -m raster2sensor process-images --config config.yml --dry-run
"""

import typer
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from raster2sensor import __app_name__, __version__
from raster2sensor.logging import configure_logging, get_logger
from raster2sensor.utils import clear
from raster2sensor.plots import Plots
from raster2sensor.ogcapiprocesses import OGCAPIProcesses
from raster2sensor.config_parser import load_datastreams_from_config, ConfigParser
from raster2sensor.image_processor import ImageProcessor

# Logger
logger = get_logger(__name__)
configure_logging(
    level="DEBUG",
    log_dir="./logs",
    enable_file_logging=True,
    enable_console_logging=True,
    use_rich=True,  # Use rich formatting if available
    suppress_third_party_debug=True  # Suppress third-party debug logs
)
# Main app
app = typer.Typer()
console = Console()

# Sub-command groups
plots_app = typer.Typer()
processes_app = typer.Typer()

# Add sub-command groups to main app
app.add_typer(plots_app, name="plots",
              help="Trial plots management in OGC SensorThings API commands")
app.add_typer(processes_app, name="processes",
              help="OGC API - Processes commands")


# Main callback


def _version_callback(value: bool) -> None:
    clear()
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    """
    Raster2Sensor - A tool for raster data processing and OGC SensorThings API integration.
    """
    return


# =============================================================================
# PLOTS COMMANDS
# =============================================================================

@plots_app.command("fetch")
def fetch_plots(
    trial_id: str = typer.Option(
        None, help="Trial identifier to fetch plots for"),
    sensorthingsapi_url: str = typer.Option(None, help="SensorThingsAPI URL"),
    config_file: str = typer.Option(
        None, "--config", help="Path to configuration file (YAML or JSON) containing sensorthingsapi_url and trial_id")
):
    """
    Fetch plots GeoJSON for a given trial ID.

    You can provide either:
    - Individual parameters: --trial-id and --sensorthingsapi-url
    - Configuration file: --config (containing sensorthingsapi_url and trial_id)

    Args:
        trial_id: The trial identifier to fetch plots for
        sensorthingsapi_url: SensorThings API URL
        config_file: Path to configuration file
    """
    clear()

    # Validate input parameters
    if config_file and (trial_id or sensorthingsapi_url):
        logger.error(
            "Cannot specify both --config and individual parameters (--trial-id, --sensorthingsapi-url). Choose one approach.")
        raise typer.Exit(1)

    if not config_file and not (trial_id and sensorthingsapi_url):
        logger.error(
            "Must specify either --config file OR both --trial-id and --sensorthingsapi-url")
        raise typer.Exit(1)

    try:
        if config_file:
            # Load configuration from file
            logger.info(f"Loading configuration from: {config_file}")
            config = ConfigParser.load_config(config_file)
            effective_trial_id = config.trial_id
            effective_sensorthingsapi_url = config.sensorthingsapi_url
            logger.info(f"Using trial_id from config: {effective_trial_id}")
            logger.info(
                f"Using sensorthingsapi_url from config: {effective_sensorthingsapi_url}")
        else:
            # Use provided arguments
            effective_trial_id = trial_id
            effective_sensorthingsapi_url = sensorthingsapi_url
            logger.info(f"Using provided trial_id: {effective_trial_id}")
            logger.info(
                f"Using provided sensorthingsapi_url: {effective_sensorthingsapi_url}")

        logger.info(f"Fetching plots for trial ID: {effective_trial_id}")
        plots_geojson = Plots.fetch_plots_geojson(
            effective_sensorthingsapi_url, effective_trial_id)

        # Log success and provide summary
        num_plots = len(plots_geojson.get('features', []))
        logger.info(
            f"✓ Successfully fetched {num_plots} plots for trial: {effective_trial_id}")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error fetching plots: {e}")
        raise typer.Exit(1)


@plots_app.command("create")
def create_plots(
    file_path: str = typer.Option(..., help="Path to plots GeoJSON/Shapefile"),
    config_file: str = typer.Option(
        ..., "--config", help="Path to unified configuration file (YAML/JSON) containing datastreams, trial metadata, etc."),
    sensorthingsapi_url: str = typer.Option(
        None, help="Override SensorThingsAPI URL from config"),
    trial_id: str = typer.Option(None,
                                 help="Override trial identifier from config"),
    plot_id_field: str = typer.Option(None,
                                      help="Override field name containing plot IDs from config"),
    treatment_id_field: str = typer.Option(
        "", help="Field name containing treatment IDs (optional)"),
    year: int = typer.Option(
        None, help="Override year from config (defaults to current year)")
):
    """
    Create plots as Things in SensorThingsAPI.

    This command creates SensorThings API Things entities for each plot in the provided
    GeoJSON or Shapefile, along with the specified parameters.

    You can provide either:  
    - A unified configuration file (--config) that contains all parameters
    - Individual parameters 

    Parameters from the config file will be used unless explicitly overridden via command line options.
    """
    clear()
    logger.info("Creating SensorThingsAPI Things Entities...")

    try:
        # Load from configuration file
        logger.info(f"Loading configuration from: {config_file}")
        config = ConfigParser.load_config(config_file)

        # Use config values or CLI overrides
        effective_sensorthingsapi_url = sensorthingsapi_url or config.sensorthingsapi_url
        effective_trial_id = trial_id or config.trial_id
        effective_plot_id_field = plot_id_field or config.plot_id_field
        effective_year = year or config.year or datetime.now().year

        if not effective_sensorthingsapi_url:
            logger.error(
                "❌ sensorthingsapi_url must be specified in config file or via --sensorthingsapi-url parameter")
            raise typer.Exit(1)
        if not effective_trial_id:
            logger.error(
                "❌ trial_id must be specified in config file or via --trial-id parameter")
            raise typer.Exit(1)
        if not effective_plot_id_field:
            logger.error(
                "❌ plot_id_field must be specified in config file or via --plot-id-field parameter")
            raise typer.Exit(1)

        # Load datastreams from config
        datastreams = load_datastreams_from_config(config_file)
        logger.debug(
            f"Loaded {len(datastreams)} datastreams from configuration")

        logger.info(
            f"Using sensorthingsapi_url: {effective_sensorthingsapi_url}")
        logger.info(
            f"Using trial_id: {effective_trial_id}, plot_id_field: {effective_plot_id_field}, year: {effective_year}")

        # Create Plots instance with datastreams
        plots = Plots(
            sensorthingsapi_url=effective_sensorthingsapi_url,
            file_path=Path(file_path),
            trial_id=effective_trial_id,
            plot_id_field=effective_plot_id_field,
            treatment_id_field=treatment_id_field,
            year=effective_year,
            datastreams=datastreams
        )

        # Create SensorThings API Things
        plots.create_sensorthings_things()

        logger.info(
            f"Successfully created SensorThings API entities for trial: {effective_trial_id}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error creating plots: {e}")
        raise typer.Exit(1)


@plots_app.command("add-datastreams")
def add_datastreams(
    trial_id: str = typer.Option(...,
                                 help="Trial identifier to add datastreams to"),
    config_file: str = typer.Option(
        ..., "--config", help="Path to configuration file (YAML/JSON) containing datastream configurations and sensorthingsapi_url"),
    sensorthingsapi_url: str = typer.Option(
        None, help="Override SensorThingsAPI URL from config")
):
    """
    Add datastreams to existing plots (SensorThings API Things).

    This command adds additional datastreams to existing SensorThings API Things
    for the specified trial. You must provide a configuration file with datastream definitions.
    """
    clear()
    logger.info(f"Adding datastreams for trial ID: {trial_id}")

    try:
        # Load from configuration file
        logger.info(f"Loading configuration from: {config_file}")
        config = ConfigParser.load_config(config_file)

        # Use config value or CLI override for sensorthingsapi_url
        effective_sensorthingsapi_url = sensorthingsapi_url or config.sensorthingsapi_url

        if not effective_sensorthingsapi_url:
            logger.error(
                "sensorthingsapi_url must be specified in config file or via --sensorthingsapi-url parameter")
            raise typer.Exit(1)

        # Load datastreams from config file
        datastreams = load_datastreams_from_config(config_file)
        logger.info(
            f"Loaded {len(datastreams)} datastreams from configuration")

        logger.info(
            f"Using SensorThings API URL: {effective_sensorthingsapi_url}")

        # Call the static method with all required parameters
        Plots.add_datastreams(
            effective_sensorthingsapi_url, trial_id, datastreams)

        logger.info(f"Successfully added datastreams for trial: {trial_id}")

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error adding datastreams for trial {trial_id}: {e}")
        raise typer.Exit(1)


# =============================================================================
# PROCESSES COMMANDS
# =============================================================================

@processes_app.command("fetch")
def fetch_processes(
    pygeoapi_url: str = typer.Option(None, help="PyGeoAPI URL"),
    config_file: str = typer.Option(
        None, "--config", help="Path to configuration file (YAML or JSON) containing pygeoapi_url")
):
    """
    Fetch available OGC API Processes.

    You can provide either:
    - Individual parameter: --pygeoapi-url
    - Configuration file: --config (containing pygeoapi_url)
    """
    clear()

    # Validate input parameters
    if config_file and pygeoapi_url:
        logger.error(
            "Cannot specify both --config and --pygeoapi-url. Choose one approach.")
        raise typer.Exit(1)

    if not config_file and not pygeoapi_url:
        logger.error(
            "Must specify either --config file OR --pygeoapi-url")
        raise typer.Exit(1)

    try:
        if config_file:
            # Load configuration from file
            logger.info(f"Loading configuration from: {config_file}")
            config = ConfigParser.load_config(config_file)
            effective_pygeoapi_url = config.pygeoapi_url
            logger.info(
                f"Using pygeoapi_url from config: {effective_pygeoapi_url}")
        else:
            # Use provided argument
            effective_pygeoapi_url = pygeoapi_url
            logger.info(
                f"Using provided pygeoapi_url: {effective_pygeoapi_url}")

        if not effective_pygeoapi_url:
            logger.error("pygeoapi_url must be specified")
            raise typer.Exit(1)

        # Initialize OGC API Processes with the effective URL
        ogc_processes = OGCAPIProcesses(effective_pygeoapi_url)
        ogc_processes.get_processes()

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error fetching processes: {e}")
        raise typer.Exit(1)


@processes_app.command("describe")
def describe_process(
    process_id: str = typer.Option(...,
                                   help="The ID of the process to describe"),
    pygeoapi_url: str = typer.Option(None, help="PyGeoAPI URL"),
    config_file: str = typer.Option(
        None, "--config", help="Path to configuration file (YAML or JSON) containing pygeoapi_url")
):
    """
    Describe a specific OGC API Process.

    You can provide either:
    - Individual parameter: --pygeoapi-url
    - Configuration file: --config (containing pygeoapi_url)

    Args:
        process_id: The ID of the process to describe
        pygeoapi_url: PyGeoAPI URL 
        config_file: Path to configuration file
    """
    clear()

    # Validate input parameters
    if config_file and pygeoapi_url:
        logger.error(
            "Cannot specify both --config and --pygeoapi-url. Choose one approach.")
        raise typer.Exit(1)

    if not config_file and not pygeoapi_url:
        logger.error(
            "Must specify either --config file OR --pygeoapi-url")
        raise typer.Exit(1)

    try:
        if config_file:
            # Load configuration from file
            logger.info(f"Loading configuration from: {config_file}")
            config = ConfigParser.load_config(config_file)
            effective_pygeoapi_url = config.pygeoapi_url
            logger.info(
                f"Using pygeoapi_url from config: {effective_pygeoapi_url}")
        else:
            # Use provided argument
            effective_pygeoapi_url = pygeoapi_url
            logger.info(
                f"Using provided pygeoapi_url: {effective_pygeoapi_url}")

        if not effective_pygeoapi_url:
            logger.error("pygeoapi_url must be specified")
            raise typer.Exit(1)

        # Initialize OGC API Processes with the effective URL
        ogc_processes = OGCAPIProcesses(effective_pygeoapi_url)
        ogc_processes.describe_process(process_id)

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error describing process {process_id}: {e}")
        raise typer.Exit(1)


# TODO: Generic execute command
@processes_app.command("execute")
def execute_process(
    process_id: str = typer.Option(...,
                                   help="The ID of the process to execute"),
    pygeoapi_url: str = typer.Option(None, help="PyGeoAPI URL"),
    config_file: str = typer.Option(
        None, "--config", help="Path to configuration file (YAML or JSON) containing pygeoapi_url"),
    input_file: Optional[str] = typer.Option(None, help="Input file path"),
    output_file: Optional[str] = typer.Option(None, help="Output file path"),
    sync: bool = typer.Option(True, help="Execute synchronously")
):
    """
    Execute a specific OGC API Process.

    You can provide either:
    - Individual parameter: --pygeoapi-url
    - Configuration file: --config (containing pygeoapi_url)

    Args:
        process_id: The ID of the process to execute
        pygeoapi_url: PyGeoAPI URL
        config_file: Path to configuration file
        input_file: Path to input file (optional)
        output_file: Path to output file (optional)
        sync: Whether to execute synchronously (default: True)
    """
    clear()

    # Validate input parameters
    if config_file and pygeoapi_url:
        logger.error(
            "Cannot specify both --config and --pygeoapi-url. Choose one approach.")
        raise typer.Exit(1)

    if not config_file and not pygeoapi_url:
        logger.error(
            "Must specify either --config file OR --pygeoapi-url")
        raise typer.Exit(1)

    try:
        if config_file:
            # Load configuration from file
            logger.info(f"Loading configuration from: {config_file}")
            config = ConfigParser.load_config(config_file)
            effective_pygeoapi_url = config.pygeoapi_url
            logger.info(
                f"Using pygeoapi_url from config: {effective_pygeoapi_url}")
        else:
            # Use provided argument
            effective_pygeoapi_url = pygeoapi_url
            logger.info(
                f"Using provided pygeoapi_url: {effective_pygeoapi_url}")

        if not effective_pygeoapi_url:
            logger.error("pygeoapi_url must be specified")
            raise typer.Exit(1)

        console.print(f"[cyan]Executing process: {process_id}[/cyan]")
        console.print(f"[dim]PyGeoAPI URL: {effective_pygeoapi_url}[/dim]")

        if input_file:
            console.print(f"[dim]Input file: {input_file}[/dim]")
        if output_file:
            console.print(f"[dim]Output file: {output_file}[/dim]")

        execution_mode = "synchronous" if sync else "asynchronous"
        console.print(f"[dim]Execution mode: {execution_mode}[/dim]")

        # TODO: Implement process execution functionality
        console.print(
            '[yellow]Note: execute_process() function needs implementation[/yellow]')

        # Initialize OGC API Processes with the effective URL
        # ogc_processes = OGCAPIProcesses(effective_pygeoapi_url)
        # ogc_processes.execute_process(process_id, input_data, sync)

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error executing process {process_id}: {e}")
        raise typer.Exit(1)


@app.command("process-images")
def process_images(
    config_file: str = typer.Option(
        ...,
        "--config",
        help="Path to unified configuration file (YAML or JSON) containing datastreams, raster images, and vegetation indices"
    ),
    trial_id: Optional[str] = typer.Option(
        None,
        "--trial-id",
        help="Override trial ID from config file"
    ),
    indices: Optional[str] = typer.Option(
        None,
        "--indices",
        help="Comma-separated list of vegetation indices to process (e.g., 'ndvi,ndre'). If not specified, processes all indices from config."
    ),
    images: Optional[str] = typer.Option(
        None,
        "--images",
        help="Comma-separated list of image paths to process. If not specified, processes all images from config."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be processed without actually executing"
    )
):
    """
    Process raster images to calculate vegetation indices and create SensorThingsAPI observations.

    This command allows you to:
    - Process multiple raster images with multiple vegetation indices
    - Calculate zonal statistics for trial plots
    - Create observations in the SensorThings API

    The configuration file should contain:
    - datastreams: SensorThings API datastream definitions
    - raster_images: List of raster files with timestamps
    - vegetation_indices: List of processes with band configurations
    - Trial metadata: trial_id, plot_id_field, year
    - sensorthingsapi_url: SensorThings API URL
    - pygeoapi_url: PyGeoAPI URL
    """
    clear()
    console.print(
        "[cyan]Processing raster images with vegetation indices[/cyan]")

    try:
        # Load configuration
        logger.info(f"Loading configuration from: {config_file}")
        config = ConfigParser.load_config(config_file)
        logger.info("✓ Configuration loaded successfully")

        # Override trial_id if provided
        if trial_id:
            config.trial_id = trial_id
            logger.info(f"Override trial_id: {trial_id}")

        if not config.trial_id:
            logger.error(
                "trial_id must be specified in config file or via --trial-id parameter")
            raise typer.Exit(1)

        # Filter vegetation indices if specified
        if indices:
            requested_indices = [idx.strip() for idx in indices.split(',')]
            filtered_indices = [
                vi for vi in config.vegetation_indices
                if vi.process in requested_indices
            ]
            if not filtered_indices:
                logger.error(
                    f"No matching vegetation indices found for: {requested_indices}")
                raise typer.Exit(1)
            config.vegetation_indices = filtered_indices
            logger.info(
                f"Filtering to indices: {[vi.process for vi in filtered_indices]}")

        # Filter raster images if specified
        if images:
            requested_images = [img.strip() for img in images.split(',')]
            filtered_images = [
                img for img in config.raster_images
                if any(req_img in img.path for req_img in requested_images)
            ]
            if not filtered_images:
                logger.error(
                    f"No matching raster images found for: {requested_images}")
                raise typer.Exit(1)
            config.raster_images = filtered_images
            logger.info(f"Filtering to {len(filtered_images)} raster images")

        # Display processing plan
        logger.info(
            f"Processing Plan - Trial ID: {config.trial_id}, Raster Images: {len(config.raster_images)}, Vegetation Indices: {len(config.vegetation_indices)}, Total Processes: {len(config.raster_images) * len(config.vegetation_indices)}")

        if dry_run:
            console.print(
                "\n[yellow]DRY RUN - Showing what would be processed:[/yellow]")
            # Display processing plan
            console.print("\n[bold]Processing Plan:[/bold]")
            console.print(f"Trial ID: [cyan]{config.trial_id}[/cyan]")
            console.print(
                f"Raster Images: [yellow]{len(config.raster_images)}[/yellow]")
            console.print(
                f"Vegetation Indices: [yellow]{len(config.vegetation_indices)}[/yellow]")
            console.print(
                f"Total Processes: [yellow]{len(config.raster_images) * len(config.vegetation_indices)}[/yellow]")
            console.print("\n[bold]Raster Images:[/bold]")
            for img in config.raster_images:
                console.print(f"  • {img.path} ({img.timestamp})")

            console.print("\n[bold]Vegetation Indices:[/bold]")
            for vi in config.vegetation_indices:
                bands_str = ", ".join(
                    [f"{k}={v}" for k, v in vi.bands.items()])
                console.print(
                    f"  • {vi.name} ({vi.process}) - Bands: {bands_str}")

            console.print(
                "\n[yellow]Use --no-dry-run to execute the processing[/yellow]")
            return

        # Confirm processing
        if not typer.confirm("\nProceed with processing?"):
            console.print("[yellow]Processing cancelled[/yellow]")
            raise typer.Exit(0)

        # Create processor and execute
        logger.info("Initializing image processor")
        processor = ImageProcessor(
            pygeoapi_url=config.pygeoapi_url,
            trial_id=config.trial_id,
            raster_images=config.raster_images,
            vegetation_indices=config.vegetation_indices,
            sensorthingsapi_url=config.sensorthingsapi_url
        )

        # Process images
        logger.info("Starting image processing")
        results = processor.process()

        # Print summary
        logger.info("Processing completed!")
        ImageProcessor.log_results_summary(results)

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")

        raise typer.Exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")

        raise typer.Exit(1)
    except Exception as e:
        logger.error(f"Error processing images: {e}")
        raise typer.Exit(1)


@app.command("create-sample-config")
def create_sample_config(
    output_path: str = typer.Option(
        "config.yml",
        "--output",
        help="Output path for the sample configuration file"
    ),
    format: str = typer.Option(
        "yaml",
        "--format",
        help="Configuration format: 'yaml' or 'json'"
    )
):
    """
    Create a sample configuration file with all parameters required to run raster2sensor tool.

    This creates a comprehensive configuration file, which includes trial metadata, datastreams, raster images, and vegetation indices.
    """
    clear()
    logger.info("Creating sample configuration file")

    try:
        ConfigParser.create_sample_config(output_path, format)
        console.print(
            f"[green]✓[/green] Sample configuration created: [cyan]{output_path}[/cyan]")
        console.print("\nYou can now edit this file and use it, e.g.:")
        console.print(
            f"[dim]python -m raster2sensor process-images --config {output_path}[/dim]")

    except Exception as e:
        logger.error(f"Error creating sample configuration: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
