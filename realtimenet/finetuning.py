import os
import glob

import numpy as np
import torch
import torch.optim as optim
import torch.nn as nn

from realtimenet import camera
from realtimenet import engine


def set_internal_padding_false(module):
    """
    This is used to turn off padding of steppable convolution layers.
    """
    if hasattr(module, "internal_padding"):
        module.internal_padding = False


class FeaturesDataset(torch.utils.data.Dataset):
    """Features dataset."""

    def __init__(self, files, labels, num_timesteps=5):
        self.files = files
        self.labels = labels
        self.num_timesteps = num_timesteps

    def __len__(self):
        return len(self.files)

    def __getitem__(self, idx):
        feature = np.load(self.files[idx])
        num_preds = feature.shape[0]
        position = 0
        if num_preds > self.num_timesteps:
            position = np.random.randint(0, num_preds - self.num_timesteps)
        return [feature[position: position + self.num_timesteps], self.labels[idx]]


def generate_data_loader(features_dir, classes, class2int,
                         num_timesteps=5, batch_size=16, shuffle=True):

    # Find pre-computed features and derive corresponding labels
    features = []
    labels = []
    for label in classes:
        feature_temp = glob.glob(f'{features_dir}/{label}/*.npy')
        features += feature_temp
        labels += [class2int[label]] * len(feature_temp)

    # Build dataloader
    dataset = FeaturesDataset(features, labels, num_timesteps=num_timesteps)
    data_loader = torch.utils.data.DataLoader(dataset, shuffle=shuffle, batch_size=batch_size)

    return data_loader


def uniform_frame_sample(video, sample_rate):
    """
    Uniformly sample video frames according to the provided sample_rate.
    """

    depth = video.shape[0]
    if sample_rate < 1.:
        indices = np.arange(0, depth, 1./sample_rate)
        offset = int((depth - indices[-1]) / 2)
        sampled_frames = (indices + offset).astype(np.int32)
        return video[sampled_frames]
    return video


def extract_features(path_in, net, num_layer_finetune, use_gpu, minimum_frames=45):

    # Create inference engine
    inference_engine = engine.InferenceEngine(net, use_gpu=use_gpu)

    # extract features
    for dataset in ["train", "valid"]:
        videos_dir = os.path.join(path_in, f"videos_{dataset}")
        features_dir = os.path.join(path_in, f"features_{dataset}_{num_layer_finetune}")
        video_files = glob.glob(os.path.join(videos_dir, "*", "*.mp4"))

        print(f"\nFound {len(video_files)} videos to process")

        for video_index, video_path in enumerate(video_files):
            print(f"\rExtract features from video {video_index} / {len(video_files)}",
                  end="")
            path_out = video_path.replace(videos_dir, features_dir).replace(".mp4", ".npy")

            if os.path.isfile(path_out):
                print("\n\tSkipped - feature was already precomputed.")
            else:
                # Read all frames
                video_source = camera.VideoSource(camera_id=None,
                                                  size=inference_engine.expected_frame_size,
                                                  filename=video_path)
                video_fps = video_source.get_fps()
                frames = []
                while True:
                    images = video_source.get_image()
                    if images is None:
                        break
                    else:
                        image, image_rescaled = images
                        frames.append(image_rescaled)
                frames = uniform_frame_sample(np.array(frames), inference_engine.fps/video_fps)
                clip = np.array([frames]).astype(np.float32)

                # Inference
                if clip.shape[1] > minimum_frames:
                    predictions = inference_engine.infer(clip)
                    features = np.array(predictions)
                    os.makedirs(os.path.dirname(path_out), exist_ok=True)
                    np.save(path_out, features)

                else:
                    print(f"Video too short: {video_path}")


def training_loops(net, trainloader, use_gpu, num_epochs, lr_schedule, features_dir, classes, class2int, num_timestep):
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(net.parameters(), lr=0.0001)

    for epoch in range(num_epochs):  # loop over the dataset multiple times
        new_lr = lr_schedule.get(epoch)
        if new_lr:
            print(f"update lr to {new_lr}")
            for param_group in optimizer.param_groups:
                param_group['lr'] = new_lr

        running_loss = 0.0
        net.train()
        epoch_top_predictions = []
        epoch_labels = []

        for i, data in enumerate(trainloader):
            # get the inputs; data is a list of [inputs, targets]
            inputs, targets = data
            if use_gpu:
                inputs = inputs.cuda()
                targets = targets.cuda()

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = []
            for i in range(len(inputs)):
                pred = net(inputs[i])
                outputs.append(pred.mean(dim=0).unsqueeze(0))
            outputs = torch.cat(outputs, dim=0)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            # Store label and predictions to compute statistics later
            epoch_labels += list(targets.cpu().numpy())
            epoch_top_predictions += list(outputs.argmax(dim=1).cpu().numpy())

            # print statistics
            running_loss += loss.item()

        epoch_labels = np.array(epoch_labels)
        epoch_top_predictions = np.array(epoch_top_predictions)

        train_top1 = np.mean(epoch_labels == epoch_top_predictions)
        train_loss = running_loss / len(trainloader)

        valid_loss, valid_top1 = evaluation_model(net, criterion, features_dir, classes, class2int, num_timestep, use_gpu)
        print('[%d] train loss: %.3f train top1: %.3f valid loss: %.3f top1: %.3f' % (epoch + 1, train_loss, train_top1,
                                                                                      valid_loss, valid_top1))

    print('Finished Training')


def evaluation_model(net, criterion, features_dir, classes, class2int, num_timestep, use_gpu):
    with torch.no_grad():
        top_pred = []
        predictions = []
        y = []
        net.eval()
        for label in classes:
            features = os.listdir(os.path.join(features_dir, label))
            # used to remove .DSstore files on mac
            features = [x for x in features if not x.startswith('.')]
            for feature in features:
                feature = np.load(os.path.join(features_dir, label, feature))
                if len(feature) > num_timestep:
                    if use_gpu:
                        feature = torch.Tensor(feature).cuda()

                    output = net(feature)
                    pred = output.mean(dim=0)
                    predictions.append(pred.unsqueeze(0))
                    top_pred.append(pred.cpu().numpy().argmax())
                    y.append(class2int[label])
        predictions = torch.cat(predictions, dim=0)
        pred = np.array(top_pred)
        y = np.array(y)
        y_tensor = torch.Tensor(y).long()
        if use_gpu:
            y_tensor = y_tensor.cuda()
        loss = criterion(predictions, y_tensor).item()
        percent = (np.sum(pred == y) / len(pred))
        return loss, percent
