import unittest

from game.logic import clamp, collided, level_from_score, should_spawn_mega


class LogicTests(unittest.TestCase):
    def test_level_from_score(self):
        self.assertEqual(level_from_score(0, 10), 1)
        self.assertEqual(level_from_score(9, 10), 1)
        self.assertEqual(level_from_score(10, 10), 2)
        self.assertEqual(level_from_score(31, 10), 4)

    def test_should_spawn_mega(self):
        self.assertFalse(should_spawn_mega(0, 15))
        self.assertFalse(should_spawn_mega(14, 15))
        self.assertTrue(should_spawn_mega(15, 15))
        self.assertTrue(should_spawn_mega(30, 15))

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(20, 0, 10), 10)

    def test_collided(self):
        self.assertTrue(collided(0, 0, 10, 15, 0, 10))
        self.assertFalse(collided(0, 0, 10, 25, 0, 10))
        self.assertTrue(collided(0, 0, 10, 25, 0, 10, margin=5))


if __name__ == "__main__":
    unittest.main()
