import argparse
import logging
import os
import hashlib

import yaml
from flask import Flask, request, redirect, url_for, jsonify, flash, render_template
from werkzeug.utils import secure_filename

import labeller
from labeller import NumLabeller


app = Flask(__name__)

def parse_text(text_input):
    token = []
    rows = text_input.split('\n')
    for r in rows:
        for t in r.split(' '):
            tmp = t.strip()
            if tmp:
                token.append(tmp)
    nums = [float(n) for n in token]
    return nums


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            print file.read()

            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@app.route('/labelling')
def input():
    # get args
    filename = request.args.get('filename')
    if not filename:
        return '''
        <!doctype html>
        <title>Filename not allowed</title>
        <h1>Filename not allowed!</h1>
        '''
    filename = secure_filename(filename)
    num_of_neighbours = int(request.args.get('neighbours'))
    try:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename)) as f:
            data = parse_text(f.read())
    except Exception as e:
        return '''
        <!doctype html>
        <title>Input Error</title>
        <h1>Error while parsing input!</h1>
        <p>''' + e.message + '</p>'

    neighbors = app.config['LABELLER'].get_candidates(data, num_of_neighbours)
    label_maj = labeller.label_prediction(neighbors)
    label_avg = labeller.label_prediction(neighbors, mode='avg')

    type_maj = labeller.type_prediction(neighbors, mode='maj')
    type_avg = labeller.type_prediction(neighbors, mode='avg')

    response = {
        'values': data,
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
    #num_labeller = NumLabeller(props, config)
    #app.config['LABELLER'] = num_labeller
    print 'graphs loaded'
    logging.info("Server running: http://localhost:"+str(config['api']['port']))
    app.run(threaded=True, port=config['api']['port'], host='0.0.0.0')
