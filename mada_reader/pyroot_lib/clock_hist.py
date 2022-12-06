import ROOT as r
from pathlib import Path
from copy import copy


def clock_hist(root_file_path: str) -> r.TH2D:
    r.gROOT.SetBatch()
    root_file = r.TFile.Open(root_file_path)
    tree = root_file.tree01
    clocks = [e.clock_counter for e in tree]
    clocks_min = min(clocks)
    clocks_max = max(clocks)
    clocks_dif = clocks_max - clocks_min

    hist = r.TH1D(root_file_path, f"{root_file_path};clock;count", clocks_dif, clocks_min, clocks_max)
    for c in clocks:
        hist.Fill(c)

    return copy(hist)


def save_clock_hist_png(hist: r.TH1D, save_path: Path):
    c = r.TCanvas("", "", 1500, 800)
    hist.Draw()
    c.SaveAs(str(save_path))
