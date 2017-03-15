import numpy as np

FV1 = [min, max, np.mean, np.std]
FV2 = [lambda x: np.percentile(x, 5), lambda x: np.percentile(x, 95), np.mean, np.std]
