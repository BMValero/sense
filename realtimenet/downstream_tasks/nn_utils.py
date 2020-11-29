import numpy as np
import torch.nn as nn

from typing import Tuple


class RealtimeNeuralNet(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, input_tensor):
        """
        Feed forward of the input tensor to the feature extractor and converters.
        """
        raise NotImplementedError

    def preprocess(self, clip: np.ndarray):
        """
        Pre-process a clip from a video source.
        """
        raise NotImplementedError

    @property
    def step_size(self) -> int:
        """
        Return the step size of the neural network.
        """
        raise NotImplementedError

    @property
    def fps(self) -> int:
        """
        Return the frame per second rate of the neural network.
        """
        raise NotImplementedError

    @property
    def expected_frame_size(self) -> Tuple[int, int]:
        """
        Return the expected frame size of the neural network.
        """
        raise NotImplementedError


class Pipe(RealtimeNeuralNet):

    def __init__(self, feature_extractor, feature_converter):
        super().__init__()
        self.feature_extractor = feature_extractor
        self.feature_converter = feature_converter

    def forward(self, input_tensor):
        feature = self.feature_extractor(input_tensor)
        if isinstance(self.feature_converter, list):
            return [convert(feature) for convert in self.feature_converter]
        return self.feature_converter(feature)

    @property
    def expected_frame_size(self) -> Tuple[int, int]:
        return self.feature_extractor.expected_frame_size

    @property
    def fps(self) -> int:
        return self.feature_extractor.fps

    @property
    def step_size(self):
        return self.feature_extractor.step_size

    def preprocess(self, clip: np.ndarray):
        return self.feature_extractor.preprocess(clip)


class LogisticRegression(nn.Sequential):

    def __init__(self, num_in, num_out, global_average_pooling=True):
        super(LogisticRegression, self).__init__(
            nn.Linear(num_in, num_out),
            nn.Softmax(dim=-1)
        )
        self.global_average_pooling = global_average_pooling

    def forward(self, input_tensor):
        if self.global_average_pooling:
            input_tensor = input_tensor.mean(dim=-1).mean(dim=-1)
        return super().forward(input_tensor)
