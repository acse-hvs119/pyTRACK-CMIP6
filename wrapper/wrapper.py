import numpy as np
import cdo
from netCDF4 import Dataset

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

def calc_vorticity(uv_file, outfile):
    """
    TODO
    """
    uv = Dataset(uv_file, 'r')
    vars = [var for var in uv.variables]
    
    u_var = vars #TBD
    # TODO
    
    return

def regrid_cmip6(input, outfile):
    """
    Docstrings
    
    """
    data = cmip6_indat(input)

    gridtype = data.get_grid_type()

    # check if regridding is needed, do nothing if already gaussian
    if gridtype == 'gridtype  = gaussian':
        print("No regridding needed.")

    # check for resolution and regrid
    else:
        nx, ny = data.get_nx_ny()
        #outfile = input[:-3] + "_gaussian.nc"
        if ny <= 64:
            # NOTE: ask about bilinear vs conservative vs etc. remapping
            cdo.remapbil("n32", input=input, output=outfile)
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

def run_track(input):
    # spectral filtering
    
    # tracking

    return
    