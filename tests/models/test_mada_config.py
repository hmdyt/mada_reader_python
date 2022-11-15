from mada_reader.models.mada_config import Connection, GigaIwaki, Adalm, parse

JSON_STRING = """
    {
        "general": {},
        "gigaIwaki": {
            "GBKB-00": {
                "active": 1,
                "connection": "a1-0",
                "pitch": "800",
                "IP": "192.168.100.16",
                "Vth": 15000,
                "DACfile": "/path/to/dac00"
            },
            "GBKB-01": {
                "active": 0,
                "connection": "a1-1",
                "pitch": "800",
                "IP": "192.168.100.17",
                "Vth": 15000,
                "DACfile": "/path/to/dac01"
            },
            "GBKB-13": {
                "active": 0,
                "connection": "c1-2",
                "pitch": "800",
                "IP": "192.168.100.27",
                "Vth": 0,
                "DACfile": "/path/to/dac13"
            }
        },
    "ADALM": {
        "MADALM_0": {
            "active": 1,
            "URI": "usb:1.6.5",
            "S/N": "sn1",
            "Clock_d": 100000000.0
        },
        "MADALM_1": {
            "active": 0,
            "URI": "usb:1.7.5",
            "S/N": "sn2",
            "Clock_d": 100000000.0
        }
    }
}
"""


def test_parse():
    ret = parse(JSON_STRING)
    assert set(ret.giga_iwaki) == set([
        GigaIwaki(
            id="00",
            is_active=True,
            connection=Connection("anode", 0),
            pitch=800,
            ip_address="192.168.100.16",
            dac_file="/path/to/dac00",
            voltage_threshold_dac=15000
        ),
        GigaIwaki(
            id="01",
            is_active=False,
            connection=Connection("anode", 1),
            pitch=800,
            ip_address="192.168.100.17",
            dac_file="/path/to/dac01",
            voltage_threshold_dac=15000
        ),
        GigaIwaki(
            id="13",
            is_active=False,
            connection=Connection("cathode", 2),
            pitch=800,
            ip_address="192.168.100.27",
            dac_file="/path/to/dac13",
            voltage_threshold_dac=0
        )
    ])
    assert set(ret.adalm) == set([
        Adalm("0", True, "usb:1.6.5", "sn1", "100000000.0"),
        Adalm("1", False, "usb:1.7.5", "sn2", "100000000.0"),
    ])
