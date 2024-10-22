# Multi-level Semantic Labelling of Numerical Values
> *Sebastian Neumaier, Jürgen Umbrich, Josiane Xavier Parreira, and Axel Polleres*.
> In Proceedings of the 15th International Semantic Web Conference (ISWC 2016), Kobe, Japan, October 2016. [[ pdf ](http://polleres.net/publications/neum-etal-2016ISWC.pdf)]


We apply a hierarchical clustering over information taken from DBpedia to build a background knowledge graph of possible “semantic contexts” for bags of numerical values, over which we perform a nearest neighbour search to rank the most likely candidates.

## Setup
The total setup-time for all 50 properties in props.csv takes 15-30 minutes and ~20GB of RAM.
In order to test the system without this extreme built time and requirements use only a small subset of properties with a lower number of corresponding subjects.

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
* `$ tar -xzf local/common_types.tar.gz -C local`
* `$ cat local/subjects.tar.gz.* | tar xzvf - -C local`
* Run API service
* `$ ./runner -h`  to show help
* `$ ./runner -c config.yaml`  to start the API service
* Example curl request:
* `$ curl -X POST -F csv=@testfile/stadiums.csv http://localhost:8081/labelling?column=2`
