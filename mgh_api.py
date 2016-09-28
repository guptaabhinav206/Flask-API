import json
import flask
from flask import Flask, request, abort
from flask_cors import CORS
import requests
from pymongo import MongoClient
import uuid

app = Flask(__name__)
CORS(app)

client = MongoClient("localhost", 27017)
db = client['test_database']


@app.route('/', methods=['POST'])
def hello_world():
    abort(404)
    return 'nothing here'


@app.route('/workset/model', methods=['POST'])
def get_details():
    data = {k: v for k, v in request.form.items()}
    if not data:
        data = {k: v for k, v in request.json.items()}
    r = requests.post('http://52.41.115.78:8090/jobs?appName=MGHv1&classPath=jobserver.mlmodels.supervised.LinearRegressionMVPV1', data=json.dumps(data), headers={'content-type': 'application/json'})
    json_data = json.loads(r.content)
    json_data['display'] = False
    json_data['runId'] = "runId" + str(get_id())
    json_data['modelId'] = data['worksetId']+'lr'
    if not ("analytics_results" in db.collection_names()):
        db.create_collection('analytics_results')
    db.analytics_results.insert(json_data)
    print json_data
    del json_data["_id"]
    return flask.jsonify(json_data)


def get_id():
    #millis = int(round(time.time() * 1000))
    return uuid.uuid4()


@app.route('/save/model', methods=['POST'])
def save_results():
    data = {k: v for k, v in request.form.items()}
    if not data:
        data = {k: v for k, v in request.json.items()}
    #r = json.loads(requests.post('http://10.0.1.20:8090/jobs?appName=MGHv1&classPath=jobserver.mlmodels.supervised.LinearRegressionMVPV1&sync=true', json=data))
    run_id = data['runId']
    db.analytics_results.update({'runId': run_id}, {'$set': {'display': True}})
    data['display'] = True
    return flask.jsonify(data)


@app.route('/get/model', methods=['GET'])
def get_model():
    output = []
    result = {}
    workset_id = request.args.get('worksetId')
    model_id = request.args.get('modelId')
    if not ("analytics_results" in db.collection_names()):
        print 'collection not found'
    else:
        res = db.analytics_results.find({"worksetId" : str(workset_id), "modelId" : str(model_id), 'display': True})
        for items in res:
            try:
                del items["_id"]
            except KeyError:
                pass
            output.append(items)
            print items
    result["response"] = output
    return json.dumps(result)


@app.route('/job', methods=['GET'])
    def get_status():
        job_id = request.args.get('jobId')
        res = db.analytics_results.find_one({"result.jobId": job_id})
        model_id = res['modelId']
        r = requests.get(
            'http://52.41.115.78:8090/jobs/'+job_id, headers={'content-type': 'application/json'})
        json_data = json.loads(r.content)
        db.analytics_results.update({'jobId': job_id}, json_data)
        json_data['modelId'] = model_id
        return flask.jsonify(json_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
