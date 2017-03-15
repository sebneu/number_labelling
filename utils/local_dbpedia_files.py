import itertools
import os
import logging
import pickle

def _store_local(data, filename):
    logging.debug('Store local: ' + filename)
    with open(filename, 'w') as f:
        pickle.dump(data, f)


def store_graph(g, filename):
    _store_local(g, filename + '_graph.pkl')


def local_graph(filename):
    with open(filename + '_graph.pkl', 'r') as f:
        return pickle.load(f)


def local_common_types(filename):
    with open(filename + '_common_types.pkl', 'r') as f:
        return pickle.load(f)
