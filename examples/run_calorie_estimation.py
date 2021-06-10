#!/usr/bin/env python
"""
Live estimation of burned calories.

Usage:
  run_calorie_estimation.py [--weight=WEIGHT --age=AGE --height=HEIGHT --gender=GENDER]
                            [--camera_id=CAMERA_ID]
                            [--path_in=FILENAME]
                            [--path_out=FILENAME]
                            [--title=TITLE]
                            [--model_name=NAME]
                            [--model_version=VERSION]
                            [--use_gpu]
  run_calorie_estimation.py (-h | --help)

Options:
  --weight=WEIGHT                 Weight (in kilograms). Will be used to convert predicted MET value to calories
                                  [default: 70]
  --age=AGE                       Age (in years). Will be used to convert predicted MET value to calories [default: 30]
  --height=HEIGHT                 Height (in centimeters). Will be used to convert predicted MET value to calories
                                  [default: 170]
  --gender=GENDER                 Gender ("male" or "female" or "other"). Will be used to convert predicted MET value to
                                  calories
  --camera_id=CAMERA_ID           ID of the camera to stream from
  --path_in=FILENAME              Video file to stream from
  --path_out=FILENAME             Video file to stream to
  --title=TITLE                   This adds a title to the window display
  --model_name=NAME               Name of the model to be used.
  --model_version=VERSION         Version of the model to be used.
  --use_gpu                       Whether to run inference on the GPU or not.
"""
from typing import Optional

from docopt import docopt

import sense.display
from sense.controller import Controller
from sense.downstream_tasks import calorie_estimation
from sense.downstream_tasks.nn_utils import Pipe
from sense.loading import build_backbone_network
from sense.loading import get_relevant_weights
from sense.loading import ModelConfig


SUPPORTED_MODEL_CONFIGURATIONS = [
    ModelConfig('StridedInflatedMobileNetV2', 'pro', ['met_converter']),
    ModelConfig('StridedInflatedEfficientNet', 'pro', ['met_converter']),
    ModelConfig('StridedInflatedMobileNetV2', 'lite', ['met_converter']),
    ModelConfig('StridedInflatedEfficientNet', 'lite', ['met_converter']),
]


def run_calorie_estimation(model_name: str, model_version: str, path_in: Optional[str] = None,
                           path_out: Optional[str] = None, weight: Optional[int, float] = 70.0,
                           height: Optional[int, float] = 170.0, age: float = 30.0, gender: Optional[str] = None,
                           title: Optional[str] = None, camera_id: object = 0, use_gpu: bool = True, **kwargs):
    """
    :param model_name:
        Model from backbone (StridedInflatedEfficientNet or StridedInflatedMobileNetV2).
    :param model_version:
        Model version (pro or lite)
    :param path_in:
        The index of the webcam that is used. Default to 0.
    :param path_out:
        If provided, store the captured video in a file in this location.
    :param weight:
        Weight (in kilograms). Will be used to convert MET values to calories. Default to 70.
    :param height:
        Height (in centimeters). Will be used to convert MET values to calories. Default to 170.
    :param age:
        Age (in years). Will be used to convert MET values to calories. Default to 30.
    :param gender:
        Gender ("male" or "female" or "other"). Will be used to convert MET values to calories
    :param title:
            Title of the image frame on display.
    :param camera_id:
        The index of the webcam that is used. Default id is 0.
    :param use_gpu:
        If True, run the model on the GPU
    """
    # Load weights
    selected_config, weights = get_relevant_weights(
        SUPPORTED_MODEL_CONFIGURATIONS,
        model_name,
        model_version
    )

    # Load backbone network
    backbone_network = build_backbone_network(selected_config, weights['backbone'])

    # Load MET value converter
    met_value_converter = calorie_estimation.METValueMLPConverter()
    met_value_converter.load_state_dict(weights['met_converter'])
    met_value_converter.eval()

    # Concatenate backbone network and met converter
    net = Pipe(backbone_network, met_value_converter)

    post_processors = [
        calorie_estimation.CalorieAccumulator(weight=weight,
                                              height=height,
                                              age=age,
                                              gender=gender,
                                              smoothing=12)
    ]

    display_ops = [
        sense.display.DisplayFPS(expected_camera_fps=net.fps,
                                 expected_inference_fps=net.fps / net.step_size),
        sense.display.DisplayDetailedMETandCalories(),
    ]
    display_results = sense.display.DisplayResults(title=title, display_ops=display_ops,
                                                   display_fn=kwargs.get('display_fn', None))

    # Run live inference
    controller = Controller(
        neural_network=net,
        post_processors=post_processors,
        results_display=display_results,
        callbacks=[],
        camera_id=camera_id,
        path_in=path_in,
        path_out=path_out,
        use_gpu=use_gpu,
        stop_event=kwargs.get('stop_event', None),
    )
    controller.run_inference()


if __name__ == "__main__":
    # Parse arguments
    args = docopt(__doc__)
    _weight = float(args['--weight'])
    _height = float(args['--height'])
    _age = float(args['--age'])
    _gender = args['--gender'] or None
    _model_name = args['--model_name'] or None
    _model_version = args['--model_version'] or None
    _use_gpu = args['--use_gpu']
    _camera_id = int(args['--camera_id'] or 0)
    _path_in = args['--path_in'] or None
    _path_out = args['--path_out'] or None
    _title = args['--title'] or None

    run_calorie_estimation(
        model_name=_model_name,
        model_version=_model_version,
        path_in=_path_in,
        path_out=_path_out,
        weight=_weight,
        height=_height,
        age=_age,
        gender=_gender,
        title=_title,
        camera_id=_camera_id,
        use_gpu=_use_gpu
    )
