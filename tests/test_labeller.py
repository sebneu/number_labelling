import unittest

import yaml

from web.labeller import NumLabeller
from web import labeller


class LabellerTestCase(unittest.TestCase):
    def test_labeller(self):
        data = [1.78, 1.79, 1.80, 1.85, 1.83]
        num_of_neighbours = 10

        with open("config.yaml", 'r') as ymlfile:
            config = yaml.load(ymlfile)

        props = labeller.parse_props(config=config)
        num_labeller = NumLabeller(props, config)
        print num_labeller.get_candidates(data, num_of_neighbours)

if __name__ == '__main__':
    unittest.main()
