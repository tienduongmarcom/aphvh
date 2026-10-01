import unittest

from aphvh.costing_rules import split_by_weight


class TestSplitByWeight(unittest.TestCase):
    def test_two_outputs_40_20(self):
        # 100 kg đầu vào 10,8 tr → 40 kg A + 20 kg B
        self.assertEqual(split_by_weight(10_800_000, [40, 20]), [7_200_000, 3_600_000])

    def test_residual_goes_to_largest(self):
        self.assertEqual(split_by_weight(1_000_000, [1, 2, 1]), [250_000, 500_000, 250_000])
        # 100/3 = 33,33 → làm tròn 33 mỗi dòng, thiếu 1 → dòng lớn nhất (đầu tiên khi bằng nhau) nhận
        self.assertEqual(split_by_weight(100, [1, 1, 1]), [34, 33, 33])
        # Phần lẻ vào dòng có kg lớn nhất, không phải dòng đầu
        self.assertEqual(split_by_weight(100, [1, 1, 1.0001]), [33, 33, 34])

    def test_sum_always_equals_total(self):
        for total in (1, 7, 999_999, 123_456_789):
            for weights in ([1, 1, 1], [12.5, 7.5, 4.5, 0.5], [18, 23.5, 11, 13.5], [0.001, 1000]):
                self.assertEqual(sum(split_by_weight(total, weights)), total)

    def test_decimal_precision(self):
        amounts = split_by_weight(100, [1, 1, 1], precision=2)
        self.assertAlmostEqual(sum(amounts), 100, places=6)

    def test_invalid_weights(self):
        with self.assertRaises(ValueError):
            split_by_weight(100, [0, 0])
        with self.assertRaises(ValueError):
            split_by_weight(100, [1, -1, 2])

    def test_single_output(self):
        self.assertEqual(split_by_weight(5_000_000, [60]), [5_000_000])


if __name__ == "__main__":
    unittest.main()


class TestSplitWithFixed(unittest.TestCase):
    def test_fixed_rows_deducted_first(self):
        from aphvh.costing_rules import split_with_fixed

        # Đầu vào 1.000.000; phế 100.000 giá cố định; còn 900.000 chia 30 kg : 60 kg.
        self.assertEqual(split_with_fixed(1_000_000, [100_000], [30, 60]), [300000.0, 600000.0])

    def test_no_fixed_equals_v1(self):
        from aphvh.costing_rules import split_by_weight, split_with_fixed

        self.assertEqual(split_with_fixed(10_800_000, [], [40, 20]), split_by_weight(10_800_000, [40, 20]))

    def test_fixed_larger_than_total(self):
        from aphvh.costing_rules import split_with_fixed

        with self.assertRaises(ValueError):
            split_with_fixed(100, [60, 50], [1])

    def test_sum_equals_total(self):
        from aphvh.costing_rules import split_with_fixed

        out = split_with_fixed(1_000_001, [123_457, 1], [7, 11, 13])
        self.assertEqual(sum(out) + 123_457 + 1, 1_000_001)
