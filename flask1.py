#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
import os


import subprocess
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/ls')
def ls_route():
    ls_result = subprocess.check_output(["ls", "-la"])
    ls_result_array = ls_result.decode().splitlines()
    return render_template('simple.html', text=ls_result_array)
    #### alternative version of ls()
    # ls_result = subprocess.check_output(["ls", "-la"])
    # ls_result_formatted = ls_result.decode().replace('\n', '<br>')
    # return ls_result_formatted

@app.route('/cd')
def cd_route():
    dir_to_cd = request.args.get('to', default = '')
    if os.path.isdir(dir_to_cd):
       os.chdir(dir_to_cd)
       return "Looks ok"
    else:
        return "No such dir"
