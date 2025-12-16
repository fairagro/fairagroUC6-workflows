FROM rocker/r-ver:4.3

# Install essential system dependencies
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgdal-dev \
    libudunits2-dev \
    libproj-dev \
    libgeos-dev \
    libsqlite3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone csmtools repository and move to /uc6_csmtools directory, make it WORKDIR
RUN git clone https://github.com/leroy-bml/uc6_csmTools.git /uc6_csmTools
WORKDIR /uc6_csmTools

# Install system dependencies (using scripts from the cloned repo)
RUN chmod +x ./install_requirements.sh && ./install_requirements.sh

# install DSSAT (using scripts from the cloned repo)
RUN chmod +x ./install_dssat.sh && ./install_dssat.sh

# Install R packages with CRAN mirror
RUN R -e 'install.packages(c("remotes", "argparse"), repos="https://cloud.r-project.org/")' 

# Install csmTools package directly from GitHub (this will install all dependencies)
RUN R -e 'remotes::install_github("leroy-bml/uc6_csmTools", dependencies=TRUE)'

# Copy the CLI script
COPY csmtools_cli.R /uc6_csmTools/csmtools_cli.R
RUN chmod +x /uc6_csmTools/csmtools_cli.R


CMD ["Rscript", "/uc6_csmTools/csmtools_cli.R"]
