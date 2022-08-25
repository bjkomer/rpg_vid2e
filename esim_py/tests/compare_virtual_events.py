import os
try:
    import esim_py
except ImportError:
    print("esim_py not found, importing binaries. These do not correspond to source files in this repo")
    import sys
    binaries_folder = os.path.join(os.path.dirname(__file__), "..", "bin")
    sys.path.append(binaries_folder)
    import esim_py

import matplotlib.pyplot as plt
import numpy as np
import os
import cv2
import time


def viz_events(events, resolution):
    pos_events = events[events[:, -1] == 1]
    neg_events = events[events[:, -1] == -1]

    image_pos = np.zeros(resolution[0]*resolution[1], dtype="uint8")
    image_neg = np.zeros(resolution[0]*resolution[1], dtype="uint8")

    np.add.at(image_pos, (pos_events[:, 0]+pos_events[:, 1]*resolution[1]).astype("int32"), pos_events[:, -1]**2)
    np.add.at(image_neg, (neg_events[:, 0]+neg_events[:, 1]*resolution[1]).astype("int32"), neg_events[:, -1]**2)

    image_rgb = np.stack(
        [
            image_pos.reshape(resolution),
            image_neg.reshape(resolution),
            np.zeros(resolution, dtype="uint8")
        ], -1
    ) * 50

    return image_rgb


Cp, Cn = 0.1, 0.1
refractory_period = 1e-4
log_eps = 1e-3
use_log = True
H, W = 180, 240

image_folder = os.path.join(os.path.dirname(__file__), "data/images/images/")
timestamps_file = os.path.join(os.path.dirname(__file__), "data/images/timestamps.txt")
video_file = os.path.join(os.path.dirname(__file__), "data/video/video.avi")

timestamps = np.array([float(x) for x in open(timestamps_file, "r").readlines()])

n_samples = len(timestamps)

# Read images into a list of numpy arrays
images = []
for i in range(n_samples):

    image_file = os.path.join(image_folder, f"image_{i:05d}.png")
    # Load image and convert to grayscale
    image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)

    images.append(image)


esim = esim_py.EventSimulator(Cp,
                              Cn,
                              refractory_period,
                              log_eps,
                              use_log)

fig, ax = plt.subplots(ncols=5, nrows=5, figsize=(6, 6))

contrast_thresholds_pos = [0.1, 0.2, 0.3, 0.4, 0.5]
contrast_thresholds_neg = [0.1, 0.2, 0.3, 0.4, 0.5]
refractory_periods = [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]

num_events_plot = 30000
start = time.time()

matches = 0
total = 0

for i, Cp in enumerate(contrast_thresholds_pos):
    for j, Cn in enumerate(contrast_thresholds_neg):
        esim.setParameters(Cp, Cn, refractory_period, log_eps, use_log)
        events_array = esim.generateFromArray(images, timestamps)
        events_folder = esim.generateFromFolder(image_folder, timestamps_file)

        # assert np.allclose(events_array, events_folder)

        image_rgb_array = viz_events(events_array[:num_events_plot], [H, W])
        image_rgb_folder = viz_events(events_folder[:num_events_plot], [H, W])

        matches += np.allclose(image_rgb_array, image_rgb_folder)
        total += 1
        print(np.linalg.norm(image_rgb_array - image_rgb_folder))

        ax[i, j].imshow(image_rgb_array - image_rgb_folder)
        ax[i, j].axis('off')
        ax[i, j].set_title("Cp=%s Cn=%s" % (Cp, Cn))

end = time.time()
elapsed = end - start
print(elapsed)

print(f"Accuracy: {matches / total}")

plt.show()
