from collections import defaultdict
import os
import math
import scipy
from sklearn import preprocessing
from utils.dbpedia_access import DBpedia
import logging
import feature_extraction
from utils.local_dbpedia_files import local_common_types


def euclideanDistance(x1, x2):
    distance = 0
    for a, b in zip(x1, x2):
        distance += pow((a - b), 2)
    return math.sqrt(distance)


def euclid_dist(candidates, node, features, normalize):
    # select candidate with longest distance
    p_features = feature_extraction.get_feature_vector(node.get_values(), features)
    if not p_features:
            return None
    if normalize:
        # normalize feature vector of selected node
        scaler = preprocessing.StandardScaler().fit([p_features])
        p_features = scaler.transform([p_features])[0]

    values = []
    for c in candidates[:]:
        c_values = c.get_values()
        if c_values:
            c_features = feature_extraction.get_feature_vector(c.get_values(), features)
            if normalize:
                c_features = scaler.transform([c_features])[0]
            values.append(euclideanDistance(p_features, c_features))
        else:
            candidates.remove(c)
    if not values:
        return None
    i = values.index(max(values))
    sel_node = candidates[i]
    return sel_node


def kolmogorov_dist(candidates, node, features, normalize):
    p_values = node.get_values()
    if not p_values:
            return None
    values = []
    for c in candidates[:]:
        c_values = c.get_values()
        if c_values:
            dist, p = scipy.stats.ks_2samp(p_values, c_values)
            values.append(dist)
        else:
            candidates.remove(c)
    if not values:
        return None
    i = values.index(max(values))
    sel_node = candidates[i]
    return sel_node

def add_values_to_nodes(leaves, prop, filename):
    logging.debug('Add values to nodes [' + filename + ']')
    res = []
    p = _normalize_uri(prop.prop)
    for l in leaves:
        # remove initial values
        l.values = set()
        s_p = set()
        for s in l.subjects:
            s = _normalize_uri(s)
            s_p.add((s, p))
        res.append((l, s_p))

    # iterate over file
    with open(filename + '_subjects') as f:
        c = 0
        for l in f:
            line = l.decode('utf8')
            x = line.split(' ')
            for l, s_p in res:
                if (x[0], x[1]) in s_p:
                    o = x[2].rstrip('\n')
                    o = o.rstrip('.')
                    v = feature_extraction.get_value(o)
                    if v != None:
                        l.values.add((x[0], v))
            c += 1
            if c % 100000 == 0:
                logging.debug('triples processed: ' + str(c)[:-3] + 'k')


def normalize_uris(X):
    res = set()
    for x in X:
        res.add(_normalize_uri(x))
    return res

def _normalize_uri(x):
    if not x.startswith('<'):
        x = u'<' + x + u'>'
    return x

def single_uri(x):
    return x.strip('<').rstrip('>')


class LocalDB():
    def __init__(self, local_files, min_instances):
        self.triples = self._load_triples(local_files, min_instances)

    def _load_triples(self, filename, min_instances):
        logging.debug('Load p-o pairs into memory')
        triples = defaultdict(set)
        shared = defaultdict(int)
        # iterate over file
        with open(filename + '_subjects') as f:
            c = 0
            for l in f:
                line = l.decode('utf8')
                x = line.split(' ')
                triples[x[0]].add((x[1], x[2]))
                shared[(x[1], x[2])] += 1
                # debug logging
                c += 1
                if c % 100000 == 0:
                    logging.debug('triples processed: ' + str(c)[:-3] + 'k')

        logging.debug('Filter p-o pairs with min instances (1)')
        for k, v in shared.items():
            if v < min_instances:
                del shared[k]

        logging.debug('Filter p-o pairs with min instances (2)')
        shared = set(shared.keys())
        del_set = []
        for s in triples:
            triples[s] &= shared
            if not triples[s]:
                del_set.append(s)
        for s in del_set:
            del triples[s]

        logging.debug('Finished loading p-o pairs')
        return triples

    def local_shared_property_object_pairs(self, subs):
        logging.debug('Find shared p-o pairs')
        res = defaultdict(set)
        # normalize subjects
        subjects = normalize_uris(subs)

        for s in subjects:
            if s in self.triples:
                for p, o in self.triples[s]:
                    if o.startswith('<'):
                        res[(p, o)].add(single_uri(s))
        return res



def info_msg(node):
    logging.debug('NODE: ' + str(node) + ', CHILDREN: ' + str(node.children))
    for c in node.children:
        info_msg(c)


class Property(object):
    def __init__(self, prop, dir):
        self.prop = _normalize_uri(prop)
        sp_name = self.prop.split('ontology/')
        self.name = sp_name[-1][:-1].replace('/', '_')

        self.filename = os.path.join(dir, self.name)

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)


class PropertyGraph(object):
    def __init__(self, prop, subjects, local_files, min_instances):
        self.prop = prop
        self.nodes = []
        self.roots = []
        self.leaves = []
        self.local_files = local_files
        self.subjects = subjects
        self.min_instances = min_instances
        self.local_db = LocalDB(self.local_files, min_instances)

    def build_type_hierarchy(self):
        kb = DBpedia()
        self._build_subclasses(kb)

        # add parent and children
        for c in self.nodes:
            if not c.parent:
                self.roots.append(c)
            else:
                # add potential parent subjects
                c.parent.subjects |= c.subjects
            if not c.children:
                self.leaves.append(c)

    def _build_subclasses(self, kb):
        res = local_common_types(self.local_files)
        for r in res:
            uri = r[0]
            # only add the subjects which are within the own subject set
            subjects = kb.get_subjects_by_predicate_type(self.prop.prop, u'<' + uri + u'>') & self.subjects
            if len(subjects) > self.min_instances:
                c = TypeNode(uri, subjects, self.prop)
                c.subclasses = kb.get_subclasses(c.get_uri())
                self.nodes.append(c)
        # build type hierarchy
        for t1 in self.nodes:
            for t2 in self.nodes:
                if t2 in t1:
                    t1.add_child(t2)
                    t2.add_parent(t1)

    def single_element_values(self):
        for node in self.nodes:
            # convert to single element lists
            vals = [x[1] for x in node.values]
            node.values = vals
            if vals:
                node.min = min(vals)
                node.max = max(vals)

    def _get_common_po_pairs(self, subjects):
        shared = self.local_db.local_shared_property_object_pairs(subjects)
        common_pairs = set([tup for tup in shared if len(shared[tup]) == len(subjects)])
        return common_pairs

    def _collect_candidates(self, node, min_instances, min_perc=1/100., max_perc=99/100.):
        # collect candidates for splitting
        candidates = []
        logging.debug('Collect candidates for splitting: ' + str(node))
        shared = self.local_db.local_shared_property_object_pairs(node.subjects)
        logging.debug('Split candidates in range: >' + str(max((1/100.) * node.instances, min_instances)))
        for tup in shared:
            subjects = shared[tup]
            if max(min_perc * node.instances, min_instances) < len(subjects) <= max_perc * node.instances:
                n = SharedPairs(node.uri, subjects, self.prop, tup)
                values = set()
                for s, v in node.values:
                    uri = s.lstrip('<').rstrip('>')
                    if uri in subjects:
                        values.add((s, v))
                n.values = values
                # check if there are enough numeric values in this node
                if len(n.get_values()) >= min_instances:
                    # additionally add all shared pairs of these subjects
                    n.common_pairs = self._get_common_po_pairs(n.subjects)
                    candidates.append(n)
        return candidates

    def _process_candidates(self, candidates, node, features, dist_function, min_instances, normalize):
        # check if we can split further
        if len(candidates) == 0:
            return None
        sel_node = dist_function(candidates, node, features, normalize=normalize)
        if not sel_node:
            return None
        candidates.remove(sel_node)
        # update other candidates
        for c in candidates[:]:
            if c.subjects & sel_node.subjects:
                candidates.remove(c)
        return sel_node

    def _update_candidates_by_existing_children(self, candidates, node):
        for child in node.children:
            for c in candidates:
                c.subjects -= child.subjects
                c.values -= child.values


    ################### SPLIT ON LONGEST FEATURE VECTOR DISTANCE, INSTANCES IN ALL NODES ############################
    def branching(self, features, dist_function, min_instances=50, max_instances=100, normalize=True):
        add_values_to_nodes(self.nodes, self.prop, self.local_files)

        for node in self.roots:
            logging.info('PROCESSING NODE: ' + str(node))
            self._branching(node, min_instances, max_instances, features, dist_function, normalize)
            info_msg(node)
        # update leaves
        self.leaves = []
        for c in self.nodes:
            if not c.children:
                self.leaves.append(c)

    def _branching(self, node, min_instances, max_instances, features, dist_function, normalize):
        candidates = self._collect_candidates(node, min_instances)
        self._update_candidates_by_existing_children(candidates, node)

        while True:
            sel_node = self._process_candidates(candidates, node, features, dist_function, min_instances, normalize)
            if not sel_node:
                break
            # update parent node
            logging.debug('ADD NODE: ' + str(sel_node))

            # update original node
            node.add_child(sel_node)
            sel_node.add_parent(node)
            self.nodes.append(sel_node)

        for c in node.children:
            # split selected node recursively
            self._branching(c, min_instances, max_instances, features, dist_function, normalize)


class TypeNode(object):
    def __init__(self, t, subjects, property):
        self.property = property
        self.children = []
        self.parent = None
        self.subjects = subjects
        self.uri = t
        self.subclasses = []
        self.values = set()
        self.weight = 1.
        self.features = None

    def get_path(self):
        if self.parent:
            res = self.parent.get_path()
            res.append(self.uri)
            return res
        else:
            return [self.uri]

    @property
    def instances(self):
        return len(self.subjects)

    def split(self, n):
        self.add_child(n)
        self.subjects -= n.subjects
        self.values -= n.values
        n.add_parent(self)

    def add_parent(self, p):
        if self.parent and p != self.parent:
            logging.warning('node ' + str(self) + ' has already a parent node assigned')
        else:
            self.parent = p

    def add_child(self, c):
        self.children.append(c)
        for x in self.children:
            x.weight = self.weight/len(self.children)

    def get_uri(self):
        return u'<' + self.uri + u'>'

    def is_subclass(self, t):
        return t.uri in self.subclasses

    def __contains__(self, t):
        return self.is_subclass(t)

    def __repr__(self):
        return self.uri.split('/')[-1].replace('/', '_') + '[' + str(self.property) + ']'

    def extract_testdata(self, percent):
        count = percent * self.instances

        res_data = set()
        res_subj = set()
        i = 0
        #random.shuffle(self.values)
        while i < count:
            v = self.values.pop()
            uri = single_uri(v[0])
            self.subjects.discard(uri)
            res_subj.add(uri)
            res_data.add(v)
            i += 1
        n = TestData(self.uri, res_subj, self.property)
        n.parent = self
        n.values = res_data
        return n

    def get_values(self):
        return [x[1] for x in self.values]

class SharedPairs(TypeNode):
    def __init__(self, t, subjects, property, predicate_object):
        super(SharedPairs, self).__init__(t, subjects, property)
        self.predicate_object = predicate_object

    def get_path(self):
        if self.parent:
            res = self.parent.get_path()
            res.append(self.predicate_object)
            return res
        else:
            return [self.predicate_object]

    def __repr__(self):
        if self.parent:
            return self.parent.__repr__() + '>' + get_pair_repr(self.predicate_object)
        else:
            return get_pair_repr(self.predicate_object)

class Rest(TypeNode):
    def __init__(self, t, subjects, property, predicate_object=('REST>', '')):
        super(Rest, self).__init__(t, subjects, property)
        self.predicate_object = predicate_object

    def get_path(self):
        if self.parent:
            res = self.parent.get_path()
            res.append(self.predicate_object)
            return res
        else:
            return [self.predicate_object]

    def __repr__(self):
        if self.parent:
            return self.parent.__repr__() + '>NOT' + get_pair_repr(self.predicate_object)
        else:
            return 'NOT' + get_pair_repr(self.predicate_object)

class TestData(TypeNode):
    def __init__(self, t, subjects, property):
        super(TestData, self).__init__(t, subjects, property)

    def get_path(self):
        return self.parent.get_path()

    def __repr__(self):
        if self.parent:
            return 'TESTDATA: ' + self.parent.__repr__()
        else:
            return 'TESTDATA'


def get_pair_repr(pair):
    return '(' + pair[0].split('/')[-1].replace('/', '_')[:-1] + '|' + pair[1].split('/')[-1].replace('/', '_')[:-1] + ')'


