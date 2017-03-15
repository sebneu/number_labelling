import logging
import math


def get_float(v):
    try:
        h = float(v)
        return h
    except Exception as e:
        try:
            if ',' in v and not '.' in v:
                v = v.replace(',', '.')
                return float(v)
        except Exception as e:
            return None

def get_value(v):
    try:
        # first try without strip
        x = get_float(v)
        if x:
            return x
        # now try if we can remove datatype description
        v = v.strip().strip('"').split('^^')[0].rstrip('"')
        return get_float(v)
    except Exception as e:
        return None

def get_numeric_values(values):
    res = []
    for v in values:
        x = get_value(v)
        if x != None:
            res.append(x)
    return res

def get_feature_vector(values, features):
    # apply feature functions
    features = [f(values) for f in features]
    if not any([math.isnan(x) for x in features]):
        return features
