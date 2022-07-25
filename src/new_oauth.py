# !/usr/bin/python3
# -*- coding: utf-8 -*-
#-*-coding:gb2312-*-
"""Run small webservice for oath."""
import json, time
import sys
from pathlib import Path
import os
import os.path
import pathlib2 as pathlib
import socket
from actions import say_save
from requests_oauthlib import OAuth2Session
from google.oauth2.credentials import Credentials
from google.assistant.library.file_helpers import existing_file
host_name = socket.gethostname()
h=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host_addr = ''
try:
    host_addr = socket.gethostbyname(host_name + ".local")
    h.connect(("8.8.8.8", 80))
except:
    host_addr = h.getsockname()[0]
say_save('Cần phải đăng kí lại với Google tại địa chỉ: '+host_addr+'hai chấm 5002')
ROOT_PATH = os.path.realpath(os.path.join(__file__, '..', '..'))
USER_PATH = os.path.realpath(os.path.join(__file__, '..', '..','..'))
env = USER_PATH+'/env/bin/python -m pip install '
oauth_json = os.path.join(os.path.expanduser('~/'),'ViPi','vipi.json')
data = {"installed":{"client_id":"id","project_id":"project_id","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"secret","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
config_file = '/home/pi/ViPi/src/config.yaml'
cred_file = os.path.join(os.path.expanduser('~/.config'),'google-oauthlib-tool','credentials.json')
cred_dir =  os.path.join(os.path.expanduser('~/.config'),'google-oauthlib-tool')
if os.path.exists(oauth_json)==False:
    with open  (oauth_json,"w") as f:
        json.dump(data,f,ensure_ascii=False,indent=4)
with open(oauth_json,'r') as data:
    user_data = json.load(data)['installed']
oauth2 = OAuth2Session(
        user_data['client_id'],
        redirect_uri='urn:ietf:wg:oauth:2.0:oob',
        scope=["https://www.googleapis.com/auth/assistant-sdk-prototype", "https://www.googleapis.com/auth/gcm"]
    )
auth_url, _ = oauth2.authorization_url(user_data['auth_uri'], access_type='offline', prompt='consent')  
from flask import Flask, request, jsonify, render_template
from flask_restful import Resource, Api
from flask_bootstrap import Bootstrap
app = Flask(__name__)
api = Api(app)
Bootstrap(app)
@app.route('/')
def index():
   return render_template('upload.html',url = auth_url)

@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    try:
        if request.method == 'POST':
            f = request.files['file']
            f.save(oauth_json)
            upload = 'Đã upload thành công'
    except:
            upload  = 'Upload không thành công'
    return render_template('upload.html',url = auth_url, upload = upload)
@app.route('/token', methods = ['POST'])
def token():
    token = request.form['token']
    oauth2.fetch_token(user_data['token_uri'], client_secret=user_data['client_secret'], code=token)
    credentials = Credentials(
        oauth2.token['access_token'],
        refresh_token=oauth2.token.get('refresh_token'),
        token_uri=user_data['token_uri'],
        client_id=user_data['client_id'],
        client_secret=user_data['client_secret'],
        scopes=oauth2.scope
    )
    pathlib.Path(os.path.dirname(cred_dir)).mkdir(exist_ok=True)
    pathlib.Path(os.path.dirname(cred_file)).mkdir(exist_ok=True)
    with open(cred_file,'w') as json_file:
        json.dump({
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        },json_file)
    say_save('Đã đăng kí thành công với Google. Hệ thống tự khởi động lại sau 1 phút, vui lòng chờ.')
    #os.system('sudo supervisorctl reload')
    result = 'Đã hoàn thành'
    time.sleep(5)
    os.system('sudo reboot')
    return render_template('upload.html',url = auth_url, result = result)

@app.route('/config', methods=['GET', 'POST'])
def config():
    import yaml, json
    """Renders index page to edit provided yaml file."""
    with open(config_file) as file_obj:
        data = yaml.load(file_obj, Loader=yaml.Loader)
    return render_template('yaml.html',
                           data=json.dumps(data),
                           change_str='#CHANGE_ME')

@app.route('/tree', methods=['GET', 'POST'])
def tree():
    import yaml, json
    """Renders tree view page to edit provided yaml file."""
    with open(config_file) as file_obj:
        data = yaml.load(file_obj, Loader=yaml.Loader)
    return render_template('treeyaml.html',
                           data=data, datastr=json.dumps(data),
                           change_str='#CHANGE_ME')

@app.route('/save', methods=['POST'])
def save():
    import yaml, json
    """Save current progress on file."""
    out = request.json.get('yaml_data')
    with open(config_file, 'w') as file_obj:
        yaml.dump(out, file_obj, default_flow_style=False)
    return "Data saved successfully!"

@app.route('/saveExit', methods=['POST'])
def save_exit():
    import yaml, json
    """Save current progress on file and shuts down the server."""
    out = request.json.get('yaml_data')
    with open(config_file, 'w') as file_obj:
        yaml.dump(out, file_obj, default_flow_style=False)
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return "Saved successfully, Shutting down app! You may close the tab!"

@app.errorhandler(404)
def page_not_found(e):
    """Serves 404 error."""
    return '<h1>404: Page not Found!</h1>'
app.run(host='0.0.0.0',port=5002)