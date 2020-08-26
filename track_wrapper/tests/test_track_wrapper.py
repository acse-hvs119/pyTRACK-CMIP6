from pytest import fixture


@fixture(scope='module')
def track_wrapper()
    """Perform the module import"""
    import track_wrapper
    return track_wrapper

def test_import(track_wrapper):
    """Check package imports"""
    assert track_wrapper

def test_calc_vorticity(track_wrapper):
    """Test vorticity calculation function."""
    track_wrapper.calc_vorticity('data/uv_test_filled.nc', 'pytest_vor.dat')
    assert os.path.isfile(str(Path.home()) + \
                            "/TRACK-1.5.2/indat/pytest_vor.dat")
    os.system("rm " + str(Path.home()) + "/TRACK-1.5.2/indat/pytest_vor.dat")

def test_track_uv_vor850(track_wrapper):
    """Test vorticity tracking function.
    Checks if an output is produced, i.e. if TRACK was successfully run."""
    track_wrapper.track_uv_vor850('data/uv_test.nc', '~')
    assert os.path.isdir(str(Path.home()) + "/2010_vor850_uv_test")
    os.system("rm -R " + str(Path.home()) + "/2010_vor850_uv_test")

def test_track_mslp(track_wrapper):
    """Test MSLP tracking function.
    Checks if an output is produced, i.e. if TRACK was successfully run."""
    track_wrapper.track_mslp('data/psl_test.nc', '~')
    assert os.path.isdir(str(Path.home()) + "/2010_psl_test")
    os.system("rm -R " + str(Path.home()) + "/2010_psl_test")

