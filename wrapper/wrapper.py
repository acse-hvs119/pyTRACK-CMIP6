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
        if ny <= 64:
            # NOTE: ask about bilinear vs conservative vs etc. remapping
            cdo.remapcon("n32", input=input, output=outfile)
        # T63
        elif ny <= 96:
            cdo.remapcon("n48", input=input, output=outfile)
        # T80
        elif ny <= 128:
            cdo.remapbil("n64", input=input, output=outfile)
        # T106?
        elif ny <= 160:
            cdo.remapbil("n80", input=input, output=outfile)
        else:
            cdo.remapbil("n120", input=input, output=outfile)

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
    tempname = "uv_file.nc"
    os.system("cp " + uv_file + " " + str(Path.home()) + "/TRACK-1.5.2/indat/" + tempname)
    os.system("cp indat/calcvor.in " + str(Path.home()) + "/TRACK-1.5.2/calcvor.in")

    # generate vorticity calculation input file and calculate vorticity using TRACK
    line_1 = "sed -e \"s/VAR1/"+ u_name + "/;s/VAR2/" + v_name + "/;s/NX/" + nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile + "/\" calcvor.in > calcvor.test"
    line_2 = "bin/track.linux -i " + tempname + " -f y" + year + " < calcvor.test"
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")
    os.system(line_1)
    os.system(line_2)

    return

def run_track(input):
    """
    TODO
    also ask if we should have higher resolutions for spectral filtering
    INCLUDE SPECFILT RESOLUTION OPTION!!!
    
    SPLIT INTO YEARS AND RUN EACH FULL YEAR
    ---- ask how to select seasons
    """
    data = cmip6_indat(input)
    nx, ny = data.get_nx_ny()
    years = cdo.showyear(input=input)
    
    input_path = os.path.abspath(input)
    ### note: files from wrapper directory, not TRACK directory
    specfilt = os.path.abspath('indat/specfilt.in')
    specfilt_nc = os.path.abspath('indat/specfilt_nc.in')

    os.chdir(str(Path.home()) + "/TRACK-1.5.2") # maybeTODO: find some way to get TRACK directory for future versions

    for year in years:
        year_file = 'temp_'+year+'.nc'
        cdo.selyear(year, input=input_path, output=year_file)

        # spectral filtering: check if mslp or uv
        ## mslp
        if data.get_variable_type() == "psl":
            if ny >= 96: # T63
                line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + "/;s/TRUNC/63/\" " + specfilt_nc + " > spec.test"
            else: # T42
                line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + "/;s/TRUNC/42/\" " + specfilt_nc + " > spec.test"
            ######## fix this full path thing, need to be in /indat/#########
            line_2 = "bin/track.linux -i " + full_path + " -f y" + year + " < spec.test"
        ## uv
        elif data.get_variable_type() == 'va':
            vor_file = "indat/vor850" + full_path[2:]
            calc_vorticity(full_path, vor_file)
            if ny >= 96: # T63
                line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + "/;s/TRUNC/63/\" " + specfilt + " > spec.test"
            else: # T42
                line_1 = "sed -e \"s/NX/" + nx + "/;s/NY/" + ny + "/;s/TRUNC/42/\" " + specfilt + " > spec.test"
            line_2 = "bin/track.linux -i " + vor_file + " -f y" + year + " < spec.test"
        ## other variable
        else:
            print("Invalid variable type: please use cmip6 mslp or uv-wind.")
            break

        line_3 = "mv outdat/specfil.y" + year + "_band001 indat/" #incomplete#######



        # tracking
        os.system()
        
        
        os.system("rm "+year_file)

    return

def postprocess(input):
    
    return
    