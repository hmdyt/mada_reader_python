from mada_reader import parser

MADAFILE = "tests/assets/GBKB-13_0000.mada"
events = parser.read_file(MADAFILE)


def test_parse_event():
    event = events[123]
    header, event = parser.parse_header(event)
    assert header == parser.EventHeader(
        trigger_counter=123,
        clock_counter=1177695,
        input_ch2_counter=0
    )
    fadc, _ = parser.parse_flush_adc(event)
    assert len(fadc.ch0) == 1024
    assert fadc.ch1[33] == 545


def test_parse_from_mada_file():
    events = parser.parse_from_mada_file(MADAFILE)
    event = events[12]
    assert event.header.trigger_counter == 12
    assert len(event.fadc.ch0) == 1024
    assert len(event.fadc.ch1) == 1024
    assert len(event.fadc.ch2) == 1024
    assert len(event.fadc.ch3) == 1024


def test_parse_headers():
    parsed_events = parser.parse_headers(events)
    assert len(parsed_events) == 183
    assert parsed_events[1] == parser.EventHeader(
        trigger_counter=1,
        clock_counter=35356,
        input_ch2_counter=0
    )
    assert parsed_events[123] == parser.EventHeader(
        trigger_counter=123,
        clock_counter=1177695,
        input_ch2_counter=0
    )
