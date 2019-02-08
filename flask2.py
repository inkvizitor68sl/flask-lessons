#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from flask_pymongo import PyMongo
import os
import subprocess
import datetime
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from git import Repo
from flask_wtf import Form
from wtforms import TextField, BooleanField
from wtforms import SelectField
from wtforms.validators import Required
import paramiko




app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/flask"
mongo = PyMongo(app)
bootstrap = Bootstrap(app)
nav = Nav(app)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


# temporary global vars, will be stored in mongo in future
local_repo_path = "/home/inky/projects/flask-lessons/deploy"
app.config.update(dict(
    CSRF_ENABLED = True,
    SECRET_KEY = 'asfhu89qwojrnbuqi091j24124'
    ))
app_to_deploy = {'app_name': 'Test App', 'deploy_module': 'git', 'build_module': 'git',
'stages': {'test': 'test_app_test_server', 'prod': 'test_app_prod_server'}}
server_list = {'test_app_test_server': {'host': '::1', 'dir': '/var/www/test'}, 
'test_app_prod_server': {'host': '::1', 'dir': '/var/www/prod'}}

#####

@nav.navigation()
def mynavbar():
    return Navbar(
        'Foobar',
        View('index', 'hello_world'),
        View('history', 'history_route'),
        View('ls', 'ls_route'),
        View('cd', 'cd_route_form'),
        View('git', 'git_route_get')
    )

@app.route('/')
def hello_world():
    return render_template('simple.html', text_line='Hello, world!')

@app.route('/ls')
def ls_route():
    ls_result = subprocess.check_output(["ls", "-la"])
    ls_result_array = ls_result.decode().splitlines()
    add_history_event('ls ' + os.getcwd())
    return render_template('simple.html', text=ls_result_array)

@app.route('/cd', methods=['POST'])
def cd_route():
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

@app.route('/cd', methods=['GET'])
def cd_route_form():
    add_history_event('cd form opened')
    return render_template('cd-form.html')

@app.route('/history')
def history_route():
    add_history_event('history')
    history_to_show = get_all_history()
    return render_template('simple.html', text=history_to_show)

@app.route('/git', methods=['POST'])
def git_route_post():
    git_has_to_deploy = request.form.get('gitcommit_choice').split()[0]
    stage_to_deploy = request.form.get('stage_choice')
    data_from_deploy = module_deploy_git(stage_to_deploy, git_has_to_deploy)
    text_from_deploy = data_from_deploy.decode().splitlines()
    print(data_from_deploy)
    print('asfasf')
    print (text_from_deploy, type(text_from_deploy))
    type(text_from_deploy)
    return render_template('simple.html', text=text_from_deploy)

@app.route('/git', methods=['GET'])
def git_route_get():
    commit_list = list_git_commits()
    stages_list = list_stages_for_app()
    git_form = GitDeployForm()
    git_form.gitcommit_choice.choices = [(g, g) for g in commit_list]
    git_form.stage_choice.choices = [(i, i) for i in stages_list.keys()]
    print(stages_list)
    print(type(stages_list))
    #print(list_stages_for_app())
    return render_template('git-form.html', text=commit_list, form = git_form)

def add_history_event(action_done):
    current_timestamp = datetime.datetime.now().strftime("%s")
    mongo.db.history.insert_one({'timestamp': current_timestamp, 'command': action_done})

def get_all_history():
    received_history = mongo.db.history.find({})
    received_history_list = []
    for history_line in received_history:
        received_history_list.append(history_line["timestamp"] + ': ' 
            + history_line["command"])
    return received_history_list

def list_git_commits():
    # using print as logging for a while
    repo_path = local_repo_path
    commits_limit = 20
    gitrepo = Repo(repo_path)
    commits_list = []
    if not gitrepo.bare:
        print('Repo at {} successfully loaded.'.format(repo_path))
        #print_repository(gitrepo)
        commits = list(gitrepo.iter_commits('master'))
        for commit in commits:
            commit_string = str(commit.hexsha) + ' ' + str(commit.summary)
            commits_list.append(commit_string)
            #print(str(commit.hexsha))
            pass
    else:
        print('Could not load repository at {} :('.format(repo_path))
    return commits_list[:commits_limit]

def list_stages_for_app():
    # mongo will be there
    return app_to_deploy['stages']

def module_deploy_git(stage, git_hash):
    stage_server_params = get_server_by_stage(stage)
    stage_server_params_str = str(stage_server_params)
    ssh_host = stage_server_params['host']
    ssh_directory = stage_server_params['dir']
    ssh.connect(hostname=ssh_host, username='root', 
        key_filename='/home/inky/projects/flask-lessons/id_rsa', port=22)
    stdin, stdout, stderr = ssh.exec_command('cd ' + 
        ssh_directory + '; git fetch; git checkout ' + git_hash + '; echo ___')
    data = stdout.read() + stderr.read()
    ssh.close()
    return data

def get_server_by_stage(stage):
    # mongo will be there
    stage_server_name = app_to_deploy['stages'][stage]
    stage_server_params = server_list[stage_server_name]
    return stage_server_params

class GitDeployForm(Form):
    gitcommit = TextField('gitcommit')
    gitcommit_choice = SelectField('gitcommit_choice')
    stage_choice = SelectField('stage_choice')