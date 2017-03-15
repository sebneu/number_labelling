import csv
import logging
from collections import defaultdict

from algorithm import graph, dimensions
from algorithm.algorithms import KolmogorovSmirnov
from utils.dbpedia_access import DBpedia


def parse_props(config):
    propfile = config['properties']
    props = []
    with open(propfile, 'r') as f:
        csvr = csv.reader(f)
        for row in csvr:
            props.append(row[0])
    return [graph.Property(prop, dir=config['local-files']) for prop in props]


class NumLabeller():
    def __init__(self, props, config):
        self. config = config
        self.dist_fct = getattr(graph, self.config['graph-setup']['dist-function'])
        self.features = None
        if self.dist_fct == graph.euclid_dist:
            self.features = getattr(dimensions, self.config['graph-setup']['feature-vector'])

        dbp = DBpedia()
        self.graphs = {}
        for p in props:
            logging.info('Collecting all subjects for property: ' + p.name)
            subjects = dbp.get_subjects_by_predicate(graph._normalize_uri(p.prop))

            logging.info('Build property graph: ' + p.name)
            g = graph.PropertyGraph(p, subjects, p.filename, min_instances=self.config['graph-setup']['nodes']['min'])
            g.build_type_hierarchy()
            logging.info('Branching for property graph: ' + p.name)
            g.branching(
                features=self.features,
                dist_function=self.dist_fct,
                min_instances=self.config['graph-setup']['nodes']['min'],
                max_instances=self.config['graph-setup']['nodes']['max'],
                normalize=self.config['graph-setup']['normalize-dist']
            )
            g.single_element_values()
            self.graphs[p] = g

    def get_candidates(self, values, k):
        return ks_classify(values, self.graphs, k)


def ks_classify(values, graphs, k):
    X = []
    nodes = []
    for p in graphs:
        graph = graphs[p]
        for n in graph.nodes:
            if n.instances > 0:
                v = n.values
                if v and in_range(values, n):
                    X.append(v)
                    nodes.append(n)
    ks_test = KolmogorovSmirnov(X, nodes)
    return ks_test.getNeighbors(values, k)


def in_range(values, x):
    if not hasattr(x, 'max') or not hasattr(x, 'min'):
        logging.error('Node has no min or max attribute: ' + str(x))
        return False
    if min(values) > x.max or max(values) < x.min:
        return False
    else:
        return True


def label_prediction(neighbors, mode='maj'):
    labels = defaultdict(list)

    for i, n in enumerate(neighbors):
        labels[n[0].property].append(n[1])
    if mode == 'maj':
        list_len = [(prop, len(labels[prop])) for prop in labels]
        prediction = sorted(list_len, key=lambda x: x[1], reverse=True)
    else:
        dists = [(prop,  sum(labels[prop])/float(len(labels[prop])) ) for prop in labels]
        prediction = sorted(dists, key=lambda x: x[1])
    return prediction


def type_prediction(neighbors, mode='maj', parent_type='all'):
    # recursive function for adding parent types
    def _get_all_types(n, d, types):
        types[n.uri + ' (' + str(n.property) + ')'].append(d)
        if n.parent:
            _get_all_types(n.parent, d, types)

    def _get_parent_type(n):
        if n.parent:
            return _get_parent_type(n.parent)
        else:
            return n.uri

    types = defaultdict(list)
    for i, n in enumerate(neighbors):
        if parent_type == 'all':
            _get_all_types(n[0], n[1], types)
        elif parent_type == 'parent':
            t = _get_parent_type(n[0])
            types[t].append(n[1])
        else:
            t = n[0].uri
            types[t].append(n[1])

    if mode == 'maj':
        list_len = [(t, len(types[t])) for t in types]
        prediction = sorted(list_len, key=lambda x: x[1], reverse=True)
    else:
        dists = [(t, sum(types[t]) / float(len(types[t]))) for t in types]
        prediction = sorted(dists, key=lambda x: x[1])
    return prediction
