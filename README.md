# pyTRACK-CMIP6: A Python Wrapper Library to Adapt TRACK for CMIP6 Input and Extratropical Cyclone Analysis

[TRACK](http://www.nerc-essc.ac.uk/~kih/TRACK/Track.html) is a powerful storm tracking software package that automatically identifies and tracks storm features in model and observational data. pyTRACK-CMIP6 is intended to be a Python 3 wrapper for using TRACK on mean sea level pressure (MSLP) data and 850 hPa vorticity data, calculated from horizontal winds, from phase 6 of the Coupled Model Intercomparison Project (CMIP6). pyTRACK-CMIP6 also includes functionality to run TRACK on ERA5 reanalysis MSLP and vorticity data calculated from horizontal winds.

## Installation Guide

The pyTRACK-CMIP6 functionalities require a Linux system with standard setups of GCC, GFortran and NetCDF, as well as a working installation of TRACK. To install TRACK, you will need to download it from its [homepage](http://www.nerc-essc.ac.uk/~kih/TRACK/Track.html). For permission to download, please contact the author of TRACK, Dr Kevin Hodges. Note that TRACK will soon be available via GitLabs. Once you have downloaded the TRACK tarball, please place it in your home directory and untar. Then, to complete the installation process, you can run the `linux_track_installation` script included in this repository.

Once TRACK is installed in your home directory, please clone this repository with the following command in the Linux command line. This is a necessary step because the input files stored in this repository are needed to configure and set up TRACK.
```
git clone https://github.com/acse-hvs119/TRACK-cmip6.git
```

Please ensure that you have Python 3 installed. You can check your version by running the following. Note that on machines with Python 2.7 installed beforehand, the command to call Python 3 would be `python3` instead of `python`.
```
python --version
```

Next, run this from the pyTRACK-CMIP6 directory in order to configure TRACK for use by pyTRACK-CMIP6:
```
python setup_track.py
```

Please install the Python 3 dependencies of this package by running:
```
pip install -r python_requirements.txt
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

For individual functions separate from the wrappers, please refer to the documentation included in the `html` folder in this repository about details and usage.


## Using pyTRACK-CMIP6 on JASMIN

It is possible to use pyTRACK-CMIP6 on JASMIN, but it will require a few extra steps due to the way that NetCDF is set up there. If you are using JASMIN, please also have TRACK in your home directory and refer to the following method to install TRACK:
```
module load netcdf/gnu/4.4.7/4.3.2
export CC=gcc FC=gfortran ARFLAGS=
export NETCDF=/apps/libs/netCDF/gnu4.4.7/4.3.2
export PATH=${PATH}:.
```
Then, from within the `~/TRACK-1.5.2` directory, run:
```
master -build -i=linux -f=linux
make utils
```

After that, in order to run Python 3 and install the necessary dependencies for pyTRACK-CMIP6, a Python virtual environment is needed. To create one and activate it, please follow the steps below:
```
module load jaspy
python -m venv --system-site-packages [/path/to/my_virtual_env]
source [/path/to/my_virtual_env]/bin/activate
```
To activate it in every session afterwards, only the last line is needed.

Once the Python virtual environment is set up, follow the installation steps from above.

Before using the functions as described in the user instructions section, please make sure to load the netcdf module and that the NETCDF environment variable is set.
```
module load netcdf/gnu/4.4.7/4.3.2
export NETCDF=/apps/libs/netCDF/gnu4.4.7/4.3.2
```
Then, pyTRACK-CMIP6 can be run as usual.
