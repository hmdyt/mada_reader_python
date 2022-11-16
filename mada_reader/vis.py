import ROOT as r

from mada_reader.parser import FlushADC
from mada_reader.pyroot_lib import util


@util.pyroot_func
def vis_flush_adc(
    flush_adc: FlushADC,
    save_file_name="flush_adc.png"
):
    """
    任意の1イベントのFADC波形をpngに出力する。
    任意のイベントを選ぶためにファイル内の
    すべてのイベントをdumpしているのでめっちゃ遅い。
    """
    fadc_clock_depth = len(flush_adc.ch0)
    graphs = [
        util.TPGraph(fadc_clock_depth, list(range(fadc_clock_depth)), fadc)
        for fadc in flush_adc
    ]

    canvas = r.TCanvas("canvas_fadc", "canvas_fadc", 1600, 1200)
    canvas.Divide(2, 2)
    for i in range(4):
        canvas.cd(i + 1)
        graphs[i].SetTitle(f"analog sum ch{i}")
        graphs[i].Draw("AL")
    canvas.SaveAs(save_file_name)
