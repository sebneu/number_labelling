import scipy
import operator

__author__ = 'sebastian'

import logging
from sklearn.neighbors import NearestNeighbors
from sklearn import preprocessing


class KNNClassifier:
    def __init__(self, X, nodes, normalize=True):
        self.normalize = normalize
        self.neigh = NearestNeighbors()
        self.X = X
        self.nodes = nodes
        if self.normalize:
            self.scaler = preprocessing.StandardScaler()
        self.fit()

    def fit(self):
        if self.normalize:
            self.scaler = self.scaler.fit(self.X)
            self.X = self.scaler.transform(self.X)
        self.neigh.fit(self.X)

    def getNeighbors(self, x, k):
        if self.normalize:
            x = self.scaler.transform([x])[0]
        logging.debug('get ' + str(k) + ' neighbors for feature vector ' + str(x))
        neighbors = []
        dist, indices = self.neigh.kneighbors(x)
        for i, x in enumerate(indices[0]):
            if i > k:
                break
            neighbors.append((self.nodes[x], dist[0][i]))
        return neighbors


class KolmogorovSmirnov:
    def __init__(self, X, nodes):
        self.X = X
        self.nodes = nodes

    def getNeighbors(self, x, k):
        distances = []
        for i in range(len(self.X)):
            dist, p = scipy.stats.ks_2samp(x, self.X[i])
            distances.append((self.nodes[i], dist))
        distances.sort(key=operator.itemgetter(1))
        neighbors = []
        for i in range(min(k, len(distances))):
            neighbors.append(distances[i])
        return neighbors