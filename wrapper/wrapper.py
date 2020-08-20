import os
import numpy as np
from cdo import *
from netCDF4 import Dataset
from pathlib import Path
from math import ceil

cdo = Cdo()

__all__ = ['cmip6_indat', 'regrid_cmip6', 'setup_track', 'calc_vorticity',
           'track_mslp', 'track_uv_vor850']

class cmip6_indat(object):
    """Class to obtain information about the CMIP6 input data."""
    def __init__(self, filename):
        """
        Reads the netCDF file and scans its variables.

        Parameters
        ----------

        filename : string
            Filename of a .nc file containing CMIP6 sea level pressure or wind
            velocity data.

        """
        self.filename = filename
        self.data = Dataset(filename, 'r')
        self.vars = [var for var in self.data.variables]

    def get_nx_ny(self):
        # returns number of latitudes and longitudes in the grid
        return str(len(self.data.variables['lon'][:])), str(len(self.data.variables['lat'][:]))

    def get_grid_type(self):
        # returns the grid type
        return cdo.griddes(input=self.filename)[3]

    def get_variable_type(self):
        # returns the variable type
        return self.vars[-1]

    def get_timesteps(self):
        # returns the number of timesteps
        return str(len(data.variables['time'][:]))

def merge_uv(u_file, v_file, outfile):
    """
    Merge U and V files into a UV file.

    MAYBE DELETE AND JUST SAY HOW TO USE CDO.....
    """
    #outfile = "~/TRACK-1.5.2/indat/uv" + u_file[2:]
    cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
    return

def regrid_cmip6(input, outfile):
    """
    Detect grid of input CMIP6 data and regrid to gaussian grid if necessary.

    Parameters
    ----------

    input : string
        Path to .nc file containing input data

    outfile : string
        Desired path of regridded file

    """
    data = cmip6_indat(input) # maybe do this outside of this function

    gridtype = data.get_grid_type()

    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")

    # check for resolution and regrid
    else:
        nx, ny = data.get_nx_ny()
        #outfile = input[:-3] + "_gaussian.nc"
        
        # T42
        if int(ny) <= 64:
            cdo.remapcon("n32", input=input, output=outfile)
        # T63
        elif int(ny) <= 96:
            cdo.remapcon("n48", input=input, output=outfile)
        # T80
        elif int(ny) <= 128:
            cdo.remapcon("n64", input=input, output=outfile)
        # T106?
        else:
            cdo.remapcon("n80", input=input, output=outfile)

        print("Regridded to gaussian grid.")
    return

def setup_track():
    """
    Configure template input files according to local machine setup and copy
    into TRACK directory for tracking.
    """
    ### edit RUNDATIN files
    # MSLP_A
    with open('indat/template.MSLP_A.in', 'r') as file:
        contents = file.read()
    contents = contents.replace('DIR', str(Path.home()))
    with open('indat/RUNDATIN.MSLP_A.in', "w") as file:
        file.write(contents)

    # VOR
    with open('indat/template.VOR.in', 'r') as file:
        contents = file.read()
    contents = contents.replace('DIR', str(Path.home()))
    with open('indat/RUNDATIN.VOR.in', "w") as file:
        file.write(contents)

    # VOR_A
    with open('indat/template.VOR_A.in', 'r') as file:
        contents = file.read()
    contents = contents.replace('DIR', str(Path.home()))
    with open('indat/RUNDATIN.VOR_A.in', "w") as file:
        file.write(contents)

    ### copy files into local TRACK directory
    os.system("cp trackdir/* " + str(Path.home()) + "/TRACK-1.5.2/")
    os.system("cp indat/RUNDATIN.* " + str(Path.home()) + "/TRACK-1.5.2/indat")
    os.system("cp data/* " + str(Path.home()) + "/TRACK-1.5.2/data")
    os.system("cp tr2nc_new.tar " + str(Path.home()) + "/TRACK-1.5.2/utils")
    return

def calc_vorticity(uv_file, outfile):
    """
    Use TRACK to calculate vorticity at 850 hPa from horizontal wind velocities.

    Parameters
    ----------

    uv_file : string
        Path to .nc file containing combined U and V data

    outfile : string
        Desired path of vorticity file

    """
    # gather information about data
    uv = cmip6_indat(uv_file)
    nx, ny = uv.get_nx_ny()
    year = cdo.showyear(input=uv_file)[0]
    u_name = uv.vars[-2]
    v_name = uv.vars[-1]
    
    # copy input files to necessary directories for TRACK to find
    tempname = "temp_file.nc"
    os.system("cp " + uv_file + " " + str(Path.home()) + "/TRACK-1.5.2/indat/" + \
              tempname)

    # generate input file and calculate vorticity using TRACK
    line_1 = "sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" + nx + \
                "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile + \
                "/\" calcvor.in > calcvor.test"
    line_2 = "bin/track.linux -i " + tempname + " -f y" + year + " < calcvor.test"
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")
    os.system(line_1)
    os.system(line_2)

    return

def track_mslp(input, outdir):
    """
    Run TRACK on CMIP6 sea level pressure data.

    Parameters
    ----------

    input : string
        Path to .nc file containing CMIP6 psl data

    outdir : string
        Path of directory to output tracks to

    """
    input_basename = os.path.basename(input)
    print("Starting preprocessing.")
    
    # regrid
    regridded = input[:-3] + "_gaussian.nc"
    regrid_cmip6(input, regridded)
    
    # fill missing values
    filled = regridded[:-3] + "_filled.nc"
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + regridded +
              " " + filled)
    print("Filled missing values.")
    os.system("rm " + regridded)

    # get data info
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)

    # files need to be moved to TRACK directory for TRACK to find them
    # copy data into TRACK indat directory
    tempname = "temp_file.nc"
    os.system("cp " + filled + " " + str(Path.home()) + "/TRACK-1.5.2/indat/" +
              tempname)
    os.system("rm " + filled)
    print("Data copied into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        cdo.selyear(year, input="indat/"+tempname, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # spectral filtering
        # NOTE: NORTHERN HEMISPHERE; add SH option???
        if int(ny) >= 96: # T63
            fname = "T63filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/63/\" specfilt_nc.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + year + "_" + input_basename[:-3] + \
                        " -e=track.linux -d=now -i=" + fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T63_NH -n=1,62," + \
                        str(nchunks) + " -o=" + outdir + \
                        " -r=RUN_AT_ -s=RUNDATIN.MSLP"

        else: # T42
            fname = "T42filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/42/\" specfilt_nc.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + year + "_" + input_basename[:-3] + \
                        " -e=track.linux -d=now -i=" + fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T42_NH -n=1,62," + str(nchunks) + \
                        " -o=" + outdir + " -r=RUN_AT_ -s=RUNDATIN.MSLP"

        line_2 = "bin/track.linux -i " + year_file + " -f y" + year + \
                    " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

        # setting environment variables
        os.environ["CC"] = "gcc"
        os.environ["FC"] = "gfortran"
        os.environ["ARFLAGS"] = ""
        os.environ["PATH"] += ":." 

        # executing the lines to run TRACK
        print("Spectral filtering...")

        os.system(line_1)
        os.system(line_2)
        os.system(line_3)
        os.system(line_4)

        print("Running TRACK...")

        os.system(line_5)

        # cleanup
        os.system("rm indat/"+year_file)

    return

def track_uv_vor850(input, outdir):
    """
    Calculate 850 hPa vorticity from CMIP6 horizontal wind velocity data
    and run TRACK.

    Parameters
    ----------

    input : string
        Path to .nc file containing combined CMIP6 UV data

    outdir : string
        Path of directory to output tracks to

    """
    # regrid
    input_basename = os.path.basename(input)
    print("Starting preprocessing.")

    # regrid
    regridded = input[:-3] + "_gaussian.nc"
    regrid_cmip6(input, regridded)
    
    # fill missing values
    filled = regridded[:-3] + "_filled.nc"
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + regridded +
              " " + filled)
    print("Filled missing values.")
    os.system("rm " + regridded)

    # get data info
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)
    
    # copy data into TRACK indat directory
    ## files need to be moved to TRACK directory for TRACK to find them
    tempname = "temp_file.nc"
    os.system("cp " + filled + " " + str(Path.home()) + "/TRACK-1.5.2/indat/" +
              tempname)
    os.system("rm " + filled)
    print("Data copied into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")
    
    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        cdo.selyear(year, input="indat/"+tempname, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        tempname = "vor850_temp.dat"
        calc_vorticity("./indat/"+year_file, tempname)
        year_file = tempname

        # spectral filtering
        # NOTE: NORTHERN HEMISPHERE; add SH option???
        if int(ny) >= 96: # T63
            fname = "T63filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/63/\" specfilt.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + year + "_vor850_" + input_basename[:-3] + \
                        " -e=track.linux -d=now -i=" + fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T63_NH -n=1,62," + \
                        str(nchunks) + " -o=" + outdir + \
                        " -r=RUN_AT_ -s=RUNDATIN.VOR"

        else: # T42
            fname = "T42filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/42/\" specfilt.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + year + "_vor850_" + input_basename[:-3] + \
                        " -e=track.linux -d=now -i=" + fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T42_NH -n=1,62," + \
                        str(nchunks) + " -o=" + outdir + \
                        " -r=RUN_AT_ -s=RUNDATIN.VOR"

        line_2 = "bin/track.linux -i " + year_file + " -f y" + year + \
                    " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

        # setting environment variables
        os.environ["CC"] = "gcc"
        os.environ["FC"] = "gfortran"
        os.environ["ARFLAGS"] = ""
        os.environ["PATH"] += ":." 

        # executing the lines to run TRACK
        print("Spectral filtering...")

        os.system(line_1)
        os.system(line_2)
        os.system(line_3)
        os.system(line_4)

        print("Running TRACK...")

        os.system(line_5)

        # cleanup
        os.system("rm indat/"+year_file)
    
    return

def postprocess(input):
    """
    AHHHHHH
    """
    
    return
