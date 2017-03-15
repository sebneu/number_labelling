from collections import defaultdict
import logging
from time import sleep
from SPARQLWrapper import SPARQLWrapper, JSON
import operator


class DBpedia(object):
    def __init__(self):
        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.sparql.setTimeout(500)
        self.sparql.setReturnFormat(JSON)

    def get_predicates(self):
        query = u" SELECT DISTINCT ?p WHERE {" \
                u" ?p a rdf:Property" \
                u"}" \
                u" ORDER BY ?p"
        return set(self._retrieve(query, ['p']))

    def get_subject_object_pairs(self, p):
        query = u" SELECT ?s ?o" \
                u" WHERE {{ ?s {0} ?o }}".format(p)
        return set(self._retrieve(query, ['s', 'o']))

    def get_predicate_object_pairs(self, s, filter_predicates=None):
        query = u" SELECT ?p ?o WHERE {{" \
                u" {0} ?p ?o ".format(s)

        if filter_predicates:
            query += u" MINUS {"
            for f in filter_predicates:
                query += u" {0} {1} ?o .".format(s, f)
            query += u"}"
        query += u" FILTER( !isLiteral(?o) ) "
        query += u"}"
        return self._retrieve(query, ["p", "o"])

    def most_common_types(self, prop, min_instances=50):
        types = defaultdict(int)
        query = u"SELECT ?t count(distinct ?s) AS ?c" \
                u" WHERE {{" \
                u" ?s {0} ?o;" \
                u"    a ?t" \
                u" FILTER(STRSTARTS(STR(?t), 'http://dbpedia.org/ontology'))" \
                u" }}" \
                u" GROUP BY ?t" \
                u" ORDER BY DESC(?c)".format(prop)
        for t, c in self._retrieve(query, ['t', 'c'], limit=50, filter=[lambda x: True, lambda x: int(x) > min_instances]):
            types[t] += int(c)

        types = sorted(types.items(), key=operator.itemgetter(1), reverse=True)
        return types

    def get_values_of_type(self, type, property):
        query = u"SELECT ?o" \
                u" WHERE {{" \
                u" ?s {0} ?o;" \
                u"    a {1}" \
                u" }}".format(property, type)
        return [x[0] for x in self._retrieve(query, ["o"])]

    def get_types(self, s):
        query = u"SELECT ?t" \
                u" WHERE {{" \
                u" {0} a ?t" \
                u" }}".format(s)
        return set([x[0] for x in self._retrieve(query, ['t'])])

    def get_subclasses(self, s):
        query = u"SELECT ?t" \
                u" WHERE {{" \
                u" ?t rdfs:subClassOf {0}" \
                u" }}".format(s)
        return set([x[0] for x in self._retrieve(query, ['t'])])

    def get_subjects_by_predicate(self, p):
        query = u"SELECT ?s" \
                u" WHERE {{" \
                u" ?s {0} ?o" \
                u" }}".format(p)
        return set([x[0] for x in self._retrieve(query, ['s'])])

    def get_subjects_by_predicate_type(self, p, t):
        query = u"SELECT ?s" \
                u" WHERE {{" \
                u" ?s a {0}." \
                u" ?s {1} ?o" \
                u" }}".format(t, p)
        return set([x[0] for x in self._retrieve(query, ['s'])])

    def get_subjects_by_predicate_object_type(self, p, o, t):
        query = u"SELECT ?s" \
                u" WHERE {{" \
                u" ?s a {0}." \
                u" ?s {1} {2}" \
                u" }}".format(t, p, o)
        return set([x[0] for x in self._retrieve(query, ['s'])])

    def get_triples_by_subject(self, s, literals=True):
        query = u" SELECT ?p ?o WHERE {"
        query += u" {0} ?p ?o ".format(s)
        if not literals:
            query += u" FILTER( !isLiteral(?o) ) "
        query += u"}"
        return self._retrieve(query, ['p', 'o'])

    def _retrieve(self, query, params, limit=5000, filter=None, retries=10):
        try:
            logging.debug('DBpedia query: ' + query)
            res = []
            offset = 0
            has_next = True
            while has_next:
                q = query + u" LIMIT {1} OFFSET {2}".format(property, limit, offset)

                self.sparql.setQuery(q)
                resp = self.sparql.query().convert()
                results = resp["results"]["bindings"]

                for result in results:
                    tup = [result[p]["value"] for p in params]
                    if filter:
                        if all([f(t) for t, f in zip(tup, filter)]):
                            res.append(tup)
                    else:
                        res.append(tup)

                offset += limit

                if len(res) < offset:
                    has_next = False

                if offset % 10000 == 0:
                    logging.debug('DBPedia results retrieved: ' + str(offset))

            return res
        except Exception as e:
            if retries > 0:
                logging.warning('DBpedia connection lost: ' + str(e) + '. Try again...(' + str(retries) + ')')
                sleep(20)
                return self._retrieve(query, params, limit, filter, retries - 1)
            logging.warning('DBpedia connection error: ' + str(e))
            raise e

