from pathlib import Path
from typing import List
from copy import copy

import ROOT as r
import numpy as np
import mada_reader.models.mada_config as config
from mada_reader.pyroot_lib.util import pyroot_func
from mada_reader.parser import Event, parse_from_mada_file


def draw_waveform_hist2d(events: List[Event]) -> List[r.TH2D]:
    hists: List[r.TH2D] = [
        r.TH2D(
            f"wf_ch{ch}", f"wf_ch{ch}",
            1024, 0, 1023,  # x -> clock
            2048, 0, 2047  # y -> adc value
        )
        for ch in range(4)
    ]
    for event in events:
        for ch, fadc in enumerate(event.fadc):
            for clock, adc_value in enumerate(fadc):
                hists[ch].Fill(clock, adc_value)
    return [copy(h) for h in hists]


@pyroot_func
def mada_to_root(target_mada_path: Path) -> None:
    TREE_NAME = "tree01"
    events = parse_from_mada_file(target_mada_path)
    # /hoge/fuga/piyo.mada -> hoge/fuga/piyo.root
    tfile_path = target_mada_path.absolute().parent / target_mada_path.name.replace(".mada", ".root")
    tfile = r.TFile(str(tfile_path), "recreate")

    fadc = np.ndarray((4, 1024), dtype=np.int32)
    trigger_counter = np.ndarray(1, dtype=np.int32)
    clock_counter = np.ndarray(1, dtype=np.int32)
    input_ch2_counter = np.ndarray(1, dtype=np.int32)

    tree = r.TTree(TREE_NAME, TREE_NAME)
    tree.Branch("fadc", fadc, "fadc[4][1024]/I")
    tree.Branch("trigger_counter", trigger_counter, "trigger_counter/I")
    tree.Branch("clock_counter", clock_counter, "clock_counter/I")
    tree.Branch("input_ch2_counter", input_ch2_counter, "input_ch2_counter/I")

    for event in events:
        trigger_counter[0] = event.header.trigger_counter
        clock_counter[0] = event.header.clock_counter
        input_ch2_counter[0] = event.header.input_ch2_counter
        for i, fadc_ch_i in enumerate(event.fadc):
            for j, v in enumerate(fadc_ch_i):
                fadc[i][j] = v
        tree.Fill()

    tree.Write()

    hists = draw_waveform_hist2d(events)
    for h in hists:
        h.Write()
