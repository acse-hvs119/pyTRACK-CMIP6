import os
import numpy as np
from cdo import *
from netCDF4 import Dataset
from pathlib import Path

cdo = Cdo()

#other imports

__all__ = []

class cmip6_indat(object):
    def __init__(self, filename):
        self.filename = filename
        self.data = Dataset(filename, 'r')
        self.vars = [var for var in self.data.variables]
    def get_nx_ny(self):
        return str(len(self.data.variables['lon'][:])), str(len(self.data.variables['lat'][:]))
        
    def get_grid_type(self):
        return cdo.griddes(input=self.filename)[3]
    
    def get_variable_type(self):
        return self.vars[-1]

def merge_uv(u_file, v_file):
    """
    Only relevant for cmip6 because ERA5 already has them together
    """
    outfile = "~/TRACK-1.5.2/indat/uv" + u_file[2:]
    cdo.merge(input=" ".join((u_file, v_file)), output=outfile)
    return

def regrid_cmip6(input, outfile):
    """
    Preprocessing: regrid
    
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
        elif int(ny) <= 160:
            cdo.remapcon("n80", input=input, output=outfile)
        else:
            cdo.remapcon("n120", input=input, output=outfile)

    return

def calc_vorticity(uv_file, outfile):
    """
    Docs
    == CODE DONE ==
    """
    # gather information about data
    uv = cmip6_indat(uv_file)
    nx, ny = uv.get_nx_ny()
    year = cdo.showyear(input=uv_file)[0]
    u_name = uv.vars[-2]
    v_name = uv.vars[-1]
    
    # copy input files to necessary directories for TRACK to find
    tempname = "temp_file.nc"
    os.system("cp " + uv_file + " " + str(Path.home()) + "/TRACK-1.5.2/indat/" + tempname)
    #os.system("cp indat/calcvor.in " + str(Path.home()) + "/TRACK-1.5.2/calcvor.in")

    # generate vorticity calculation input file and calculate vorticity using TRACK
    line_1 = "sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" + nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile + "/\" calcvor.in > calcvor.test"
    line_2 = "bin/track.linux -i " + tempname + " -f y" + year + " < calcvor.test"
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")
    os.system(line_1)
    os.system(line_2)

    return

def edit_rundatin():
    """
    """
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
    return

def copy_files(data='none'):
    """
    """
    os.system("cp trackdir/* " + str(Path.home()) + "/TRACK-1.5.2/")
    
    os.system("cp indat/RUNDATIN.* " + str(Path.home()) + "/TRACK-1.5.2/indat")

    os.system("cp data/* " + str(Path.home()) + "/TRACK-1.5.2/data")
    return


def run_track(input, outdir):
    """
    
    OR MAYBE THIS IS JUST SPECFILT??
    
    TODO
    also ask if we should have higher resolutions for spectral filtering
    INCLUDE SPECFILT RESOLUTION OPTION!!!
    
    SPLIT INTO YEARS AND RUN EACH FULL YEAR
    ---- ask how to select seasons
    """
    filled = input[:-3] + "_filled.nc"
    os.system("ncatted -a _FillValue,,d,, -a missing_value,,d,, " + input + " " + filled)
    print("Filled missing values.")
    
    data = cmip6_indat(filled)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=filled)

    # files need to be moved to TRACK directory for TRACK to find them
    # copy data into TRACK indat directory
    tempname = "temp_file.nc"
    os.system("cp " + filled + " " + str(Path.home()) + "/TRACK-1.5.2/indat/" + tempname)

    # copy spectral filtering input files into TRACK directory
    #os.system("cp indat/specfilt.in " + str(Path.home()) + "/TRACK-1.5.2/specfilt.in")
    #os.system("cp indat/specfilt_nc.in " + str(Path.home()) + "/TRACK-1.5.2/specfilt_nc.in")
    #os.system("cp indat/RUNDATIN.* ")
    copy_files()

    print("Inputs copied to TRACK directory.")

    # MSLP
    if data.get_variable_type() == "psl":
        specfilt = "specfilt_nc.in"
        var = "MSLP"

    # UV
    elif data.get_variable_type() == 'va':
        specfilt = "specfilt.in"
        var = "VOR"

    # other
    else:
        print("Invalid variable type: please use CMIP6 mslp or uv-wind.")
        return

    cwd = os.getcwd()
    os.chdir(str(Path.home()) + "/TRACK-1.5.2") # maybeTODO: find some way to get TRACK directory for future versions

    # do tracking for one year at a time
    for year in years:
        print(year + "...")
        year_file = 'tempyear.nc'
        cdo.selyear(year, input="indat/"+tempname, output="indat/"+year_file)

        # calculate vorticity if UV file
        if data.get_variable_type() == 'va':
            #os.chdir(cwd)
            tempname = "vor850_temp.dat"
            calc_vorticity("./indat/"+year_file, tempname)
            year_file = tempname
        
        # spectral filtering
        # NOTE: NORTHERN HEMISPHERE; add SH option???
        if int(ny) >= 96: # T63
            fname = "T63filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + "/;s/TRUNC/63/\" " + specfilt + " > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + year + "_" + input[:-3] + " -e=track.linux -d=now -i=" + fname + " -f=y" + year + " -j=RUN_AT.in -k=initial.T63_NH -n=1,62,6 -o=" + outdir + " -r=RUN_AT_ -s=RUNDATIN." + var

        else: # T42
            fname = "T42filt_" + year + ".dat"
            line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + "/;s/TRUNC/42/\" " + specfilt + " > spec.test"
            line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" + fname
            # NH
            line_5 = "master -c=" + year + "_" + input[:-3] + " -e=track.linux -d=now -i=" + fname + " -f=y" + year + " -j=RUN_AT.in -k=initial.T42_NH -n=1,62,6 -o=" + outdir + " -r=RUN_AT_ -s=RUNDATIN." + var

        line_2 = "bin/track.linux -i " + year_file + " -f y" + year + " < spec.test"
        line_4 = "rm outdat/specfil.y" + year + "_band000"

        # tracking
        os.environ["CC"] = "gcc"
        os.environ["FC"] = "gfortran"
        os.environ["ARFLAGS"] = ""
        os.environ["PATH"] += ":." 
        
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

# I SHOULD SPLIT INTO SEPARATE VOR AND MSLP FUNCTIONS!!! IM SO FUMB