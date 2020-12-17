from collections import deque

import numpy as np


class PostProcessor:

    def __init__(self, indices=None):
        self.indices = indices

    def filter(self, predictions):
        if predictions is None:
            return predictions

        if self.indices:
            if len(self.indices) == 1:
                index = self.indices[0]
                return predictions[index]
            else:
                return [predictions[index] for index in self.indices]
        return predictions

    def postprocess(self, prediction):
        raise NotImplementedError

    def __call__(self, predictions):
        return self.postprocess(self.filter(predictions))


class PostprocessClassificationOutput(PostProcessor):

    def __init__(self, mapping_dict, smoothing=1, **kwargs):
        super().__init__(**kwargs)
        self.mapping = mapping_dict
        self.smoothing = smoothing
        assert smoothing >= 1
        self.buffer = deque(maxlen=smoothing)

    def postprocess(self, classif_output):
        if classif_output is not None:
            self.buffer.append(classif_output)

        if self.buffer:
            classif_output_smoothed = sum(self.buffer) / len(self.buffer)
        else:
            classif_output_smoothed = np.zeros(len(self.mapping))

        indices = classif_output_smoothed.argsort()

        return {
            'sorted_predictions': [(self.mapping[index], classif_output_smoothed[index])
                                   for index in indices[::-1]]
        }


class PostprocessRepCounts(PostProcessor):

    def __init__(self, mapping_dict, threshold=0.4, **kwargs):
        super().__init__(**kwargs)
        self.mapping = mapping_dict
        self.threshold = threshold
        self.jumping_jack_counter = TwoPositionsRepCounter(
            mapping_dict,
            "counting - jumping_jacks_position=arms_down",
            "counting - jumping_jacks_position=arms_up",
            threshold)
        self.squats_counter = TwoPositionsRepCounter(
            mapping_dict,
            "counting - squat_position=high",
            "counting - squat_position=low",
            threshold)

    def postprocess(self, classif_output):
        if classif_output is not None:
            self.jumping_jack_counter.postprocess(classif_output)
            self.squats_counter.postprocess(classif_output)

        return {
            'counting': {
                "jumping_jacks": self.jumping_jack_counter.count,
                 "squats": self.squats_counter.count
            }
        }


class TwoPositionsRepCounter(PostProcessor):

    def __init__(self, mapping, position0, position1, threshold0, threshold1, out_key, **kwargs):
        super().__init__(**kwargs)
        self.threshold0 = threshold0
        self.threshold1 = threshold1
        self.position0 = mapping[position0]
        self.position1 = mapping[position1]
        self.count = 0
        self.position = 0
        self.out_key = out_key

    def postprocess(self, classif_output):
        if classif_output is not None:
            if self.position == 0:
                if classif_output[self.position1] > self.threshold1:
                    self.position = 1
            else:
                if classif_output[self.position0] > self.threshold0:
                    self.position = 0
                    self.count += 1

        return {self.out_key: self.count}


class OnePositionRepCounter(PostProcessor):

    def __init__(self, mapping, position, threshold, out_key, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold
        self.position = mapping[position]
        self.count = 0
        self.active = False
        self.out_key = out_key

    def postprocess(self, classif_output):
        if classif_output is not None:
            if self.active and classif_output[self.position] < self.threshold:
                self.active = False
            elif not self.active and classif_output[self.position] > self.threshold:
                self.active = True
                self.count += 1

        return {self.out_key: self.count}
