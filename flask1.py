#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from flask_pymongo import PyMongo
import os
import subprocess
import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/flask"
mongo = PyMongo(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/ls')
def ls_route():
    ls_result = subprocess.check_output(["ls", "-la"])
    ls_result_array = ls_result.decode().splitlines()
    add_history_event('ls ' + os.getcwd())
    return render_template('simple.html', text=ls_result_array)
    #### alternative version of ls()
    # ls_result = subprocess.check_output(["ls", "-la"])
    # ls_result_formatted = ls_result.decode().replace('\n', '<br>')
    # return ls_result_formatted

@app.route('/cd', methods=['GET', 'POST'])
def cd_route():
    if request.method == 'POST':
        #TA: Как вынести POST в отдельную функцию? можно ли без импорта?
        # или только пилить роутинг на методы? 
        dir_to_cd = request.form.get('to_dir')
        add_history_event('cd post ' + dir_to_cd)
        if os.path.isdir(dir_to_cd):
            try:
                os.chdir(dir_to_cd)
                return render_template('cd-result.html', text="Looks ok")
            except PermissionError:
                return render_template('cd-result.html', text="Permission Denied (chmod/chown)")
        else:
            return render_template('cd-result.html', text="No such dir: " + dir_to_cd)
    else:
        add_history_event('cd form opened')
        return render_template('cd-form.html')

@app.route('/history')
def mongo_route():
    add_history_event('history')
    history_to_show = get_all_history()
    return render_template('simple.html', text=history_to_show)

def add_history_event(action_done):
    current_timestamp = datetime.datetime.now().strftime("%s")
    mongo.db.history.insert_one({'timestamp': current_timestamp, 'command': action_done})

def get_all_history():
    received_history = mongo.db.history.find({})
    received_history_list = []
    for history_line in received_history:
        received_history_list.append(history_line["timestamp"] + ': ' + history_line["command"])
    return received_history_list
