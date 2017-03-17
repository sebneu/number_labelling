# Multi-level Semantic Labelling of Numerical Values
*Sebastian Neumaier, Jürgen Umbrich, Josiane Xavier Parreira, and Axel Polleres*

We apply a hierarchical clustering over information taken from DBpedia to build a background knowledge graph of possible “semantic contexts” for bags of numerical values, over which we perform a nearest neighbour search to rank the most likely candidates.

## Setup
* `$ git clone https://github.com/sebneu/number_labelling.git`
* `$ cd number_labelling`
* (optionally) setup virtual environment
* `$ virtualenv --system-site-packages labelling_env`
* `$ . labelling_env/bin/activate`
* Install [anycsv](https://github.com/sebneu/anycsv) CSV parser
* `$ pip install git+git://github.com/sebneu/anycsv.git`
* Install requirements 
* `$ python setup.py install`
* Setup local files
* `$ tar -xzf local/common_types.tar.gz`
* `$ tar -xzf local/subjects.tar.gz`
* Run API service
* `$ ./runner -h`  to show help
* `$ ./runner -c config.yaml`  to start the API service
* Example curl request:
* `$ curl -X POST -F csv=@/path/to/file.csv http://localhost:8081/labelling?column=1&neighbours=10`
