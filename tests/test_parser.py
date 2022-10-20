from mada_reader import parser

MADAFILE = "tests/assets/GBKB-13_0004.mada"
events = parser.read_file(MADAFILE)


def test_parse_event():
    event = events[123]
    header, _ = parser.parse_header(event)
    assert header == parser.EventHeader(
        trigger_counter=123,
        clock_counter=971495,
        input_ch2_counter=0
    )


def test_parse_events():
    parsed_events = parser.parse_headers(events)
    assert len(parsed_events) == 183
    assert parsed_events[0] == parser.EventHeader(
        trigger_counter=0,
        clock_counter=0,
        input_ch2_counter=0
    )
    assert parsed_events[123] == parser.EventHeader(
        trigger_counter=123,
        clock_counter=971495,
        input_ch2_counter=0
    )
