# pyTRACK-CMIP6: A Python Wrapper Library to Adapt TRACK for CMIP6 Input and Extratropical Cyclone Analysis

[TRACK](http://www.nerc-essc.ac.uk/~kih/TRACK/Track.html) is a powerful storm tracking software package that automatically identifies and tracks storm features in model and observational data. pyTRACK-CMIP6 is intended to be a Python 3 wrapper for using TRACK on mean sea level pressure (MSLP) data and 850 hPa vorticity data, calculated from horizontal winds, from phase 6 of the Coupled Model Intercomparison Project (CMIP6). pyTRACK-CMIP6 also includes functionality to run TRACK on ERA5 reanalysis MSLP and vorticity data calculated from horizontal winds.

## Installation Guide

Note: If you plan to use this module on JASMIN, please first look at the "Using pyTRACK-CMIP6 on JASMIN" section at the end. If installing on a standard linux system, follow the instructions below.

To begin, please clone this repository with the following command in the Linux command line. This repository does not need to exist in the home directory, but this is a necessary step because the input files stored in this repository are needed to configure and set up TRACK.
```
git clone https://github.com/acse-hvs119/pyTRACK-CMIP6.git
```

The pyTRACK-CMIP6 functionalities require a Linux system with standard setups of GCC, GFortran and NetCDF, as well as a working installation of TRACK. Additionally, please make sure csh is installed. To install TRACK, you will need to download it from its [homepage](http://www.nerc-essc.ac.uk/~kih/TRACK/Track.html). For permission to download, please contact the author of TRACK, Dr Kevin Hodges. Note that TRACK will soon be available via GitLabs. Due to somce path dependencies in TRACK, it is highly recommended to install TRACK in your home folder. Once you have downloaded the TRACK tarball, please place it in your home directory and untar. Then, to complete the installation process, the `linux_track_installation.sh` script included in this repository can be used in the following way, from the `pyTRACK-CMIP6` directory:
```
sudo ./linux_track_installation.sh
```

Please ensure that you have Python 3.6 or above installed. You can check your version by running the following. Note that on machines with Python 2.7 installed beforehand, the command to call Python 3 would be `python3` instead of `python`.
```
python --version
```

Change into the pyTRACK-CMIP6 directory and install the Python 3 dependencies of this package by running:
```
pip install -r requirements.txt
```

Next, run this from the pyTRACK-CMIP6 directory in order to configure TRACK for use by pyTRACK-CMIP6:
```
python setup_track.py
```

Afterwards, if the pyTRACK-CMIP6 main wrapper functions are to be imported and run from any directory, please install the pyTRACK-CMIP6 module using pip by running the following:
```
pip install pyTRACK-CMIP6
```
Note that this will not enable to setup functions to run from anywhere, since those are dependent on files that exist in this repository. However, if the previous steps have been followed, the setup functions are not needed.


## User Instructions

After installation, the module can be imported with the following command, from within Python 3. If the repository was cloned but the package was not installed through pip, this can only be done from the main directory of this repository.
```
>>> import track_wrapper
```

#### CMIP6 TRACK wrapper functions

Before running the wrapper functions, please ensure that there is sufficient space available in your TRACK installation directory to store the input data and the preprocessing/TRACK outputs produced during runtime.
To run pyTRACK-CMIP6 on CMIP6 sea level pressure (psl) data:
```
>>> import track_wrapper
>>> track_wrapper.track_mslp('[path_to_input_file]', '[path_to_output_directory]', NH=[True/False], netcdf=[True/False])
```
The `NH` argument determines whether tracking will be done on the Northern Hemisphere (`NH=True`) or the Southern Hemisphere (`NH=False`). By default, if not specified, tracking will be run on the Northern Hemisphere. To track the other hemisphere, simply run the same command again with the opposite `NH` input. The `netcdf` argument is optional and determines whether or not the resultant TRACK output will be converted from ASCII to NetCDF format after tracking is done. Note that the paths can be either absolute or relative paths.

To perform tracking on vorticity data that is calculated from CMIP6 horizontal winds (U and V), you can either input two separate U and V files or combine them yourself and input a UV file.
```
>>> import track_wrapper
>>> track_wrapper.track_uv_vor850('[path_to_input_file]', '[path_to_output_directory]', infile2='[path_to_second_input_if_applicable]', NH=[True/False], netcdf=[True/False])
```
The `NH` and `netcdf` arguments are the same as with the MSLP function. The `infile2` argument is optional and should be used if U and V are input as separate files. If you are inputting a combined UV file containing both variables, just leave the `infile2` argument out. 

#### ERA5 TRACK wrapper functions

Example scripts to download ERA-5 data from the CDS (Copernicus Data Store) API are included in this repository.
To perform tracking on ERA-5, please make sure during download that the data downloaded is on a gaussian grid and run the following for MSLP:
```
>>> import track_wrapper
>>> track_wrapper.track_era5_mslp('[path_to_input_file]', '[path_to_output_directory]', NH=[True/False], netcdf=[True/False])
```
with the arguments being the same as for the CMIP6 wrapper functions above. For UV/vorticity, please ensure that U and V are downloaded in a single file.
```
>>> import track_wrapper
>>> track_wrapper.track_era5_vor850('[path_to_input_file]', '[path_to_output_directory]', NH=[True/False], netcdf=[True/False])
```

#### Other individual functions

If you wish to use the individual functions in this module outside of the wrappers, please refer to the documentation included in the `html` folder in this repository about details and usage.

#### TRACK Output

After running a wrapper function, if tracking succeeded, the output will be found in the specified output directory in the following format:

For MSLP data, only negative anomalies are tracked. The two output netCDF files containing the tracks are named `tr_trs_neg.nc` and `ff_trs_neg.nc`. `tr_trs_neg.nc` contains all tracks detected in the data, while `ff_trs_neg.nc` contains only filtered tracks that last longer than 48 hours and travel at least 1000 km.

For vorticity, both positive and negative anomalies are tracked, since cyclones are associated with positive anomalies in the Northern Hemisphere and negative anomalies in the Southern Hemisphere. There will be four output netCDF files that are named `tr_trs_pos.nc`, `tr_trs_neg.nc`, `ff_trs_pos.nc` and `ff_trs_neg.nc`. The `tr` files again contain all tracks and the `ff` files contain only filtered tracks that last longer than 48 hours and travel at least 1000 km.


#### Graphical postprocessing

Basic graphical postprocessing and examples are found in the `data` folder in the form of a Jupyter notebook. This is optional and to run requires the Basemap Python package to be installed.


## Using pyTRACK-CMIP6 on JASMIN

#### Installing TRACK

It is possible to use pyTRACK-CMIP6 on JASMIN, but the installation will require a few extra steps due to the way that NetCDF is set up there. Due to some path dependencies in TRACK, it is highly recommended to install TRACK in your home directory. Please ensure that enough disk space is available in your JASMIN home directory to accommodate copies of the input data in the TRACK directory, which is required for running TRACK. To install, please also have TRACK in your home directory and refer to the following method:
```
module load netcdf/gnu/4.4.7/4.3.2
export CC=gcc FC=gfortran ARFLAGS=
export NETCDF=/apps/libs/netCDF/gnu4.4.7/4.3.2
export PATH=${PATH}:.
```
Note that this only needs to be done for installation. Then, from within the `~/TRACK-1.5.2` directory, run:
```
master -build -i=linux -f=linux
make utils
```

#### Installing pyTRACK-CMIP6

Note that installation only needs to be completed once.

In order to run Python 3 and install the necessary dependencies for pyTRACK-CMIP6, a Python virtual environment is needed. To create one and activate it, please follow the steps below:
```
module load jaspy
python -m venv --system-site-packages [/path/to/my_virtual_env]
source [/path/to/my_virtual_env]/bin/activate
```

Once the Python virtual environment is set up and activated, follow the installation steps from above, in the "Installation Guide" section, from the beginning, to install pyTRACK-CMIP6 in your virtual environment. Make sure that the pyTRACK-CMIP6 python module and its dependencies are installed before use. 

It is important to note that the setup of the TR2NC utility that converts TRACK output to NetCDF format may fail the first time on JASMIN. However, it will usually install normally the second time - after running the `setup_track.py` script, please wait a while and run the following command from the TRACK directory:

```
make utils
```
And check that TR2NC was installed by making sure the `tr2nc` program exists under the directory `TRACK-1.5.2/utils/bin`.

#### Using pyTRACK-CMIP6

Right after installation, the module can be used as described in the "User Instructions" section. For every subsequent JASMIN session, please follow the steps below to activate the Python virtual environment:

```
module load jaspy
module load netcdf/gnu/4.4.7/4.3.2
export NETCDF=/apps/libs/netCDF/gnu4.4.7/4.3.2
source [/path/to/my_virtual_env]/bin/activate
```

Then, pyTRACK-CMIP6 can be run as usual.

