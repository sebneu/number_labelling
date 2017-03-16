import argparse
import logging
import os
import hashlib

import anycsv
import flask
import yaml
from flask import Flask, request, redirect, url_for, jsonify, flash, render_template
from werkzeug.utils import secure_filename

import labeller
from labeller import NumLabeller


app = Flask(__name__)
app.secret_key = "multi-level labelling"

def parse_data(values):
    nums = []
    missing = []
    for v in values:
        try:
            n = float(v)
            nums.append(n)
        except:
            missing.append(v)
    return nums, missing


def isInt(value):
  try:
    int(value)
    return True
  except:
    return False


def get_response(values, neighbours):
    data, invalid = parse_data(values)
    neighbors = app.config['LABELLER'].get_candidates(data, neighbours)
    label_maj = labeller.label_prediction(neighbors)
    label_avg = labeller.label_prediction(neighbors, mode='avg')

    type_maj = labeller.type_prediction(neighbors, mode='maj')
    type_avg = labeller.type_prediction(neighbors, mode='avg')

    response = {
        'values': data,
        'invalid': invalid,
        'neighbours': [[str(n[0]), round(n[1], 4)] for n in neighbors],
        'labelling': {
            'property': {
                'maj': [[str(l[0]), round(l[1], 4)] for l in label_maj],
                'avg': [[str(l[0]), round(l[1], 4)] for l in label_avg]
            },
            'type': {
                'maj': [[str(l[0]), round(l[1], 4)] for l in type_maj],
                'avg': [[str(l[0]), round(l[1], 4)] for l in type_avg]
            }
        }
    }
    return jsonify(response)


@app.route('/labelling', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'csv' in request.files:
            # get number of neighbours, default=10
            neighbours = request.args.get('neighbours', '10')
            if not isInt(neighbours):
                flash('Invalid number of neighbours. Use "neighbours={count}". Default is 10.')
                flask.abort(422, '\n'.join(flask.get_flashed_messages()))
            column = request.args.get('column', '0')
            if not isInt(column):
                flash('Invalid column index specified. Use "column={index}" parameter. Default is 0')
                flask.abort(422, '\n'.join(flask.get_flashed_messages()))
            file = request.files['csv']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                flash('No selected file')
                flask.abort(400, '\n'.join(flask.get_flashed_messages()))
            if file:
                #filename = secure_filename(file.filename)
                reader = anycsv.reader(content=file.read())
                values = [r[int(column)] for r in reader]
                return get_response(values=values, neighbours=int(neighbours))

        flash('Use "csv" parameter to specify file')
    return flask.abort(400, '\n'.join(flask.get_flashed_messages()))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="config file")
    parser.add_argument("--logfile", help="log output to file")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    # setup logging
    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO
    if args.logfile:
        logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(message)s', filename=args.logfile)
    else:
        logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(message)s')
    # setup upload folder
    UPLOAD_FOLDER = 'submitted/'
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    with open("config.yaml", 'r') as ymlfile:
        config = yaml.load(ymlfile)
    props = labeller.parse_props(config=config)
    num_labeller = NumLabeller(props, config)
    app.config['LABELLER'] = num_labeller
    logging.info("Finished branching. Graphs loaded in memory")
    logging.info("Service running at: http://localhost:"+str(config['api']['port'])+'/labelling')
    logging.info("Example curl request: curl -X POST -F csv=@/path/to/file.csv http://localhost:"+str(config['api']['port'])+"/labelling?column=1&neighbours=10")
    app.run(threaded=True, port=config['api']['port'], host='0.0.0.0')
