import unittest
import yaml

from algorithm import graph, dimensions
from utils.dbpedia_access import DBpedia


class InitGraphTestCase(unittest.TestCase):
    def setUp(self):
        with open("config.yaml", 'r') as ymlfile:
            self.config = yaml.load(ymlfile)

        self.dist_fct = getattr(graph, self.config['graph-setup']['dist-function'])

        self.features = None
        if self.dist_fct == graph.euclid_dist:
            self.features = getattr(dimensions, self.config['graph-setup']['feature-vector'])


    def test_single_prop_graph(self):
        dbp = DBpedia()
        p = graph.Property('<http://dbpedia.org/ontology/width>', dir=self.config['local-files'])
        subjects = dbp.get_subjects_by_predicate(graph._normalize_uri(p.prop))

        g = graph.PropertyGraph(p, subjects, p.filename, min_instances=self.config['graph-setup']['nodes']['min'])
        g.build_type_hierarchy()

        g.branching(
            features=self.features,
            dist_function=self.dist_fct,
            min_instances=self.config['graph-setup']['nodes']['min'],
            max_instances=self.config['graph-setup']['nodes']['max'],
            normalize=self.config['graph-setup']['normalize-dist']
        )
        g.single_element_values()


if __name__ == '__main__':
    unittest.main()
