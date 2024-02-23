from unittest import TestCase

from stream.coder import CoderDecodeError, CRCCoder


class Test01CRCCoder(TestCase):
    def test_01_lte16(self):
        coder = CRCCoder("lte16")
        data = bytearray([1, 2, 3, 4, 5, 6])
        encoded = coder.encode(data)
        self.assertEqual(len(data) + 2, len(encoded), "lte16 should add 2 bytes")
        try:
            decoded = coder.decode(encoded)
        except CoderDecodeError:
            self.fail("Valid crc should not raise an exception")
        self.assertEqual(data, decoded, "Decoded data is not equal to data")
        invalid = encoded[1:]
        with self.assertRaises(
            CoderDecodeError, msg="Invalid crc should raise an exception"
        ):
            coder.decode(invalid)
