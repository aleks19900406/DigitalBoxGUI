import re
from collections import defaultdict
from typing import Tuple

import serial.tools.list_ports

from stream.byte import SyncByteInternalsType, SyncByteIOStream


def get_bridged_serial() -> Tuple[str, str]:
    bridged_serials = tuple(
        comport
        for comport in serial.tools.list_ports.comports()
        if comport.hwid.startswith("COM0COM")
    )
    bridges = defaultdict(list)
    for comport in bridged_serials:
        bridge_index = re.findall(r"\d+$", comport.hwid)
        if bridge_index:
            bridges[bridge_index[0]].append(comport.device)
    for bridge in bridges.values():
        if len(bridge) == 2:
            return tuple(bridge)
    return tuple()


BRIDGED_SERIAL = get_bridged_serial()
HAS_BRIDGED_SERIAL = bool(BRIDGED_SERIAL)
if HAS_BRIDGED_SERIAL:
    # SERIAL1_PARAMS = {"device": re.compile(BRIDGED_SERIAL[0])}
    # SERIAL2_PARAMS = {"device": re.compile(BRIDGED_SERIAL[1])}
    SERIAL1_PARAMS = {"device": BRIDGED_SERIAL[0]}
    SERIAL2_PARAMS = {"device": BRIDGED_SERIAL[1]}
else:
    SERIAL1_PARAMS = None
    SERIAL2_PARAMS = None

DATA_FIRST = bytearray(b"12345")
DATA_LAST = bytearray(b"67890")
DATA_SIMPLE = DATA_FIRST + DATA_LAST


class CrossByteStream(SyncByteIOStream):
    def _r_w_worker(self, internal: SyncByteInternalsType):
        data = bytearray()
        with internal.buffer_lock:
            if not internal.write_buffer:
                internal.buffer_lock.wait()
            if internal.write_buffer:
                data = internal.write_buffer[:]
                internal.write_buffer.clear()
                internal.read_buffer.extend(data)
                internal.buffer_lock.notify_all()
