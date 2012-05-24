import unittest
import models


class TestModelsHandler(unittest.TestCase):
    """ModelsHandler Tests"""

    def setUp(self):
        self.models_handler = models.ModelsHandler()


    def test_create_new_user(self):
        pass

if __name__ == '__main__':
    #VERBOSITY = util.verbosity_helper()
    VERBOSITY = 1

    SUITE = unittest.TestLoader().loadTestsFromTestCase(
            TestModelsHandler)
    unittest.TextTestRunner(verbosity=VERBOSITY).run(SUITE)
