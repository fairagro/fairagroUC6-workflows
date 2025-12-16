FROM rocker/r-ver:4.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgdal-dev \
    libudunits2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R package dependencies
RUN R -e "install.packages(c('devtools', 'remotes', 'argparse', 'dplyr', 'readr', 'jsonlite', 'lubridate'), repos='https://cloud.r-project.org/')"

# Install csmTools from GitHub
RUN R -e "remotes::install_github('leroy-bml/uc6_csmTools')"

# Copy the CLI script
COPY csmtools_cli.R /opt/csmtools_cli.R
RUN chmod +x /opt/csmtools_cli.R

# Set working directory
WORKDIR /work

CMD ["R"]
