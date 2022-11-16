from array import array
import ROOT as r


def pyroot_func(func):
    def _wrapper(*args, **kwargs):
        r.gROOT.SetBatch()
        func(*args, **kwargs)
    return _wrapper


def list_to_array(l: list) -> array:
    t = type(l[0])
    if t == int:
        return array("i", l)
    elif t == float:
        return array("d", l)
    else:
        raise TypeError("unsupported type {t}")


@pyroot_func
def TPGraph(n: int, x: list, y: list) -> r.TGraph:
    xx = list_to_array(x)
    yy = list_to_array(y)
    return r.TGraph(n, xx, yy)
