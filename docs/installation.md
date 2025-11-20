# Installation

## Minimal

Stable releases of `compas_fea2` can be installed from PyPI using `pip`.

```bash
pip install compas_fea2
```

This will install the main `compas_fea2` package, without any analysis backends.
Although you can't run any analyses with this setup, you can still define and inspect analysis models.

## Backends

To actually run an analysis, at least one of the supported backends should be installed.
To install a backend explicitly, using `pip`, check out the installation instructions of the backend itself.
Backends can also be installed as "optional dependencies" of the core package (`compas_fea2`).

```bash
pip install "compas_fea2[opensees]"
```

!!! note

    Installing the `compas_fea2` backend Python package (e.g. `compas_fea2_opensees`) alone is not enough.
    The backend software/solver has to be installed on your system as well.

## Full

To install `compas_fea2` with backends and visualisation support, we recommend using `conda` and a `conda` environment.

```bash
conda create -n fea2 python pip compas compas_occ compas_viewer
conda activate fea2
pip install "compas_fea2[opensees,abaqus]"
```

## Development

For development, you may want to use the preconfigured environment available in the repository.

```bash
git clone https://github.com/compas-dev/compas_fea2.git
cd compas_fea2
conda env create -f environment.yml
conda activate fea2-dev
```
