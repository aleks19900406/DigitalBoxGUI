from unittest import TestCase
from unittest.case import skipUnless

from stream.byte import SerialStream
from stream.coder import CoderStream, CRCCoder
from stream.packer import HisensePacker, PackerStream
from stream.specializations.hisense import (
    CHECKSUM_CODER,
    ALFrame,
    ChecksumType,
    DeviceFamily,
    HisenseStrem,
    LLFrame,
    LLId1,
    LLResponseId,
    NLAddress,
    NLFrame,
    NLId1,
    NLResponseId,
    TLEncryption,
    TLFrame,
    TLId1,
    TLResponseId,
    TLStatus,
)

from .. import (
    DATA_FIRST,
    DATA_SIMPLE,
    HAS_BRIDGED_SERIAL,
    SERIAL1_PARAMS,
    SERIAL2_PARAMS,
    CrossByteStream,
)


class Test01LinkLayer(TestCase):
    def test_01_llid1(self):
        i = 0  # No LLId2
        i += 0 << 1  # Frame sequence number = 0
        i += 1 << 5  # Length is 2 bytes
        i += 2 << 6  # Checksum method is CRC16
        llid = LLId1(0, 0, 1, 2)
        self.assertEqual(llid.ll2_present, 0, "Invalid ll2 present")
        self.assertEqual(llid.frame_number, 0, "Invalid frame number")
        self.assertEqual(llid.nl_len_repr_size, 1, "Invalid nl size repr")
        self.assertEqual(llid.checksum_type, 2, "Invalid checksum type")
        self.assertEqual(bytes([i]), bytes(llid), "Invalid bytes representation")
        self.assertEqual(int(llid), i, "Invalid int representation")

    def test_02_frame_construction(self):
        i = 0  # No LLId2
        i += 0 << 1  # Frame sequence number = 0
        i += 1 << 5  # Length is 2 bytes
        i += 2 << 6  # Checksum method is CRC16
        correct = bytearray(
            [
                0,  # LLResponseId.TRSM
                i,  # LLId1 is set, LLId2 and LLId3 are omitted
                0,  # Size MSByte (big endian)
                len(DATA_SIMPLE),  # Size LSByte (big endian)
                *DATA_SIMPLE,
            ]
        )
        f = LLFrame(
            LLResponseId.TRSM,
            LLId1(0, 0, 1, ChecksumType.CRC16),
            None,
            None,
            len(DATA_SIMPLE),
            DATA_SIMPLE,
        )
        self.assertEqual(f.response_id, 0, "Invalid response id")
        self.assertEqual(int(f.id1), i, "Invalid id1")
        self.assertIsNone(f.id2, "Invalid id2")
        self.assertIsNone(f.id3, "Invalid id3")
        self.assertEqual(f.nl_length, len(DATA_SIMPLE), "Invalid data length")
        self.assertEqual(f.payload, DATA_SIMPLE, "Invalid payload")
        self.assertEqual(correct, bytearray(f), "Bytearrays are not the same")
        i = 0  # No LLId2
        i += 0 << 1  # Frame sequence number = 0
        i += 0 << 5  # Length is 2 bytes
        i += 2 << 6  # Checksum method is CRC16
        correct = bytearray(
            [
                0,  # LLResponseId.TRSM
                i,  # LLId1 is set, LLId2 and LLId3 are omitted
                len(DATA_SIMPLE),  # Size
                *DATA_SIMPLE,
            ]
        )
        f = LLFrame(
            LLResponseId.TRSM,
            LLId1(0, 0, 0, ChecksumType.CRC16),
            None,
            None,
            len(DATA_SIMPLE),
            DATA_SIMPLE,
        )
        self.assertEqual(int(f.id1), i, "Invalid id1 2")
        self.assertEqual(f.nl_length, len(DATA_SIMPLE), "Invalid data length 2")
        self.assertEqual(correct, bytearray(f), "Bytearrays are not the same 2")

    def test_03_frame_reconstruction(self):
        f1 = LLFrame(
            LLResponseId.TRSM,
            LLId1(0, 0, 1, ChecksumType.CRC16),
            None,
            None,
            len(DATA_SIMPLE),
            DATA_SIMPLE,
        )
        p1 = CHECKSUM_CODER[ChecksumType(f1.id1.checksum_type)].encode(bytearray(f1))
        f2 = LLFrame(bytearray(p1))
        self.assertEqual(f1.response_id, f2.response_id, "Invalid response id")
        self.assertEqual(int(f1.id1), int(f2.id1), "Invalid id1")
        self.assertEqual(f1.id2, f2.id2, "Invalid id2")
        self.assertEqual(f1.id3, f2.id3, "Invalid id3")
        self.assertEqual(f1.nl_length, f2.nl_length, "Invalid data length")
        self.assertEqual(bytearray(f1), bytearray(f2), "Bytearrays are not the same")

    def test_04_data_shortage(self):
        with self.assertRaises(
            ValueError, msg="Incompatible decalred and data lengths 1"
        ):
            f = LLFrame(
                LLResponseId.TRSM,
                LLId1(0, 0, 1, ChecksumType.CRC16),
                None,
                None,
                len(DATA_SIMPLE) + 10,
                DATA_SIMPLE,
            )
        with self.assertRaises(
            ValueError, msg="Incompatible decalred and data lengths 2"
        ):
            data = bytearray(
                [0, ChecksumType.CRC16.value, 10, *[1, 2, 3, 4, 5, 6, 7, 8, 9]]
            )
            LLFrame(data)


class Test02NetworkLayer(TestCase):
    def test_01_nlid1(self):
        i = 0  # No NLId2
        i += 0 << 1  # RESERVED
        i += 0 << 3  # Address code is two bytes
        i += 0 << 5  # Only address1 and address2 are present
        i += 0 << 6  # All addresses are codes from specification
        nlid = NLId1(0, i, 0, 0, 0)
        self.assertEqual(nlid.nl2_present, 0, "Invalid ll2 present")
        self.assertEqual(nlid.addr_len_repr_size, 0, "Invalid address representation")
        self.assertEqual(nlid.all_addresses_present, 0, "Invalid addresses present")
        self.assertEqual(nlid.addressing, 0, "Invalid addressing")
        self.assertEqual(bytes([i]), bytes(nlid), "Invalid bytes representation")
        self.assertEqual(int(nlid), 0, "Invalid int representation")

    def test_02_frame_construction(self):
        correct = bytearray(
            [
                0,  # LLResponseId.TRSM
                0,  # LLId1 is set, LLId2 and LLId3 are omitted
                7,  # Targeting device is from dishwasher family
                0,  # Targeting processor index
                254,  # Source is master
                1,  # As specified for master
                *DATA_SIMPLE,
            ]
        )
        f = NLFrame(
            NLResponseId.TRSM,
            NLId1(),
            None,
            None,
            NLAddress(DeviceFamily.DISH_WASHER, 0),
            NLAddress(DeviceFamily.WIFI, 1),
            None,
            None,
            None,
            DATA_SIMPLE,
        )
        self.assertEqual(f.response_id, 0, "Invalid response id")
        self.assertEqual(int(f.id1), 0, "Invalid id1")
        self.assertIsNone(f.id2, "Invalid id2")
        self.assertIsNone(f.id3, "Invalid id3")
        self.assertEqual(
            f.addr1.device_family,
            DeviceFamily.DISH_WASHER,
            "Invalid addr1 device family",
        )
        self.assertEqual(f.addr1.device_number, 0, "Invalid addr1 device index")
        self.assertEqual(
            f.addr2.device_family, DeviceFamily.WIFI, "Invalid addr2 device family"
        )
        self.assertEqual(f.addr2.device_number, 1, "Invalid addr2 device index")
        self.assertIsNone(f.addr3, "Invalid addr3")
        self.assertIsNone(f.addr4, "Invalid addr4")
        self.assertIsNone(f.addr5, "Invalid addr5")
        self.assertEqual(f.payload, DATA_SIMPLE, "Invalid payload")
        self.assertEqual(correct, bytearray(f), "Bytearrays are not the same")

    def test_03_frame_reconstruction(self):
        f1 = NLFrame(
            NLResponseId.TRSM,
            NLId1(),
            None,
            None,
            NLAddress(DeviceFamily.DISH_WASHER, 0),
            NLAddress(DeviceFamily.WIFI, 1),
            None,
            None,
            None,
            DATA_SIMPLE,
        )
        f2 = NLFrame(bytearray(f1))
        self.assertEqual(f1.response_id, f2.response_id, "Invalid response id")
        self.assertEqual(int(f1.id1), int(f2.id1), "Invalid id1")
        self.assertEqual(f1.id2, f2.id2, "Invalid id2")
        self.assertEqual(f1.id3, f2.id3, "Invalid id3")
        self.assertEqual(
            f1.addr1.device_family,
            f2.addr1.device_family,
            "Invalid addr1 device family",
        )
        self.assertEqual(
            f1.addr1.device_number, f2.addr1.device_number, "Invalid addr1 device index"
        )
        self.assertEqual(
            f1.addr2.device_family,
            f2.addr2.device_family,
            "Invalid addr2 device family",
        )
        self.assertEqual(
            f1.addr2.device_number, f2.addr2.device_number, "Invalid addr2 device index"
        )
        self.assertEqual(f1.addr3, f2.addr3, "Invalid addr3")
        self.assertEqual(f1.addr4, f2.addr4, "Invalid addr4")
        self.assertEqual(f1.addr5, f2.addr5, "Invalid addr5")
        self.assertEqual(bytearray(f1), bytearray(f2), "Bytearrays are not the same")


class Test03TransportLayer(TestCase):
    def test_01_nlid1(self):
        i = 0  # No NLId2
        i += 0 << 1  # RESERVED
        i += 0 << 4  # Application layer is not encripted
        tlid = TLId1(i)
        self.assertEqual(tlid.tl2_present, 0, "Invalid tl2 present")
        self.assertEqual(tlid.al_encripted, 0, "Invalid al encryption type")
        self.assertEqual(bytes([i]), bytes(tlid), "Invalid bytes representation")
        self.assertEqual(int(tlid), i, "Invalid int representation")

    def test_02_frame_construction(self):
        correct = bytearray(
            [
                0,  # LLResponseId.TRSM
                0,  # LLId1 is set, LLId2 and LLId3 are omitted
                *DATA_SIMPLE,
            ]
        )
        f = TLFrame(
            TLResponseId(TLEncryption.NO_ENCRYPTION, TLStatus.MASTER),
            TLId1(),
            None,
            None,
            DATA_SIMPLE,
        )
        self.assertEqual(
            f.response_id.encryption,
            TLEncryption.NO_ENCRYPTION,
            "Invalid response id encryption",
        )
        self.assertEqual(
            f.response_id.status, TLStatus.MASTER, "Invalid response id status"
        )
        self.assertEqual(int(f.id1), 0, "Invalid id1")
        self.assertIsNone(f.id2, "Invalid id2")
        self.assertIsNone(f.id3, "Invalid id3")
        self.assertEqual(f.payload, DATA_SIMPLE, "Invalid payload")
        self.assertEqual(correct, bytearray(f), "Bytearrays are not the same")

    def test_03_frame_reconstruction(self):
        f1 = TLFrame(
            TLResponseId(TLEncryption.NO_ENCRYPTION, TLStatus.MASTER),
            TLId1(),
            None,
            None,
            DATA_SIMPLE,
        )
        f2 = TLFrame(bytearray(f1))
        self.assertEqual(
            f1.response_id.encryption,
            f2.response_id.encryption,
            "Invalid response id encryption",
        )
        self.assertEqual(
            f1.response_id.status, f1.response_id.status, "Invalid response id status"
        )
        self.assertEqual(int(f1.id1), int(f2.id1), "Invalid id1")
        self.assertEqual(f1.id2, f2.id2, "Invalid id1")
        self.assertEqual(f1.id3, f2.id3, "Invalid id1")
        self.assertEqual(bytearray(f1), bytearray(f2), "Bytearrays are not the same")


class Test04HisenseStream(TestCase):
    N_RETRIES = 10  # Number of retryes if peer does not respond

    def test_01_frame_numbering(self):
        s = HisenseStrem(CrossByteStream(), DeviceFamily.DISH_WASHER)
        numbers = tuple(s.get_frame_no() for _ in range(32))
        number_set = set(numbers)
        self.assertLessEqual(max(number_set), 15, "Invalid maximum")
        self.assertGreaterEqual(min(number_set), 0, "Invalid minimum")
        self.assertEqual(len(number_set), 16, "Invalid number of unique elements")
        for i in range(16):
            if i not in number_set:
                self.fail(f"Missing value {i}")

    @skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
    def test_02_stream(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        h1 = HisenseStrem(s1, DeviceFamily.DISH_WASHER)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        p2 = PackerStream(HisensePacker, s2)
        c2 = CoderStream(CRCCoder, p2, method="lte16")
        h1.open()
        c2.open()
        device_number = 1
        command = b"01"
        h1.write([(device_number, command, DATA_SIMPLE * 100)])
        packet = c2.read(1, timeout=1)[0]
        ll = LLFrame(packet)
        nl = NLFrame(ll.payload)
        tl = TLFrame(nl.payload)
        al = ALFrame(tl.payload)
        self.assertEqual(al.payload, DATA_SIMPLE * 100, "Invalid data received")
        c2.write([bytearray(self._compose_response(ll, DATA_FIRST))])
        response = h1.read(timeout=10)
        self.assertEqual(len(response), 1, "Response should arrive")
        self.assertEqual(response[0][2], DATA_FIRST, "Invalid data received back")
        h1.close()
        c2.close()

    @skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
    def test_03_timeout(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        h1 = HisenseStrem(s1, DeviceFamily.DISH_WASHER)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        p2 = PackerStream(HisensePacker, s2)
        h1.TIMEOUT = 0.001  # Mock timeout to raise early
        h1.open()
        p2.open()
        device_number = 1
        command = b"01"
        h1.write([(device_number, command, DATA_SIMPLE)])
        with self.assertRaises(RuntimeError, msg="Error should be raised on no reply"):
            h1.read(timeout=2)
        self.assertEqual(p2.in_waiting, self.N_RETRIES, "Invalid number of retryes")
        h1.close()
        p2.close()

    @skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
    def test_04_ll_error(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        h1 = HisenseStrem(s1, DeviceFamily.DISH_WASHER)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        p2 = PackerStream(HisensePacker, s2)
        c2 = CoderStream(CRCCoder, p2, method="lte16")
        h1.open()
        c2.open()
        device_number = 1
        command = b"01"
        # Unsupported checksum type
        h1.write([(device_number, command, DATA_SIMPLE)])
        frame = LLFrame(c2.read(timeout=2)[0])
        frame.response_id = LLResponseId.ERROR
        c2.write([bytearray(frame)])
        with self.assertRaises(TypeError, msg="Unsupported checksum type"):
            h1.read(timeout=2)
        # Link layer fail
        h1.clear_exceptions()
        h1.write([(device_number, command, DATA_SIMPLE)])
        frame = LLFrame(c2.read(timeout=2)[0])
        frame.response_id = LLResponseId.FAIL
        c2.write([bytearray(frame)])
        with self.assertRaises(NotImplementedError, msg="LL fail not implemented"):
            h1.read(timeout=2)
        # Link layer id2
        h1.clear_exceptions()
        h1.write([(device_number, command, DATA_SIMPLE)])
        frame = LLFrame(c2.read(timeout=2)[0])
        frame.id1.ll2_present = 1
        frame.id2 = 0
        c2.write([bytearray(frame)])
        with self.assertRaises(NotImplementedError, msg="LLId2 not implemented"):
            h1.read(timeout=2)
        # Invalid frame number - should retry
        h1.N_TRIES = 1
        h1.TIMEOUT = 1
        h1.clear_exceptions()
        h1.write([(device_number, command, DATA_SIMPLE)])
        frame = LLFrame(c2.read(timeout=2)[0])
        frame.id1.ll2_present = 1
        frame.id2 = 0
        c2.write([bytearray(frame)])
        with self.assertRaises(RuntimeError, msg="Error on no valid reply"):
            h1.read(timeout=2)
        h1.close()
        c2.close()

    def _compose_response(self, frame: LLFrame, payload: bytearray) -> LLFrame:
        nl1 = NLFrame(frame.payload)
        tl1 = TLFrame(nl1.payload)
        al1 = ALFrame(tl1.payload)
        al2 = ALFrame(al1.command, payload)
        tl2 = TLFrame(
            TLResponseId(TLStatus.SUCCESS, TLEncryption.NO_ENCRYPTION),
            TLId1(0, 0, 0),
            None,
            None,
            bytearray(al2),
        )
        nl2 = NLFrame(
            NLResponseId.SUCCESS,
            NLId1(0, 0, 0, 0, 0),
            None,
            None,
            nl1.addr2,
            nl1.addr1,
            None,
            None,
            None,
            bytearray(tl2),
        )
        payload = bytearray(nl2)
        return LLFrame(
            LLResponseId.SUCCESS, frame.id1, None, None, len(payload), payload
        )
