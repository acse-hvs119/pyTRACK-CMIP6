from pytest import fixture


@fixture(scope='module')
def track_wrapper()
    """Perform the module import"""
    import track_wrapper
    return track_wrapper


# TBC


def test_import(track_wrapper):
    """Check package imports"""
    assert track_wrapper


