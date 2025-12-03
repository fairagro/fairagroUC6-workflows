# FAIRagro UC6 Workflows

## Usage

### Create commands

``` bash
s4n create -n process-images python workflows/scripts/main.py process-images --help
```

### Execute Commands

``` bash
s4n execute local workflows/process-images/process-images.cwl
```

### Pending Issues

- Creating workflows with an array of inputs using the cli tool

