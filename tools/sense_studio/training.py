import multiprocessing
import os
import queue
import time
import urllib

from flask import Blueprint
from flask import render_template
from flask import request

from tools.sense_studio import utils
from tools.sense_studio.training_script import training_model

training_bp = Blueprint('training_bp', __name__)

train_process = None
queue_train_logs = None


@training_bp.route('/<string:project>', methods=['GET'])
def training_page(project):
    project = urllib.parse.unquote(project)
    path = utils.lookup_project_path(project)
    return render_template('training.html', project=project, path=path, models=utils.BACKBONE_MODELS, is_disabled=False)


@training_bp.route('/train-model', methods=['POST'])
def train_model():
    data = request.form
    project = data['project']
    path = data['path']
    config = utils.load_project_config(path)
    model_name, model_version = data['model_name'].split('-')

    ctx = multiprocessing.get_context('spawn')

    global queue_train_logs
    queue_train_logs = ctx.Queue()

    training_kwargs = {
        'path_in': path,
        'num_layers_to_finetune': int(data['layers_to_finetune']),
        'path_out': os.path.join(path, data['output_folder'] or "checkpoints"),
        'model_version': model_version,
        'model_name': model_name,
        'epochs': int(data['epochs']),
        'use_gpu': config['use_gpu'],
        'temporal_training': config['temporal'],
        'training_logs': queue_train_logs,
    }

    global train_process
    train_process = ctx.Process(target=training_model, kwargs=training_kwargs)
    train_process.start()

    def get_training_logs():
        global train_process
        global queue_train_logs
        while True:
            try:
                output = queue_train_logs.get(timeout=1)
                if output:
                    time.sleep(0.1)
                    yield output + '\n'
            except queue.Empty:
                if not train_process.is_alive():
                    train_process.terminate()
                    train_process = None
                    queue_train_logs.close()
                    break

    return render_template('training.html', project=project, path=path, is_disabled=True, models=utils.BACKBONE_MODELS,
                           logs=get_training_logs())


@training_bp.route('/cancel-training', methods=['POST'])
def cancel_training():
    data = request.form
    project = data['project']
    path = data['path']
    global train_process
    if train_process:
        train_process.terminate()
        train_process = None
        log = "Training Cancelled."
    else:
        log = "No Training Process Running to Terminate."
    return render_template('training.html', project=project, path=path, models=utils.BACKBONE_MODELS, is_disabled=False,
                           logs=[log])
