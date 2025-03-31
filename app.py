import os
import json
from flask import (
    Flask,
    render_template,
    request,
)
import sys
from azure.storage.blob import BlobClient

SAS = "?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2025-06-02T14:42:36Z&st=2025-03-31T06:42:36Z&spr=https,http&sig=J%2FnMxiP3xdt5N2evTxxRBfJwfGwRxPERs6%2BgELblqqc%3D"
### Imports for the ML models that the BTAP team developed
# import eegmodel
# from eegmodel import realtimeFromFile

subfolder_path = os.getcwd() + "/code/"
sys.path.insert(1, subfolder_path)
from running import airpod_running

app = Flask(__name__)


@app.route("/")
def index():
    print("Request for index page received")
    return render_template("index.html")


@app.route("/running_speed", methods=["POST"])
def running_speed():
    try:
        f = request.files["file"]
    except Exception as e:
        raise e
    try:
       
        speed_x, speed_y = airpod_running.predict(f)
        print("RESULT", speed_x)
        prediction_result = speed_x
        result_map = {}
        result_map["prediction_result"] = prediction_result
        json_obj = json.dumps(result_map)
        return json_obj

    except Exception as e:
        prediction_result = e
        result_map = {}
        result_map["prediction_result"] = e
        json_obj = json.dumps(result_map)
        return json_obj


def model_prediction(f):
    blob_name = f
    container_name = "datafiles"
    sas_token = SAS
    blob_url = (
        "https://cognitiveloadstorage.blob.core.windows.net"
        + "/"
        + container_name
        + "/"
        + blob_name
        + sas_token
    )
    client = BlobClient.from_blob_url(blob_url)
    # downloads the given blob to a empty csv file named temp.csv
    with open(file=os.path.join("temp.csv"), mode="wb") as sample_blob:
        download_stream = client.download_blob()
        sample_blob.write(download_stream.readall())

    speed_x, speed_y = airpod_running.predict("temp.csv")
    print("RESULT", speed_x)
    return str(speed_x)


# for the web interface to use
@app.route("/get_prediction_web", methods=["POST"])
def get_prediction_web():
    try:
        f = request.form.get("pfile")  # filename from the textbox
        prediction_result = model_prediction(f)
    except Exception as e:
        prediction_result = e
    return render_template("prediction.html", pred=prediction_result)


# for the web interface to use to upload files
@app.route("/recording_upload_web", methods=["POST"])
def recording_upload_web():
    print(request.files)
    f = request.files["file"]
    local_file_name = f.filename
    status = "Success"
    try:
        # uploads the file to eegfiles container in Azure
        blob_name = local_file_name
        container_name = "datafiles"
        sas_token = SAS
        blob_url = (
            "https://cognitiveloadstorage.blob.core.windows.net"
            + "/"
            + container_name
            + "/"
            + blob_name
            + sas_token
        )
        client = BlobClient.from_blob_url(blob_url)

        # Read the entire file as bytes and upload
        file_contents = f.read()

        if not file_contents:
            raise ValueError("File is empty or not read correctly")

        # Upload the file
        client.upload_blob(file_contents, overwrite=True)

    except Exception as e:
        status = e

    return render_template("upload.html", file_status=status)


### ENDPOINTS SPECIFICALLY FOR THE ANDROID VERSION:
# for the android interface to use
@app.route("/get_prediction_mobile", methods=["POST"])
def get_prediction_mobile():
    try:
        f = request.args.get("file")
        prediction_result = model_prediction(f)
        result_map = {}
        result_map["prediction_result"] = prediction_result
        json_obj = json.dumps(result_map)
        return json_obj

    except Exception as e:
        prediction_result = e
        result_map = {}
        result_map["prediction_result"] = "ERROR"
        json_obj = json.dumps(result_map)
        return json_obj


# # for the android interface to use to upload files
# @app.route("/recording_upload_mobile", methods=["POST"])
# def recording_upload_mobile():
#     print(request.files)
#     f = request.files["file"] #might need to change depending on how Android sends over the file
#     local_file_name = f.filename
#     status = "Success"
#     try:
#         # uploads the file to eegfiles container in Azure
#         blob_name = local_file_name
#         container_name = "datafiles"
#         sas_token = "?sv=2022-11-02&ss=bfqt&srt=co&sp=rwdlacupiytfx&se=2025-03-01T08:54:24Z&st=2024-02-15T00:54:24Z&spr=https,http&sig=LsxToIZpmS4YyA1CIRnnYKItaD6HXzStQIg12xL3fJE%3D"
#         blob_url = (
#             "https://cognitiveloadstorage.blob.core.windows.net"
#             + "/"
#             + container_name
#             + "/"
#             + blob_name
#             + sas_token
#         )
#         client = BlobClient.from_blob_url(blob_url)

#         client.upload_blob(f.read())
#         # Upload the created file
#     except Exception as e:
#         print(e)
#         status = "ERROR"

#     result_map = {}
#     result_map["upload_status"] = status
#     json_obj = json.dumps(result_map)
#     return json_obj

if __name__ == "__main__":
    app.run(port=8000)
