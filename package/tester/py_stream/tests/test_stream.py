from time import sleep
from unittest import TestCase, skipUnless

from serial.serialutil import SerialException

from stream._stack import StreamStack
from stream.byte import SerialStream
from stream.coder import CheckSumCoder, CoderStream
from stream.packer import HisensePacker, PackerStream
from stream.topic import ByteTopicStream

from . import (
    DATA_FIRST,
    DATA_LAST,
    DATA_SIMPLE,
    HAS_BRIDGED_SERIAL,
    SERIAL1_PARAMS,
    SERIAL2_PARAMS,
)


@skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
class Test01SerialStream(TestCase):
    def test_01_open_close(self):
        s = SerialStream(SERIAL1_PARAMS)
        with self.assertRaises(
            RuntimeError, msg="Closed stream should raise if written to"
        ):
            s.write(DATA_SIMPLE)
        try:
            s.open()
            s.close()
            s.open()
        except Exception:
            self.fail("Closing and reopening should not raise exception")
        with self.assertRaises(
            RuntimeError, msg="Already opened port not raising an exception"
        ):
            s.open()
        try:
            s.close()
            s.close()
        except Exception:
            self.fail("Closing closed port should not raise exception")

    def test_02_simple_package(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        s1.open()
        s2.open()
        s1.write(DATA_SIMPLE)
        sleep(0.1)
        self.assertEqual(
            s2.in_waiting, len(DATA_SIMPLE), "Invalid number of bytes in waiting"
        )
        data_in = s2.read(len(DATA_SIMPLE), timeout=0.1)
        self.assertEqual(DATA_SIMPLE, data_in, "Invalid data received")
        data_in = s2.read(timeout=0.1)
        self.assertFalse(len(data_in), "Should not receive any more data")
        s1.close()
        s2.close()


@skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
class Test02PackerStream(TestCase):
    def test_01_open_close(self):
        s = SerialStream(SERIAL1_PARAMS)
        p = PackerStream(HisensePacker, s)
        with self.assertRaises(
            RuntimeError, msg="Closed stream should raise if written to"
        ):
            p.write([DATA_SIMPLE])
        try:
            p.open()
            p.close()
            p.open()
        except Exception:
            self.fail("Closing and reopening should not raise exception")
        with self.assertRaises(
            (RuntimeError, SerialException),
            msg="Already opened stream not raising an exception",
        ):
            p.open()
        try:
            p.close()
            p.close()
        except Exception:
            self.fail("Closing closed stream should not raise exception")

    def test_02_simple_package(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        p1 = PackerStream(HisensePacker, s1)
        p2 = PackerStream(HisensePacker, s2)
        p1.open()
        p2.open()
        p1.write([DATA_SIMPLE])
        sleep(0.1)
        self.assertEqual(p2.in_waiting, 1, "Invalid number of packets in waiting")
        data_in = p2.read(timeout=0.1)
        self.assertEqual(len(data_in), 1, "Invalid number of packages received")
        self.assertEqual(DATA_SIMPLE, data_in[0], "Invalid data received")
        data_in = p2.read(timeout=0.1)
        self.assertFalse(len(data_in), "Should not receive any more data")
        p1.close()
        p2.close()


@skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
class Test03CoderStream(TestCase):
    def test_01_open_close(self):
        s = SerialStream(SERIAL1_PARAMS)
        p = PackerStream(HisensePacker, s)
        c = CoderStream(CheckSumCoder, p)
        with self.assertRaises(
            RuntimeError, msg="Closed stream should raise if written to"
        ):
            c.write([DATA_SIMPLE])
        try:
            c.open()
            c.close()
            c.open()
        except Exception:
            self.fail("Closing and reopening should not raise exception")
        with self.assertRaises(
            (RuntimeError, SerialException),
            msg="Already opened stream not raising an exception",
        ):
            c.open()
        try:
            c.close()
            c.close()
        except Exception:
            self.fail("Closing closed stream should not raise exception")

    def test_02_simple_package(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        p1 = PackerStream(HisensePacker, s1)
        p2 = PackerStream(HisensePacker, s2)
        c1 = CoderStream(CheckSumCoder, p1)
        c2 = CoderStream(CheckSumCoder, p2)
        c1.open()
        c2.open()
        c1.write([DATA_SIMPLE])
        sleep(0.1)
        self.assertEqual(c2.in_waiting, 1, "Invalid number of packets in waiting")
        data_in = c2.read(timeout=0.1)
        self.assertEqual(len(data_in), 1, "Invalid number of packages received")
        self.assertEqual(DATA_SIMPLE, data_in[0], "Invalid data received")
        data_in = c2.read(timeout=0.1)
        self.assertFalse(len(data_in), "Should not receive any more data")
        c1.close()
        c2.close()


@skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
class Test04TopicStream(TestCase):
    def test_01_open_close(self):
        s = SerialStream(SERIAL1_PARAMS, 2000000)
        p = PackerStream(HisensePacker, s)
        c = ByteTopicStream(p, topic_length=2)
        with self.assertRaises(
            RuntimeError, msg="Closed stream should raise if written to"
        ):
            c.write([(b"ab", DATA_SIMPLE)])
        c.open()
        try:
            c.close()
            c.open()
        except Exception:
            self.fail("Closing and reopening should not raise exception")
        with self.assertRaises(
            (RuntimeError, SerialException),
            msg="Already opened stream not raising an exception",
        ):
            c.open()
        try:
            c.close()
            c.close()
        except Exception:
            self.fail("Closing closed stream should not raise exception")

    def test_02_simple_package(self):
        topic1 = b"12"
        topic2 = bytearray(b"13")
        topic_short = b"1"
        topic_long = b"123"
        msg1 = bytearray(b"123456")
        msg2 = bytearray(b"654321")
        t1, t2 = self.get_streams()
        # TODO: test direct stream write
        try:
            s = t1[topic1]
        except:
            self.fail("Topic stream construction failed")
        try:
            data_in = s.read(block=False)
            self.assertIsInstance(data_in, list, "Read return type should be list")
            self.assertEqual(len(data_in), 0, "Empty stream should return empty list")
        except Exception:
            self.fail("Reading a topic should not fail if stream is opened")
        with self.assertRaises(ValueError, msg="Too short topic should be rejected"):
            t1[topic_short]
        with self.assertRaises(ValueError, msg="Too long topic should be rejected"):
            t1[topic_long]
        t1[topic1].write([DATA_SIMPLE])
        sleep(0.1)
        self.assertEqual(
            len(t2[topic2].read(block=False)),
            0,
            "Topic that was not written to, should not contain a message",
        )
        self.assertEqual(
            t2[topic1].in_waiting, 1, "Invalid number of packets in waiting"
        )
        data_in = t2[topic1].read(block=False)
        self.assertEqual(len(data_in), 1, "There should be a single message")
        self.assertEqual(data_in[0], DATA_SIMPLE, "Message is invalid")
        t1[topic2].write([DATA_SIMPLE, DATA_FIRST, DATA_LAST])
        sleep(0.1)
        data_in = t2[topic2].read(10, timeout=0.2)
        self.assertEqual(len(data_in), 3, "There should be three messages")
        self.assertEqual(
            data_in, [DATA_SIMPLE, DATA_FIRST, DATA_LAST], "Messages are invalid"
        )
        t2[topic1].write(data_in)
        sleep(0.1)
        data_in = t1[topic1].read(10, block=False)
        self.assertEqual(len(data_in), 3, "There should be three messages")
        self.assertEqual(
            data_in, [DATA_SIMPLE, DATA_FIRST, DATA_LAST], "Messages are invalid"
        )
        t2[topic1].write(data_in)
        sleep(0.1)
        t1[topic1].discard()
        data_in = t1[topic1].read(block=False)
        self.assertEqual(
            len(data_in), 0, "There should be no messages after discarding"
        )
        t1.close()
        t2.close()

    def get_streams(self):
        s1 = SerialStream(SERIAL1_PARAMS, 2000000)
        s2 = SerialStream(SERIAL2_PARAMS, 2000000)
        p1 = PackerStream(HisensePacker, s1)
        p2 = PackerStream(HisensePacker, s2)
        t1 = ByteTopicStream(p1, topic_length=2)
        t2 = ByteTopicStream(p2, topic_length=2)
        t1.open()
        t2.open()
        return t1, t2


@skipUnless(HAS_BRIDGED_SERIAL, "Bridged serial ports not found - install com0com")
class Test11StreamStack(TestCase):
    def test_01_open_close(self):
        ss = StreamStack(
            (
                (SerialStream, (SERIAL1_PARAMS, 2000000), {}),
                (PackerStream, (HisensePacker,), {}),
                (CoderStream, (CheckSumCoder,), {}),
            )
        )
        with self.assertRaises(
            RuntimeError, msg="Closed stream should raise if written to"
        ):
            ss.write([DATA_SIMPLE])
        try:
            ss.open()
            ss.close()
            ss.open()
        except Exception:
            self.fail("Closing and reopening should not raise exception")
        with self.assertRaises(
            RuntimeError, msg="Already opened port not raising an exception"
        ):
            ss.open()
        try:
            ss.close()
            ss.close()
        except Exception:
            self.fail("Closing closed port should not raise exception")
        ss.open()
        del ss
        try:
            ss = StreamStack(
                (
                    (SerialStream, (SERIAL1_PARAMS, 2000000), {}),
                    (PackerStream, (HisensePacker,), {}),
                    (CoderStream, (CheckSumCoder,), {}),
                )
            )
        except:
            self.fail("Deleting a stream stack should close and delete all streams")

    def test_02_simple_package(self):
        ss1 = StreamStack(
            (
                (SerialStream, (SERIAL1_PARAMS, 2000000), {}),
                (PackerStream, (HisensePacker,), {}),
                (CoderStream, (CheckSumCoder,), {}),
            )
        )
        ss2 = StreamStack(
            (
                (SerialStream, (SERIAL2_PARAMS, 2000000), {}),
                (PackerStream, (HisensePacker,), {}),
                (CoderStream, (CheckSumCoder,), {}),
            )
        )
        ss1.open()
        ss2.open()
        ss1.write([DATA_SIMPLE])
        data_in = ss2.read(timeout=0.1)
        self.assertEqual(len(data_in), 1, "Invalid number of packages received")
        self.assertEqual(DATA_SIMPLE, data_in[0], "Invalid data received")
        data_in = ss2.read(timeout=0.1)
        self.assertFalse(len(data_in), "Should not receive any more data")
