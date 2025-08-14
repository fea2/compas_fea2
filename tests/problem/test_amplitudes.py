import unittest

from compas_fea2.problem.amplitudes import Amplitude


class TestAmplitude(unittest.TestCase):
    def test_amplitude_init_and_data_roundtrip(self):
        A = Amplitude([0.0, 1.0, 0.5], [0.0, 1.0, 2.0])
        data = A.__data__
        self.assertEqual(data["multipliers"], [0.0, 1.0, 0.5])
        self.assertEqual(data["times"], [0.0, 1.0, 2.0])

        A2 = Amplitude.__from_data__(data)
        self.assertEqual(A2.multipliers, [0.0, 1.0, 0.5])
        self.assertEqual(A2.times, [0.0, 1.0, 2.0])

    def test_amplitude_validation_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            Amplitude([0.0, 1.0], [0.0])

    def test_amplitude_multipliers_times_zip(self):
        A = Amplitude([1.0, 2.0], [0.0, 1.0])
        self.assertEqual(list(A.multipliers_times), [(1.0, 0.0), (2.0, 1.0)])

    def test_amplitude_equally_spaced_current_bug(self):
        # The current implementation uses len(fixed_interval) which raises TypeError for float
        with self.assertRaises(TypeError):
            Amplitude.equally_spaced([0.0, 1.0, 2.0], first_value=0.0, fixed_interval=0.5)


if __name__ == "__main__":
    unittest.main()
