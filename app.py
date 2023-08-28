from flask import Flask
from flask import request
from flask import render_template
from flask import session

import onfido
from onfido.regions import Region
from onfido.exceptions import (OnfidoServerError,
                               OnfidoRequestError,
                               OnfidoInvalidSignatureError,
                               OnfidoTimeoutError,
                               OnfidoConnectionError,
                               OnfidoUnknownError)

import secrets
import os
import requests
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET')

@app.route("/init")
def receive_token():
    return render_template("init.html")

@app.route("/",  methods=['POST', 'GET'])
def authenticate():
    #print(session.get('token'))
    #print(request.method)

    if request.method == 'POST':
        session['token'] = request.form.get("token")
        session['workflow_id'] = request.form.get("workflow_id")
    else:
        if session.get('token') is None or session.get("workflow_id") is None:
            return render_template("error.html", error="token/workflow id not set")

    api = onfido.Api(session['token'], region=Region.EU)
    ret = create_applicant(api)
    if isinstance(ret, str):
        session["applicant_id"] = ret
        print("applicant_id", session["applicant_id"])

        request_body = {"applicant_id": session["applicant_id"], "referrer": "*"}
        token = api.sdk_token.generate(request_body)["token"]
        workflow_run_id = initiate_workflow(session["applicant_id"], session["workflow_id"])
        return render_template("view.html", token=token, applicant_id=session["applicant_id"], workflow_run_id=workflow_run_id)
    else:
        return render_template("error.html", error=ret)



def initiate_workflow(applicant_id, workflow_id):

    url = "https://api.eu.onfido.com/v3.6/workflow_runs"
    payload = json.dumps({
        "workflow_id": workflow_id,
        "applicant_id": applicant_id
    })
    headers = {
        'Authorization': f"Token token={session['token']}",
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response = json.loads(response.text)
    print("response---->", response)
    print(response["id"])
    return response["id"]



def create_applicant(api):

    applicant_details = {
        "first_name": "First name",
        "last_name": "Last name",
        "dob": "1984-01-01",
        "address": {
            "street": "Second Street",
            "town": "London",
            "postcode": "S2 2DF",
            "country": "GBR"
        }
    }
    try:
        applicant = api.applicant.create(applicant_details)
        return applicant['id']
    except OnfidoServerError:
        return OnfidoServerError
    except OnfidoRequestError:
        return OnfidoRequestError
    except OnfidoInvalidSignatureError:
        return OnfidoInvalidSignatureError
    except OnfidoTimeoutError:
        return OnfidoTimeoutError
    except OnfidoConnectionError:
        return OnfidoConnectionError
    except OnfidoUnknownError:
        return OnfidoUnknownError






