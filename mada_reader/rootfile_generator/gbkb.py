from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Tuple
import itertools

import numpy as np
import ROOT as r
from mada_reader.parser import Event, FlushADC, parse_from_mada_file
from mada_reader.pyroot_lib.util import pyroot_func
from nptyping import NDArray


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


def calc_fadc_peak2peak(fadc: FlushADC) -> Optional[List[float]]:
    """
    1イベントのFADCのp2pを4chぶん取得する
    [shape (4,)]
    """
    ret = [0., 0., 0., 0.]
    for i, fadc_ch_i in enumerate(fadc):
        if fadc_ch_i:
            ret[i] = float(abs(max(fadc_ch_i) - min(fadc_ch_i)))
        else:
            return None
    return ret


@dataclass
class FlushADCAmplitude:
    attr: Literal["min", "max"]
    value: Tuple[float, float, float, float]


def calc_fadc_amplitudes(
    fadc: FlushADC,
    baseline_correction_range: Tuple[int, int] = (600, 1000)
) -> Optional[Tuple[FlushADCAmplitude, FlushADCAmplitude]]:
    """
    1イベントのFADCのmax, minを4chぶん取得する
    baselineも引く
    [ch0_min, ch1_min, ch2_min, ch3_min], [ch0_max, ch1_max, ch2_max, ch3_max]
    """
    if len(fadc.ch0) != 1024:
        return None

    ret_min = [None, None, None, None]
    ret_max = [None, None, None, None]
    range_min, range_max = baseline_correction_range

    baselines = [
        np.array(fadc_ch_i[range_min:range_max]).mean()
        for fadc_ch_i in fadc
    ]

    for i, fadc_ch_i in enumerate(fadc):
        if fadc_ch_i:
            ret_min[i] = min(fadc_ch_i) - baselines[i]
            ret_max[i] = max(fadc_ch_i) - baselines[i]
        else:
            return None
    return FlushADCAmplitude("min", ret_min), FlushADCAmplitude("max", ret_max)


def get_fadc_peak2peak_from_mada_file(target_mada_path: Path) -> NDArray:
    """
    .mada 1ファイル分の p2p を np.array で取得する 
    [shape (n_events, 4)]
    """
    events = parse_from_mada_file(target_mada_path)
    fadc_list = list(map(lambda e: e.fadc, events))
    ret = list(map(calc_fadc_peak2peak, fadc_list))
    ret = list(filter(lambda x: x != None, ret))
    return np.array(ret)


def get_fadc_amplitude_from_mada_file(target_mada_path: Path) -> Tuple[List[FlushADCAmplitude], List[FlushADCAmplitude]]:
    """
    .mada 1ファイル分の amplitude を取得する 
    [min_ampのリスト], [max_ampのリスト]
    """
    events = parse_from_mada_file(target_mada_path)
    ret_amp_mins: List[FlushADCAmplitude] = []
    ret_amp_maxs: List[FlushADCAmplitude] = []
    for event in events:
        ret_calc_fadc_amplitudes = calc_fadc_amplitudes(event.fadc, (600, 1000))
        if ret_calc_fadc_amplitudes != None:
            actual_calc_fadc_amplitudes: Tuple[FlushADCAmplitude, FlushADCAmplitude] = ret_calc_fadc_amplitudes
            amp_min, amp_max = actual_calc_fadc_amplitudes
            ret_amp_mins.append(amp_min)
            ret_amp_maxs.append(amp_max)

    return ret_amp_mins, ret_amp_maxs


def average_flush_adc_amplitudes(input_list: List[List[FlushADCAmplitude]]) -> FlushADCAmplitude:
    """
    madaファイルごとにイベントの数だけFlushADCAmplitudeがある
    それらをflattenした後にaverageするもの
    """
    flattend_amps: List[FlushADCAmplitude] = list(itertools.chain.from_iterable(input_list))
    if len(flattend_amps) == 0:
        raise ValueError("input is empty")
    min_or_max = flattend_amps[0].attr
    n_flattend_amps = len(flattend_amps)
    accumlates = [0, 0, 0, 0]
    for amp in flattend_amps:
        for ch in range(4):
            accumlates[ch] += amp.value[ch]
    return FlushADCAmplitude(min_or_max, tuple(map(lambda x: x/n_flattend_amps, accumlates)))
