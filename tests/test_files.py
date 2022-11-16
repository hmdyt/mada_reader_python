from pathlib import Path
from mada_reader.files import scan_mada_files
from mada_reader.models.mada_config import parse

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
                "active": 1,
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

TEST_SCAN_PATH = Path("tests/assets/test_files")


def test_scan_mada_files():
    mada_config = parse(JSON_STRING)
    scaned_files = scan_mada_files(TEST_SCAN_PATH, mada_config, 0, 1)
    scaned_files_name = list(map(lambda x: x.name, scaned_files))
    assert scaned_files_name == [
        "GBKB-00_0000.mada",
        "GBKB-13_0000.mada",
        "GBKB-00_0001.mada",
        "GBKB-13_0001.mada"
    ]
