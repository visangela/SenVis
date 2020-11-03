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


# @app.route( '/get-post-data', methods=['POST'] )
# def postRequest():
#    k = int(request.get_json()['k'])
#    resp = np.random.uniform(0, 10, k)
#    print(resp.nbytes/1000000)
#    return make_response(jsonify(dict(data=resp.tolist())))


# @app.route('/ping', methods=['GET'])
# def ping_pong():
#     return jsonify('pong!')


# =========================================================
# ================ for prepared model =====================
# =========================================================
@app.route('/precom', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def com_pre():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)
    print (para)

    nfix = 4

    return dataProcessing.combination_data(N, nfix, para)


@app.route('/presense', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def sen_pre():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)
    print (para)

    nfix = 4

    return dataProcessing.data_prereading(N, nfix, t)


@app.route('/combinations', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def com_data():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    if req_data['variables']:
        inputlist = req_data['variables']
    else: 
        inputlist = None
    print(inputlist)
    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)

    nfix = 4

    return dataProcessing.combination_data(N, nfix, para, inputlist)


@app.route('/sense', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def sen_data():
    # if request.method == "POST":
    req_data = request.get_json()
    case = req_data['currentcase']
    if req_data['variables']:
        inputlist = req_data['variables']
    else: 
        inputlist = None
    print(inputlist)
    functionn, axes = dataProcessing.functional(case)
    N, t, para = dataProcessing.data_processing(functionn, axes)

    nfix = 4

    return dataProcessing.data_reading(N, nfix, t, inputlist)


# =========================================================
# ================ for uploaded model =====================
# =========================================================

@app.route('/premodelcom', methods=['POST'])
def com_model_pre():
    file = request.files['file']
    filename = file.filename
    print(filename)

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    nfix = 4

    return dataProcessing.combination_data(N, nfix, para)


@app.route('/premodelsense', methods=['POST'])
def sen_model_pre():
    file = request.files['file']
    filename = file.filename
    print(filename)

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    nfix = 4

    return dataProcessing.data_prereading(N, nfix, t)


@app.route('/modelcom', methods=['POST'])
def com_model():
    file = request.files['file']
    filename = file.filename
    print(filename)
    # inputdata = request.form['json']
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']
    print(inputlist)

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)


    nfix = 4

    return dataProcessing.combination_data(N, nfix, para, inputlist)


@app.route('/modelsense', methods=['POST'])
def sen_model():
    file = request.files['file']
    filename = file.filename
    print(filename)
    # inputdata = request.form['json']
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']
    print(inputlist)

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    functionn, axes = model.get_model()
    N, t, para = dataProcessing.data_processing(functionn, axes)

    nfix = 4

    return dataProcessing.data_reading(N, nfix, t, inputlist)


# =========================================================
# ========= for special model - get fire spread ===========
# =========================================================
@app.route('/prefirecom', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def firecom_pre():
    file = request.files['file']
    filename = file.filename
    print(filename)

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()
    para = [axes[n]['name'] for n in range(N)]

    nfix = 4

    return dataProcessing.combination_data(N, nfix, para)


@app.route('/prefiresense', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def firesen_pre():
    file = request.files['file']
    filename = file.filename
    print(filename)

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()
    para = [axes[n]['name'] for n in range(N)]


    nfix = 4

    return dataProcessing.data_prereading(N, nfix, t)


@app.route('/firecom', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def firecom_data():
    file = request.files['file']
    filename = file.filename
    print(filename)
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()
    para = [axes[n]['name'] for n in range(N)]

    nfix = 4

    return dataProcessing.combination_data(N, nfix, para, inputlist)


@app.route('/firesense', methods=['POST'])
# @cross_origin(origin='*', headers=['Content-Type','Authorization'])
def firesen_data():
    file = request.files['file']
    filename = file.filename
    print(filename)
    inputdata = request.form['json']
    inputlist = json.loads(inputdata)
    inputlist = inputlist['variables']

    modelname = os.path.splitext(filename)[0]

    model = __import__(modelname)
    N, t, axes = model.get_model()


    nfix = 4

    return dataProcessing.data_reading(N, nfix, t, inputlist)


if __name__ == '__main__':
    app.run()
