from array import array
import ROOT as r


def pyroot_func(func):
    def _wrapper(*args, **kwargs):
        r.gROOT.SetBatch()
        func(*args, **kwargs)
    return _wrapper


@pyroot_func
def TPGraph(n: int, x: list, y: list) -> r.TGraph:
    xx = array('d', x)
    yy = array('d', y)
    return r.TGraph(n, xx, yy)
