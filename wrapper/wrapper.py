import os
import numpy as np
import cdo
from netCDF4 import Dataset
from pathlib import Path

cdo = Cdo()

#other imports

__all__ = []

class cmip6_indat(object):
    def __init__(self, filename):
        self.data = Dataset(filename, 'r')
        self.vars = [var for var in self.data.variables]
    def get_nx_ny(self):
        return len(data.variables['lon'][:]), len(data.variables['lat'][:])
        
    def get_grid_type(self):
        return cdo.griddes(input=filename)[3]
    
    def get_variable_type(self):
        return self.vars[-1]

def merge_uv(u_file, v_file):
    """
    Only relevant for cmip6 because ERA5 already has them together
    """
    outfile = "uv" + u_file[2:]
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
        
        # regrid to T42
        if ny <= 64:
            # NOTE: ask about bilinear vs conservative vs etc. remapping
            cdo.remapbil("n32", input=input, output=outfile)
        # T63
        elif ny <= 96:
            cdo.remapbil("n48", input=input, output=outfile)
        elif ny <= 128:
            cdo.remapbil("n64", input=input, output=outfile)
        elif ny <= 160:
            cdo.remapbil("n80", input=input, output=outfile)
        else:
            cdo.remapbil("n120", input=input, output=outfile)

    #if variables[-1] == 'psl':
    #    psl = data.variables['psl'][:]
    # else if variables[-1]
    
    return

def calc_vorticity(uv_file, outfile):
    """
    TODO: auto merge ua and va files?
    ASSUMES UV FILE IS IN TRACK/indat
    """
    uv = cmip6_indat(uv_file)
    nx, ny = uv.get_nx_ny()
    year = "dummy" #TODO
    
    line_1 = "sed -e \"s/VAR1/ua/;s/VAR2/va/;s/NX/" + nx + "/;s/NY/" + ny + "/;s/LEV/85000/;s/VOR/" + outfile + "/\" calcvor.in > calcvor.test"
    line_2 = "bin/track.linux -i " + uv_file + " -f y" + year + " < calcvor.test"
    
    os.chdir(str(Path.home()) + "/TRACK-1.5.2")
    os.system(line_1)
    os.system(line_2)
    
    return

def run_track(input):
    """
    
    """
    data = cmip6_indat(input)
    
    # spectral filtering
    os.chdir(str(Path.home()) + "/TRACK-1.5.2") # maybeTODO: find some way to get TRACK directory for future versions
    
    # check if mslp or uv
    if data.get_variable_type() == "psl":
        pass
    
    else:
        vor_file = "vor850" + input[2:]
        calc_vorticity(input, vor_file)
    
    
    # tracking
    os.system()

    return

def postprocess(input):
    return
    
    
    