from unittest import TestCase

from stream.packer import HisensePacker, InspectorPacker, TerminationPacker

from . import DATA_FIRST, DATA_LAST, DATA_SIMPLE


class Test01TerminationPacker(TestCase):
    def test_01_unpack(self):
        protocol = TerminationPacker()
        packets = protocol.try_unpack_data(DATA_FIRST)
        self.assertEqual(len(packets), 0, "Non terminated data should not be unpacked")
        packets = protocol.try_unpack_data(protocol.terminator + DATA_LAST)
        self.assertEqual(len(packets), 1, "Only one terminated packet is present")
        self.assertEqual(packets[0], DATA_FIRST, "Invalid unpacked data")
        packets = protocol.try_unpack_data(
            DATA_FIRST + protocol.terminator + DATA_LAST + protocol.terminator
        )
        self.assertEqual(len(packets), 2, "Two packets should be returned")
        self.assertEqual(
            packets, [DATA_LAST + DATA_FIRST, DATA_LAST], "Invalid unpacked data"
        )

    def test_02_unpack(self):
        terminator = b"\r\n"
        protocol = TerminationPacker(terminator)
        self.assertEqual(protocol.terminator, terminator, "Misunderstood terminator")
        packets = protocol.try_unpack_data(DATA_FIRST)
        self.assertEqual(len(packets), 0, "Non terminated data should not be unpacked")
        packets = protocol.try_unpack_data(protocol.terminator + DATA_LAST)
        self.assertEqual(len(packets), 1, "Only one terminated packet is present")
        self.assertEqual(packets[0], DATA_FIRST, "Invalid unpacked data")
        packets = protocol.try_unpack_data(
            DATA_FIRST + protocol.terminator + DATA_LAST + protocol.terminator
        )
        self.assertEqual(len(packets), 2, "Two packets should be returned")
        self.assertEqual(
            packets, [DATA_LAST + DATA_FIRST, DATA_LAST], "Invalid unpacked data"
        )

    def test_03_pack(self):
        terminator = b"\r\n"
        protocol = TerminationPacker(terminator)
        self.assertEqual(protocol.pack_data(DATA_SIMPLE), DATA_SIMPLE + terminator)
        with self.assertRaises(ValueError, msg="Terminated data should not be valid"):
            protocol.pack_data(DATA_FIRST + terminator + DATA_LAST)


class Test02HisensePacker(TestCase):
    protocol: HisensePacker

    @classmethod
    def setUpClass(cls):
        cls.protocol = HisensePacker()
        return super().setUpClass()

    def test_01_simple_packet(self):
        data_true = bytearray(DATA_SIMPLE)
        self.simple_data_test(data_true)

    def test_02_long_packet(self):
        data_true = bytearray(DATA_SIMPLE * 100)
        self.simple_data_test(data_true)

    def simple_data_test(self, data_true: bytearray):
        packet_true = self.pack_data(bytearray([*data_true]))
        packet = self.protocol.pack_data(data_true)
        self.assertEqual(packet_true, packet, "Error with data packing")
        data = self.protocol.try_unpack_data(packet)[0]
        self.assertEqual(data_true, data, "Error with data unpacking")

    def test_03_packet_with_escape(self):
        data_true = bytearray([*DATA_FIRST, self.protocol.ESCAPE, *DATA_LAST])
        packet_true = self.pack_data(
            bytearray([*DATA_FIRST, self.protocol.ESCAPE, *DATA_LAST])
        )
        packet = self.protocol.pack_data(data_true)
        self.assertEqual(packet_true, packet, "Error with data packing")
        data = self.protocol.try_unpack_data(packet)[0]
        self.assertEqual(data_true, data, "Error with data unpacking")

    def test_04_unpack_invalid_escape(self):
        data_true = bytearray([*DATA_FIRST, self.protocol.ESCAPE, *DATA_LAST])
        packet_invalid = self.pack_data(bytearray([*data_true])).replace(
            bytearray([self.protocol.ESCAPE] * 2), bytearray([self.protocol.ESCAPE])
        )
        with self.assertRaises(
            IndexError, msg="no data should be returned and package discarded"
        ):
            data = self.protocol.try_unpack_data(packet_invalid)[0]

    def test_05_escape_packet(self):
        escape = self.protocol.ESCAPE
        start = self.protocol.START
        stop = self.protocol.STOP
        data_true = bytearray(
            [escape, escape, escape, start, escape, escape, escape, stop]
        )
        packet_true = bytearray(
            [
                escape,
                start,
                escape,
                escape,
                escape,
                escape,
                escape,
                escape,
                start,
                escape,
                escape,
                escape,
                escape,
                escape,
                escape,
                stop,
                escape,
                stop,
            ]
        )
        packet = self.protocol.pack_data(data_true)
        self.assertEqual(packet_true, packet, "Package with escape chars is invalid")
        data = self.protocol.try_unpack_data(packet)[0]
        self.assertEqual(data_true, data, "Data with escape chars is invalid")

    def test_06_multiple_escape_packets(self):
        escape = self.protocol.ESCAPE
        start = self.protocol.START
        stop = self.protocol.STOP
        data_true1 = bytearray(
            [escape, escape, escape, start, escape, escape, escape, stop]
        )
        data_true2 = bytearray([escape, start, escape, escape])
        packet_true1 = bytearray(
            [
                escape,
                start,
                escape,
                escape,
                escape,
                escape,
                escape,
                escape,
                start,
                escape,
                escape,
                escape,
                escape,
                escape,
                escape,
                stop,
                escape,
                stop,
            ]
        )
        packet_true2 = bytearray(
            [
                escape,
                start,
                escape,
                escape,
                start,
                escape,
                escape,
                escape,
                escape,
                escape,
                stop,
            ]
        )
        packets = bytearray([1, 3, 45, *packet_true1, 23, 53, 12, *packet_true2])
        data_list = self.protocol.try_unpack_data(packets)
        self.assertEqual(len(data_list), 2, "Invalid number of packages unpacked")
        self.assertEqual(data_true1, data_list[0], "First packet's data is invalid")
        self.assertEqual(data_true2, data_list[1], "Second packet's data is invalid")

    def pack_data(self, data: bytearray):
        return bytearray(
            [
                self.protocol.ESCAPE,
                self.protocol.START,
                *data.replace(
                    bytearray([self.protocol.ESCAPE]),
                    bytearray([self.protocol.ESCAPE] * 2),
                ),
                self.protocol.ESCAPE,
                self.protocol.STOP,
            ]
        )


class Test03InspectorPacker(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = InspectorPacker()
        return super().setUpClass()

    def test_01_simple_packet(self):
        data_true = bytearray(DATA_SIMPLE)
        self.simple_data_test(data_true)

    def test_02_long_packet(self):
        data_true = bytearray(DATA_SIMPLE * 100)
        self.simple_data_test(data_true)

    def simple_data_test(self, data_true: bytearray):
        packet_true = self.pack_data(bytearray([*data_true]))
        packet = self.protocol.pack_data(data_true)
        self.assertEqual(packet_true, packet, "Error with data packing")
        data = self.protocol.try_unpack_data(packet)[0]
        self.assertEqual(data_true, data, "Error with data unpacking")

    def test_03_packet_with_escape(self):
        data_true = bytearray([*DATA_FIRST, self.protocol.EOF, *DATA_LAST])
        packet_true = self.pack_data(
            bytearray(
                [
                    *DATA_FIRST,
                    self.protocol.EOF,
                    *DATA_LAST,
                ]
            )
        )
        packet = self.protocol.pack_data(data_true)
        self.assertEqual(packet_true, packet, "Error with data packing")
        data = self.protocol.try_unpack_data(packet)[0]
        self.assertEqual(data_true, data, "Error with data unpacking")

    def test_04_unpack_invalid_escape(self):
        packet_invalid = bytearray([*DATA_FIRST, self.protocol.EOF, *DATA_LAST])
        with self.assertRaises(
            IndexError, msg="no data should be returned and package discarted"
        ):
            data = self.protocol.try_unpack_data(packet_invalid)[0]

    def test_05_escape_packet(self):
        stuff = self.protocol.STF
        start = self.protocol.SOF
        stop = self.protocol.EOF
        data_true = bytearray([stuff, stuff, stuff, start, stuff, stuff, stuff, stop])
        packet_true = bytearray(
            [
                start,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - start,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stop,
                stop,
            ]
        )
        packet = self.protocol.pack_data(data_true)
        self.assertEqual(packet_true, packet, "Package with escape chars is invalid")
        data = self.protocol.try_unpack_data(packet)[0]
        self.assertEqual(data_true, data, "Data with escape chars is invalid")

    def test_06_multiple_escape_packets(self):
        stuff = self.protocol.STF
        start = self.protocol.SOF
        stop = self.protocol.EOF
        data_true1 = bytearray([stuff, stuff, stuff, start, stuff, stuff, stuff, stop])
        data_true2 = bytearray([stuff, start, stuff, stuff])
        packet_true1 = bytearray(
            [
                start,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - start,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stop,
                stop,
            ]
        )
        packet_true2 = bytearray(
            [
                start,
                stuff,
                stuff - stuff,
                stuff,
                stuff - start,
                stuff,
                stuff - stuff,
                stuff,
                stuff - stuff,
                stop,
            ]
        )
        packets = bytearray([1, 3, 45, *packet_true1, 23, 53, 12, *packet_true2])
        data_list = self.protocol.try_unpack_data(packets)
        self.assertEqual(len(data_list), 2, "Invalid number of packages unpacked")
        self.assertEqual(data_true1, data_list[0], "First packet's data is invalid")
        self.assertEqual(data_true2, data_list[1], "Second packet's data is invalid")

    def pack_data(self, data: bytearray):
        packed = bytearray([self.protocol.SOF])
        for byte in data:
            if byte < self.protocol.SOF:
                packed.append(byte)
            else:
                packed.append(self.protocol.STF)
                packed.append(self.protocol.STF - byte)
        packed.append(self.protocol.EOF)
        return packed
