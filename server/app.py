from flask import Flask, jsonify, request
# make cross-origin requests -- e.g., requests that originate from a different protocol, IP address, domain name, port
from flask_cors import CORS
import os
import json


# import data processing module
dataProcessing = __import__('dataProcessing')

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)


# enable CORS - Cross-Origin Resource Sharing
CORS(app)


nfix = 4
# =========================================================
# ================ for prepared model =====================
# =========================================================
@app.route('/precom', methods=['POST'])
def com_pre():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.combination_data(N, nfix, para)


@app.route('/presense', methods=['POST'])
def sen_pre():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.data_prereading(N, nfix, t)


@app.route('/combinations', methods=['POST'])
def com_data():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    if req_data['variables']:
        inputlist = req_data['variables']
    else: 
        inputlist = None

    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.combination_data(N, nfix, para, inputlist)


@app.route('/sense', methods=['POST'])
def sen_data():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    if req_data['variables']:
        inputlist = req_data['variables']
    else: 
        inputlist = None

    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.data_reading(N, nfix, t, inputlist)


# =========================================================
# ================ for uploaded model =====================
# =========================================================

@app.route('/premodelcom', methods=['POST'])
def com_model_pre():
    file = request.files['file']
    filename = file.filename

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.combination_data(N, nfix, para)


@app.route('/premodelsense', methods=['POST'])
def sen_model_pre():
    file = request.files['file']
    filename = file.filename

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.data_prereading(N, nfix, t)


@app.route('/modelcom', methods=['POST'])
def com_model():
    file = request.files['file']
    filename = file.filename
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.combination_data(N, nfix, para, inputlist)


@app.route('/modelsense', methods=['POST'])
def sen_model():
    file = request.files['file']
    filename = file.filename
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    return dataProcessing.data_reading(N, nfix, t, inputlist)


# =========================================================
# ========= for special model - get fire spread ===========
# =========================================================
@app.route('/prefirecom', methods=['POST'])
def firecom_pre():
    file = request.files['file']
    filename = file.filename

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()
    para = [axes[n]['name'] for n in range(N)]

    return dataProcessing.combination_data(N, nfix, para)


@app.route('/prefiresense', methods=['POST'])
def firesen_pre():
    file = request.files['file']
    filename = file.filename

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()
    para = [axes[n]['name'] for n in range(N)]

    return dataProcessing.data_prereading(N, nfix, t)


@app.route('/firecom', methods=['POST'])
def firecom_data():
    file = request.files['file']
    filename = file.filename
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()
    para = [axes[n]['name'] for n in range(N)]

    return dataProcessing.combination_data(N, nfix, para, inputlist)


@app.route('/firesense', methods=['POST'])
def firesen_data():
    file = request.files['file']
    filename = file.filename
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()

    return dataProcessing.data_reading(N, nfix, t, inputlist)


if __name__ == '__main__':
    app.run()
