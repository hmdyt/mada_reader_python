from typing import List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import struct
import sys
import bitstruct


@dataclass(frozen=True)
class EventHeader:
    trigger_counter: int
    clock_counter: int
    input_ch2_counter: int

    def col(self) -> str:
        return f"{self.trigger_counter}\t{self.clock_counter}\t{self.input_ch2_counter}"


def read_file(file_path: Path) -> List[bytes]:
    binaries = open(file_path, "rb").read().split(b"uPIC")
    return list(filter(lambda x: x != b'', binaries))


def parse_headers(events: List[bytes]) -> List[EventHeader]:
    """ 
    固定長部分のcounterたちだけをparseする
    """
    return list(map(lambda e: parse_header(e)[0], events))


def parse_header(event: bytes) -> Optional[Tuple[EventHeader, bytes]]:
    """
    固定長部分のcounterたちだけをparseする
    """
    try:
        _uPIC = struct.unpack("4c", event[0:4])
        trigger_counter, clock_counter, input_ch2_counter = struct.unpack("!III", event[4:16])
        ret_event = EventHeader(trigger_counter, clock_counter, input_ch2_counter)
        return ret_event, event[16:]
    except struct.error as e:
        print(e, file=sys.stderr)
        return None


@dataclass
class FlushADC:
    ch0: List[int] = field(default_factory=list)
    ch1: List[int] = field(default_factory=list)
    ch2: List[int] = field(default_factory=list)
    ch3: List[int] = field(default_factory=list)

    def __iter__(self):
        self.__current_ch = 0
        return self

    def __next__(self) -> List[int]:
        self.__current_ch += 1

        if self.__current_ch == 1:
            return self.ch0
        elif self.__current_ch == 2:
            return self.ch1
        elif self.__current_ch == 3:
            return self.ch2
        elif self.__current_ch == 4:
            return self.ch3
        else:
            raise StopIteration


def parse_flush_adc(
    event: bytes,
    flush_adc_clock_depth: int = 1024
) -> Optional[Tuple[FlushADC, bytes]]:
    flush_adc = FlushADC()
    event_reading_bytes = 2 * 4 * flush_adc_clock_depth

    try:
        fadc_unpacked = bitstruct.unpack(
            "u4u2u10"*4*flush_adc_clock_depth,
            event[0:event_reading_bytes]
        )
    except bitstruct.Error as e:
        print(e, sys.stderr)
        return None

    for i_iter in range(0, len(fadc_unpacked), 3):
        # channel_id = fadc_unpacked[i_iter]
        # adc_value = fadc_unpacked[i_iter + 2]
        channel_id, padding, adc_value = fadc_unpacked[i_iter:i_iter+3]

        if channel_id == 4:
            flush_adc.ch0.append(adc_value)
        elif channel_id == 5:
            flush_adc.ch1.append(adc_value)
        elif channel_id == 6:
            flush_adc.ch2.append(adc_value)
        elif channel_id == 7:
            flush_adc.ch3.append(adc_value)
        else:
            # raise ValueError(
            #     f"FADC parse Error: i_iter: {i_iter}, channel_id: {channel_id}, padding: {padding}, adc_value: {adc_value}"
            # )
            break

    return flush_adc, event[event_reading_bytes:]


@dataclass
class Event:
    header: EventHeader
    fadc: FlushADC


def parse_events(bytes_list: List[bytes]) -> List[Event]:
    events: List[Event] = []
    for b in bytes_list:
        ret_parse_header = parse_header(b)
        if not ret_parse_header:
            continue
        header, remain_b = ret_parse_header

        ret_parse_flush_adc = parse_flush_adc(remain_b)
        if not ret_parse_flush_adc:
            continue
        fadc, remain_b = ret_parse_flush_adc

        events.append(Event(header, fadc))

    return events


def parse_from_mada_file(mada_file_path: Path) -> List[Event]:
    return parse_events(read_file(mada_file_path))
