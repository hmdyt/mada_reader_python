import json
from typing import Literal, List
from pathlib import Path
from pydantic import Field
from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class Connection:
    polarity: Literal["anode", "cathode"]
    position: int = Field(..., ge=0, le=2)


@dataclass(frozen=True)
class GigaIwaki:
    id_: Literal["00", "01", "03", "10", "11", "13"]
    is_active: bool
    connection: Connection
    pitch: int
    ip_address: str
    dac_file: Path
    voltage_threshold_dac: int = Field(..., ge=0, lt=16384)  # 14 bit

    @property
    def name(self) -> str:
        return f"GBKB-{self.id_}"


@dataclass(frozen=True)
class Adalm:
    id_: Literal["0", "1", "2"]
    is_active: bool
    uri: str
    serial_number: str
    clock_d: str

    def name(self) -> str:
        return f"MADALM_{self.id_}"


@dataclass(frozen=True)
class MadaConfig:
    giga_iwaki: List[GigaIwaki]
    adalm: List[Adalm]

    @property
    def available_boards(self) -> List[str]:
        names = []
        for iwaki in self.giga_iwaki:
            if iwaki.is_active:
                names.append(iwaki.name)
        return names


def parse(json_string: str) -> MadaConfig:
    """
    既存の MADA_config.json を MadaConfig class に変換する
    """
    mada_config_dict: dict = json.loads(json_string)

    giga_iwaki_list = []
    for board_name, board_attr in mada_config_dict["gigaIwaki"].items():

        board_attr_connection = board_attr["connection"]
        board_attr_connection_position = board_attr_connection[-1]
        if board_attr_connection[0] == "a":
            connection = Connection("anode", board_attr_connection_position)
        elif board_attr_connection[0] == "c":
            connection = Connection("cathode", board_attr_connection_position)

        giga_iwaki_list.append(GigaIwaki(
            id_=board_name[-2:],
            is_active=board_attr["active"],
            pitch=board_attr["pitch"],
            ip_address=board_attr["IP"],
            dac_file=board_attr["DACfile"],
            voltage_threshold_dac=board_attr["Vth"],
            connection=connection
        ))

    adalm_list = []
    for adalm_name, adalm_attr in mada_config_dict["ADALM"].items():
        adalm_list.append(Adalm(
            id_=adalm_name[-1],
            is_active=adalm_attr["active"],
            uri=adalm_attr["URI"],
            serial_number=adalm_attr["S/N"],
            clock_d=adalm_attr["Clock_d"]
        ))

    return MadaConfig(giga_iwaki_list, adalm_list)
