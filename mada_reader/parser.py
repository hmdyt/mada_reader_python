from typing import List
from dataclasses import dataclass
import struct


@dataclass
class EventHeader:
    trigger_counter: int
    clock_counter: int
    input_ch2_counter: int

    def col(self) -> str:
        return f"{self.trigger_counter}\t{self.clock_counter}\t{self.input_ch2_counter}"


def read_file(file_path: str) -> List[bytes]:
    return open(file_path, "rb").read().split(b"uPIC")


def parse_headers(events: List[bytes]) -> List[EventHeader]:
    """ 
    固定長部分のcounterたちだけをparseする
    """
    return list(map(lambda e: parse_header(e)[0], events))


def parse_header(event: bytes) -> EventHeader:
    """
    固定長部分のcounterたちだけをparseする
    """
    _uPIC = struct.unpack("4c", event[0:4])
    trigger_counter, clock_counter, input_ch2_counter = struct.unpack("!III", event[4:16])
    ret_event = EventHeader(trigger_counter, clock_counter, input_ch2_counter)
    return ret_event, event[16:]
