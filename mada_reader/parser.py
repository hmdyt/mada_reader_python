from typing import List, Tuple
from dataclasses import dataclass, field
import struct
import bitstruct


@dataclass(frozen=True)
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


def parse_header(event: bytes) -> Tuple[EventHeader, bytes]:
    """
    固定長部分のcounterたちだけをparseする
    """
    _uPIC = struct.unpack("4c", event[0:4])
    trigger_counter, clock_counter, input_ch2_counter = struct.unpack("!III", event[4:16])
    ret_event = EventHeader(trigger_counter, clock_counter, input_ch2_counter)
    return ret_event, event[16:]


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
) -> Tuple[FlushADC, bytes]:
    flush_adc = FlushADC()
    event_reading_bytes = 2 * 4 * flush_adc_clock_depth

    fadc_unpacked = bitstruct.unpack(
        "u4u2u10"*4*flush_adc_clock_depth,
        event[0:event_reading_bytes]
    )

    for i_iter in range(0, len(fadc_unpacked), 3):
        channel_id = fadc_unpacked[i_iter]
        adc_value = fadc_unpacked[i_iter + 2]
        if channel_id == 4:
            flush_adc.ch0.append(adc_value)
        elif channel_id == 5:
            flush_adc.ch1.append(adc_value)
        elif channel_id == 6:
            flush_adc.ch2.append(adc_value)
        elif channel_id == 7:
            flush_adc.ch3.append(adc_value)
        else:
            raise ValueError(
                f"FADC parse Error: i_iter: {i_iter}, channel_id: {channel_id}, adc_value: {adc_value}"
            )

    return flush_adc, event[event_reading_bytes:]


@dataclass
class Event:
    header: EventHeader
    fadc: FlushADC


def parse_events(bytes_list: List[bytes]) -> List[Event]:
    events: List[Event] = []
    for b in bytes_list:
        header, remain_b = parse_header(b)
        fadc, remain_b = parse_flush_adc(remain_b)
        events.append(Event(header, fadc))
    return events
