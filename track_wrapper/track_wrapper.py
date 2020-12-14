import os
from cdo import *
from netCDF4 import Dataset
from pathlib import Path
from math import ceil

cdo = Cdo()

__all__ = ['cmip6_indat', 'regrid_cmip6', 'setup_files', 'calc_vorticity',
           'track_mslp', 'track_uv_vor850', 'setup_tr2nc', 'track_era5_mslp',
           'track_era5_vor850', 'tr2nc_mslp', 'tr2nc_vor']

class cmip6_indat(object):
    """Class to obtain basic information about the CMIP6 input data."""
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
        return str(len(self.data.variables['lon'][:])), \
                str(len(self.data.variables['lat'][:]))

    def get_grid_type(self):
        # returns the grid type
        return cdo.griddes(input=self.filename)[3]

    def get_variable_type(self):
        # returns the variable type
        return self.vars[-1]

    def get_timesteps(self):
        # returns the number of timesteps
        return int(len(self.data.variables['time'][:]))

def setup_files():
    """
    Configure template input files according to local machine setup 
    and copy into TRACK directory for use during preprocessing and tracking.
    """
    # check if TRACK is installed
    if os.path.isdir(str(Path.home()) + "/TRACK-1.5.2") == False:
        raise Exception("TRACK-1.5.2 is not installed.")

    # edit RUNDATIN files
    for var in ['MSLP', 'MSLP_A', 'VOR', 'VOR_A']:
        with open('track_wrapper/indat/template.' + var + '.in', 'r') as file:
            contents = file.read()
        contents = contents.replace('DIR', str(Path.home()))
        with open('track_wrapper/indat/RUNDATIN.' + var + '.in', "w") as file:
            file.write(contents)

    # copy files into local TRACK directory
    os.system("cp track_wrapper/trackdir/* " + str(Path.home()) +
                "/TRACK-1.5.2/") # calcvor and specfilt files
    os.system("cp track_wrapper/indat/RUNDATIN.* " + str(Path.home()) +
                "/TRACK-1.5.2/indat") # RUNDATIN files
    os.system("cp track_wrapper/data/* " + str(Path.home()) +
                "/TRACK-1.5.2/data") # initial and adapt.dat0, zone.dat0
    os.system("cp track_wrapper/tr2nc_new.tar " + str(Path.home()) +
                "/TRACK-1.5.2/utils") # for TR2NC setup
    return

def setup_tr2nc():
    """
    Set up and compile TR2NC for converting TRACK output to NetCDF.
    """
    # check if tr2nc_new.tar file exists
    if os.path.isfile(str(Path.home()) + "/TRACK-1.5.2/utils/tr2nc_new.tar") == False:
        raise Exception("Please run the track_wrapper.setup_files function first.")

    os.system("cp track_wrapper/tr2nc_mslp.meta.elinor " + str(Path.home()) +
                "/TRACK-1.5.2/utils")

    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2/utils")
    os.system("mv TR2NC OLD_TR2NC")
    os.system("tar xvf tr2nc_new.tar")
    os.system("mv tr2nc_mslp.meta.elinor TR2NC/tr2nc_mslp.meta.elinor")

    os.environ["CC"] = "gcc"
    os.environ["FC"] = "gfortran"

    os.chdir(str(Path.home()) + "/TRACK-1.5.2")
    os.system("make utils")

    os.chdir(cwd)
    return

#
# =======================
# PREPROCESSING FUNCTIONS
# =======================
#

def merge_uv(file1, file2, outfile):
    """
    Merge CMIP6 U and V files into a UV file.

    Parameters
    ----------

    file1 : string
        Path to .nc file containing either U or V data

    file2 : string
        Path to .nc file containing either V or U data, opposite of file1

    outfile : string
        Path of desired output file

    """
    data1 = cmip6_indat(file1)
    data2 = cmip6_indat(file2)

    if data1.get_variable_type() == 'ua':
        u_file = file1
        v_file = file2

    elif data1.get_variable_type() == 'va':
        u_file = file2
        v_file = file1

    else:
        raise Exception("Invalid input variable type. Please input CMIP6 \
                            ua or va file.")

    cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
    print("Merged U and V files into UV file.")
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
    data = cmip6_indat(input)

    gridtype = data.get_grid_type()

    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")

    # check for resolution and regrid
    else:
        nx, ny = data.get_nx_ny()
        if int(ny) <= 80:
            cdo.remapcon("n32", input=input, output=outfile)
            grid = 'n32'
        elif int(ny) <= 112:
            cdo.remapcon("n48", input=input, output=outfile)
            grid = 'n48'
        elif int(ny) <= 150:
            cdo.remapcon("n64", input=input, output=outfile)
            grid = 'n64'
        else:
            cdo.remapcon("n80", input=input, output=outfile)
            grid = 'n80'
        print("Regridded to " + grid + " Gaussian grid.")

    return

def calc_vorticity(uv_file, outfile, copy_file=True, cmip6=True):
    """
    Use TRACK to calculate vorticity at 850 hPa from horizontal wind velocities.

    Parameters
    ----------

    uv_file : string
        Path to .nc file containing combined U and V data

    outfile : string
        Desired base name of .dat vorticity file that will be output into the
        TRACK-1.5.2/indat directory.

    copy_file : boolean, optional
        Whether or not the uv_file will be copied into the TRACK directory. This
        is not needed within the tracking functions, but needed for manual use.

    cmip6 : boolean, optional
        Whether or not input file is from CMIP6.

    """
    cwd = os.getcwd()

    # check if outfile is base name
    if (os.path.basename(outfile) != outfile) or (outfile[-4:] != '.dat'):
        raise Exception("Please input .dat file basename only. The output file " +
                            "will be found in the TRACK-1.5.2/indat directory.")

    # gather information about data
    year = cdo.showyear(input=uv_file)[0]

    if cmip6 == True:
        uv = cmip6_indat(uv_file)
        nx, ny = uv.get_nx_ny()
        u_name = uv.vars[-2]
        v_name = uv.vars[-1]

    else:
        uv = Dataset(uv_file, 'r')
        vars = [var for var in uv.variables]
        nx = str(len(uv.variables['lon'][:]))
        ny = str(len(uv.variables['lat'][:]))
        u_name = vars[-2]
        v_name = vars[-1]

    if copy_file == True: # copy input data to TRACK/indat directory
        tempname = "temp_file.nc"
        os.system("cp " + uv_file + " " + str(Path.home()) + 
                    "/TRACK-1.5.2/indat/" + tempname)
    else: # if uv_file is already in the TRACK-1.5.2/indat directory
        tempname = os.path.basename(uv_file)

    os.chdir(str(Path.home()) + "/TRACK-1.5.2") # change to TRACK-1.5.2 directory

    # generate input file and calculate vorticity using TRACK
    os.system("sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" +
                nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile +
                "/\" calcvor.in > calcvor.test")
    os.system("bin/track.linux -i " + tempname + " -f y" + year + " < calcvor.test")

    os.system("rm indat/" + tempname) # cleanup
    os.chdir(cwd) # change back to working directory

    return

#
# =============
# RUNNING TRACK
# =============
#

def track_mslp(input, outdirectory, NH=True, netcdf=True):
    """
    Run TRACK on CMIP6 sea level pressure data.

    Parameters
    ----------

    input : string
        Path to .nc file containing CMIP6 psl data

    outdirectory : string
        Path of directory to output tracks to

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    input_basename = os.path.basename(input)

    # files need to be moved to TRACK directory for TRACK to find them
    # copy data into TRACK indat directory
    tempname = "indat/temp_file.nc"
    os.system("cp " + input + " " + str(Path.home()) + "/TRACK-1.5.2/" +
              tempname)
    # os.system("rm " + filled)
    print("Data copied into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")

    data = cmip6_indat(tempname)

    if "psl" not in data.vars:
        raise Exception("Invalid input variable type. Please input CMIP6 psl file.")

    extr = tempname[:-3] + "_extr.nc"

    # remove unnecessary variables
    if "time_bnds" in data.vars:
        ncks = "time_bnds"
        if "lat_bnds" in data.vars:
            ncks += ",lat_bnds,lon_bnds"
        os.system("ncks -C -O -x -v " + ncks + " " + tempname + " " + extr)
    elif "lat_bnds" in data.vars:
        os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + tempname + " " + extr)
    else:
        extr = tempname

    print("Starting preprocessing.")

    gridtype = data.get_grid_type()
    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        gridcheck = extr

    else:
    # regrid
        gridcheck = tempname[:-3] + "_gaussian.nc"
        regrid_cmip6(extr, gridcheck)

    # fill missing values
    filled = gridcheck[:-3] + "_filled.nc"
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + gridcheck +
              " " + filled)
    print("Filled missing values, if any.")

    # clean up if it was regridded and if variables were removed
    if gridtype != 'gridtype  = gaussian':
        os.system("rm " + tempname[:-3] + "_gaussian.nc")
    if extr != tempname:
        os.system("rm " + extr)

    # get data info
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)[0].split()

    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        cdo.selyear(year, input=filled, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)
        c_input = year + "_" + hemisphere + "_" + input_basename[:-3]

        # spectral filtering
        if int(ny) >= 96: # T63
            fname = "T63filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/63/\" specfilt_nc.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                        fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
                        " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                        "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

        else: # T42
            fname = "T42filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/42/\" specfilt_nc.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                        fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
                        " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                        "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

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

        print("Turning track output to netCDF...")
        if netcdf == True:
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "/" + c_input + "/ff_trs_neg.gz'")
            os.system("gunzip '" + outdir + "/" + c_input + "/tr_trs_neg.gz'")
            tr2nc_mslp(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_mslp(outdir + "/" + c_input + "/tr_trs_neg")

    os.system("rm " + tempname)
    os.chdir(cwd)

    return

def track_uv_vor850(infile, outdirectory, infile2='none', NH=True, netcdf=True):
    """
    Calculate 850 hPa vorticity from CMIP6 horizontal wind velocity data
    and run TRACK.

    Parameters
    ----------

    infile : string
        Path to .nc file containing combined CMIP6 UV data

    outdirectory : string
        Path of directory to output tracks to

    infile2 : string, optional
        Path to second input file, if U and V are in separate files and
        need to be combined.

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    if infile2 == 'none':
        input = infile

    else: # if U and V separate, merge into UV file
        merge_uv(infile, infile2, infile[:-3] + "_merged.nc")
        input = infile[:-3] + "_merged.nc"

    input_basename = os.path.basename(input)

    # copy data into TRACK indat directory
    ## files need to be moved to TRACK directory for TRACK to find them
    tempname = "indat/temp_file.nc"
    os.system("cp '" + filled + "' " + str(Path.home()) + "/TRACK-1.5.2/" +
              tempname)
    os.system("rm '" + filled + "'")
    print("Data copied into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")

    data = cmip6_indat(tempname)

    if ("va" not in data.vars) or ("ua" not in data.vars):
        raise Exception("Invalid input variable type. Please input either " +
                            "a combined uv file or both ua and va from CMIP6.")

    print("Starting preprocessing.")

    # remove unnecessary variables
    extr = tempname[:-3] + "_extr.nc"
    if "time_bnds" in data.vars:
        ncks = "time_bnds"
        if "lat_bnds" in data.vars:
            ncks += ",lat_bnds,lon_bnds"
        os.system("ncks -C -O -x -v " + ncks + " " + tempname + " " + extr)
    elif "lat_bnds" in data.vars:
        os.system("ncks -C -O -x -v lat_bnds,lon_bnds " + tempname + " " + extr)
    else:
        extr = tempname

    gridtype = data.get_grid_type()
    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")
        gridcheck = tempname

    else:
    # regrid
        gridcheck = tempname[:-3] + "_gaussian.nc"
        regrid_cmip6(tempname, gridcheck)

    # fill missing values
    filled = gridcheck[:-3] + "_filled.nc"
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + gridcheck +
              " " + filled)
    print("Filled missing values, if any.")

    if gridtype != 'gridtype  = gaussian':
        os.system("rm " + tempname[:-3] + "_gaussian.nc")
    if extr != tempname:
        os.system("rm " + extr)

    # get data info
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)[0].split()

    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        cdo.selyear(year, input=filled, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        data = cmip6_indat("indat/"+year_file)
        ntime = data.get_timesteps()
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        vor850name = "vor850_temp.dat"
        calc_vorticity("./indat/"+year_file, vor850name, copy_file=False)
        year_file = vor850name
        c_input = year + "_" + hemisphere + "_" + "_vor850_" + \
                    input_basename[:-3]

        # spectral filtering
        if int(ny) >= 96: # T63
            fname = "T63filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/63/\" specfilt.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                        fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
                        " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                        "' -r=RUN_AT_ -s=RUNDATIN.VOR"

        else: # T42
            fname = "T42filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                        "/;s/TRUNC/42/\" specfilt.in > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                        fname + " -f=y" + year + \
                        " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
                        " -n=1,62," + \
                        str(nchunks) + " -o='" + outdir + \
                        "' -r=RUN_AT_ -s=RUNDATIN.VOR"

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

        print("Turning track output to netCDF...")
        if netcdf == True:
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "'/" + c_input + "/ff_trs_*")
            os.system("gunzip '" + outdir + "'/" + c_input + "/tr_trs_*")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_neg")

    os.system("rm " + tempname)
    os.chdir(cwd)
    return

def track_era5_mslp(input, outdirectory, NH=True, netcdf=True):
    """
    Run TRACK on ERA5 mean sea level pressure data.

    Parameters
    ----------

    input : string
        Path to .nc file containing ERA5 mslp data.

    outdirectory : string
        Path of directory to output tracks to.

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    input_basename = os.path.basename(input)
    data = Dataset(input, 'r')
    vars = [var for var in data.variables]
    nx = str(len(data.variables['lon'][:]))
    ny = str(len(data.variables['lat'][:]))

    if vars[-1] != "msl":
        raise Exception("Invalid input variable type. Please input ERA5 mslp file.")

    years = cdo.showyear(input=input)[0].split()

    # files need to be moved to TRACK directory for TRACK to find them
    # copy data into TRACK indat directory
    tempname = "temp_file.nc"
    os.system("cp '" + input + "' " + str(Path.home()) + "/TRACK-1.5.2/indat/" +
              tempname)
    print("Data copied into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")

    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        cdo.selyear(year, input="indat/"+tempname, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        ntime = int(len(data.variables['time'][:]))
        nchunks = ceil(ntime/62)
        c_input = year + "_" + hemisphere + "_" + input_basename[:-3]

        # spectral filtering
        # NOTE: NORTHERN HEMISPHERE; add SH option???
        fname = "T63filt_" + year + ".dat"
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                    "/;s/TRUNC/63/\" specfilt_nc.in > spec.test"
        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                    fname + " -f=y" + year + \
                    " -j=RUN_AT.in -k=initial.T63_" + hemisphere + \
                    " -n=1,62," + str(nchunks) + " -o='" + outdir + \
                    "' -r=RUN_AT_ -s=RUNDATIN.MSLP"

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

        print("Turning track output to netCDF...")
        if netcdf == True:
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "/" + c_input + "/ff_trs_neg.gz'")
            os.system("gunzip '" + outdir + "/" + c_input + "/tr_trs_neg.gz'")
            tr2nc_mslp(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_mslp(outdir + "/" + c_input + "/tr_trs_neg")

    os.system("rm indat/" + tempname)
    os.chdir(cwd)

    return

def track_era5_vor850(input, outdirectory, NH=True, netcdf=True):

    """
    Calculate 850 hPa vorticity from ERA5 horizontal wind velocity data
    and run TRACK.

    Parameters
    ----------

    input : string
        Path to .nc file containing combined ERA5 UV data

    outdirectory : string
        Path of directory to output tracks to

    NH : boolean, optional
        If true, tracks the Northern Hemisphere. If false, tracks Southern
        Hemisphere.

    netcdf : boolean, optional
        If true, converts TRACK output to netCDF format using TR2NC utility.

    """
    outdir = os.path.abspath(os.path.expanduser(outdirectory))
    input_basename = os.path.basename(input)
    data = Dataset(input, 'r')
    vars = [var for var in data.variables]
    nx = str(len(data.variables['lon'][:]))
    ny = str(len(data.variables['lat'][:]))

    if (vars[-1] != "var132") or (vars[-2] != "var131"):
        raise Exception("Invalid input variable type. Please input " +
                            "a UV file from ERA5.")

    years = cdo.showyear(input=input)[0].split()

    # copy data into TRACK indat directory
    ## files need to be moved to TRACK directory for TRACK to find them
    tempname = "temp_file.nc"
    os.system("cp '" + input + "' " + str(Path.home()) + "/TRACK-1.5.2/indat/" +
              tempname)
    print("Data copied into TRACK/indat directory.")

    # change working directory
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")

    if NH == True:
        hemisphere = "NH"
    else:
        hemisphere = "SH"

    # do tracking for one year at a time
    for year in years:
        print(year + "...")

        # select year from data
        year_file = 'tempyear.nc'
        cdo.selyear(year, input="indat/"+tempname, output="indat/"+year_file)

        # get number of timesteps and number of chunks for tracking
        ntime = int(len(data.variables['time'][:]))
        nchunks = ceil(ntime/62)

        # calculate vorticity from UV
        tempname = "vor850_temp.dat"
        calc_vorticity("./indat/"+year_file, tempname, copy_file=False,
                        cmip6=False)
        year_file = tempname
        c_input = year + "_" + hemisphere + "_" + "_vor850_" + \
                    input_basename[:-3]

        # spectral filtering, T42
        fname = "T42filt_" + year + ".dat"
        line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + \
                    "/;s/TRUNC/42/\" specfilt.in > spec.test"
        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
        # NH
        line_5 = "master -c=" + c_input + " -e=track.linux -d=now -i=" + \
                    fname + " -f=y" + year + \
                    " -j=RUN_AT.in -k=initial.T42_" + hemisphere + \
                    " -n=1,62," + \
                    str(nchunks) + " -o='" + outdir + \
                    "' -r=RUN_AT_ -s=RUNDATIN.VOR"

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

        print("Turning track output to netCDF...")
        if netcdf == True:
            # tr2nc - turn tracks into netCDF files
            os.system("gunzip '" + outdir + "'/" + c_input + "/ff_trs_*")
            os.system("gunzip '" + outdir + "'/" + c_input + "/tr_trs_*")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/ff_trs_neg")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_pos")
            tr2nc_vor(outdir + "/" + c_input + "/tr_trs_neg")

    os.chdir(cwd)

    return


#
# ========================
# POSTPROCESSING FUNCTIONS
# ========================
#

def tr2nc_mslp(input):
    """
    Convert MSLP tracks from ASCII to NetCDF using TR2NC utility

    Parameters
    ----------

    input : string
        Path to ASCII file containing tracks

    """
    fullpath = os.path.abspath(input)
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2/utils/bin")
    os.system("tr2nc '" + fullpath + "' s ../TR2NC/tr2nc_mslp.meta.elinor")
    os.chdir(cwd)
    return

def tr2nc_vor(input):
    """
    Convert vorticity tracks from ASCII to NetCDF using TR2NC utility

    Parameters
    ----------

    input : string
        Path to ASCII file containing tracks

    """
    fullpath = os.path.abspath(input)
    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2/utils/bin")
    os.system("tr2nc '" + fullpath + "' s ../TR2NC/tr2nc.meta.elinor")
    os.chdir(cwd)
    return

