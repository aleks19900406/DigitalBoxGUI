from time import sleep
from unittest import TestCase

from stream._utils import Timer


class Test01_Timer(TestCase):
    def test_01_timer_remaining(self):
        t = Timer(2)
        sleep(1)
        if t.remaining is None:
            self.fail("Timer remaining should not be None for Timer of known duration")
        self.assertAlmostEqual(
            t.remaining, 1, delta=0.02, msg="Timer remaining is incorrect"
        )
        self.assertFalse(t.expired, "Timer should not be marked as expired")
        sleep(1)
        self.assertEqual(t.remaining, 0, "Timer remaining should be 0")
        self.assertTrue(t.expired, "Timer should be marked as expired")

    def test_02_timer_endless(self):
        t = Timer(None)
        sleep(1)
        self.assertFalse(t.expired, "Timer should never expire")
        self.assertIs(t.remaining, None, "Endless Timer remaining should be None")
