# =============================================================================
# climdata-cli — climdata (https://github.com/Kaushikreddym/climdata) wrapped
# as CWL-friendly commands for the FAIRagro UC6 workflow:
#   get-climdata-weather            → retrieve weather via climdata providers
#   convert-climdata-weather-icasa  → convert the result to ICASA JSON
#
# Size: climdata's install_requires pulls in a GUI (PyQt5), plotting, ML and
# notebook tooling (~4.3 GB image). Here climdata is installed with --no-deps
# and only the packages its weather providers import at runtime are added
# (~2.8 GB, ~620 MB compressed).
# =============================================================================
FROM mambaorg/micromamba:1.5.10

ARG CLIMDATA_VERSION=1.0.1

# Compiled geo stack from conda-forge, climdata itself from PyPI without deps.
RUN micromamba install -y -n base -c conda-forge \
        python=3.11 pip \
        numpy pandas scipy xarray dask-core zarr fsspec gcsfs \
        netcdf4 h5netcdf cftime bottleneck numexpr \
        geopandas-base shapely pyproj rasterio rioxarray affine \
        xclim cf_xarray hydra-core omegaconf \
        cdsapi google-api-python-client google-auth \
        intake intake-esm wetterdienst \
        matplotlib-base scikit-learn \
        requests aiohttp tqdm toml ujson pyyaml beautifulsoup4 && \
    micromamba run -n base pip install --no-cache-dir \
        pymannkendall isimip-client && \
    micromamba run -n base pip install --no-cache-dir --no-deps \
        "climdata==${CLIMDATA_VERSION}" && \
    micromamba clean --all --force-pkgs-dirs --yes && \
    find /opt/conda -name '*.a' -delete && \
    find /opt/conda/lib/python3.11/site-packages -type d \( -name tests -o -name test \) -prune -exec rm -rf {} + && \
    rm -rf /opt/conda/lib/python3.11/site-packages/climdata_gui \
           /opt/conda/lib/python3.11/site-packages/climdata/sdba_usecase

USER root
RUN for cmd in get-climdata-weather convert-climdata-weather-icasa; do \
        printf '#!/bin/sh\nexec /opt/conda/bin/python /opt/climdata-cli/climdata_cli.py %s "$@"\n' "$cmd" \
            > /usr/local/bin/$cmd && chmod 755 /usr/local/bin/$cmd; \
    done

# Writable caches for arbitrary UIDs (s4n runs with --user=<host uid>)
ENV PATH=/opt/conda/bin:$PATH \
    MPLCONFIGDIR=/tmp/matplotlib \
    XDG_CACHE_HOME=/tmp/.cache \
    HOME=/tmp

# Copied last so editing the CLI only rebuilds this layer
COPY --chmod=755 climdata_cli.py /opt/climdata-cli/climdata_cli.py

USER $MAMBA_USER
WORKDIR /tmp
# No ENTRYPOINT: CWL invokes the commands above directly.
ENTRYPOINT []
CMD ["get-climdata-weather", "--help"]
