import cv2
import os
import numba as nb
import dask as da
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.neighbors import LocalOutlierFactor

from util.cache import cache

@nb.njit
def rolling_mean(arr, n=30):
    pre_buffer = np.zeros(3).reshape(1, 3)
    post_buffer = np.zeros(3 * n).reshape(n, 3)
    arr_cumsum = np.cumsum(np.vstack((pre_buffer, arr, post_buffer)), axis=0)
    buffer_roll_mean = (arr_cumsum[n:, :] - arr_cumsum[:-n, :]) / float(n)
    trunc_roll_mean = buffer_roll_mean[:-n, ]

    bfill_size = arr.shape[0] - trunc_roll_mean.shape[0]
    bfill = np.tile(trunc_roll_mean[0, :], (bfill_size, 1))

    return np.vstack((bfill, trunc_roll_mean))


def moving_average(curve, radius): 
	window_size = 2 * radius + 1
	# Define the filter 
	f = np.ones(window_size)/window_size 
	# Add padding to the boundaries 
	curve_pad = np.lib.pad(curve, (radius, radius), 'edge') 
	# Apply convolution 
	curve_smoothed = np.convolve(curve_pad, f, mode='same') 
	# Remove padding 
	curve_smoothed = curve_smoothed[radius:-radius]
	# return smoothed curve
	return curve_smoothed 


def smooth(trajectory): 
	smoothed_trajectory = np.copy(trajectory) 
	for i in range(3):
		smoothed_trajectory[:,i+1] = moving_average(trajectory[:,i+1], radius=50)
	return smoothed_trajectory


def zoom(frame, percent):
    width, height = frame.shape[1], frame.shape[0]
    center = width / 2, height / 2
    T = cv2.getRotationMatrix2D(center, 0, 1.0 + percent)
    return cv2.warpAffine(
        frame,
        T,
        (width, height),
        borderMode=cv2.INTER_LANCZOS4
    )


def rotate(frame, angle):
    width, height = frame.shape[1], frame.shape[0]

    center = (frame.shape[1]/2, frame.shape[0]/2)

    T = cv2.getRotationMatrix2D(center, angle, 1.0)

    return cv2.warpAffine(
        frame,
        T,
        dsize=(width, height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_REFLECT,
    )


def translate(frame, dx, dy):
    width, height = frame.shape[1], frame.shape[0]

    T = np.float32([
        [1, 0, dx],
        [0, 1, dy]
    ])

    return cv2.warpAffine(
        frame,
        T,
        dsize=(width, height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_REFLECT,
    )


def calculate_stabilization(capture):
    
    n_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    _, prev_frame = capture.read()

    prev_frame = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    transforms = np.zeros((n_frames - 1, 4), np.float32)

    for i in tqdm(range(n_frames - 2), desc="Calculating Stabilization"):
        prev_points = cv2.goodFeaturesToTrack(
            prev_frame,
            maxCorners=200,
            qualityLevel=0.01,
            minDistance=30,
            blockSize=3
        )

        ret, next_frame = capture.read()

        if not ret:
            break

        next_frame = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)

        next_points, status, error = cv2.calcOpticalFlowPyrLK(
            prev_frame,
            next_frame,
            prev_points,
            None
        )

        print(next_points.shape, prev_points.shape, next_frame.shape, prev_frame.shape)

        idx = np.where(status == 1)[0]
        prev_points = prev_points[idx]
        next_points = next_points[idx]

        m = cv2.estimateAffinePartial2D(prev_points, next_points)[0]

        dx = m[0, 2]
        dy = m[1, 2]
        da = np.arctan2(m[1, 0], m[0, 0])

        transforms[i] = [i, dx, dy, da]

        prev_frame = next_frame

    return transforms


@cache("smooth.npy")
def smooth_stablization(transforms):

    outlier_window = 20
    outlier_smooth_window = 30
    smooth_window = 20

    df = pd.DataFrame(transforms, columns=['frame_index', 'stabilize_dx', 'stabilize_dy', 'stabilize_da'])

    model = LocalOutlierFactor(n_neighbors=outlier_window)

    x_train = df[['stabilize_dx', 'stabilize_dy', 'stabilize_da']].values

    outlier_factors = model.fit_predict(x_train)

    df['outlier_factor'] = outlier_factors

    scaled_df = df.copy()

    for i in range(df.shape[0]):
        # if is an outlier, replace with rolling average
        if df.iloc[i]['outlier_factor'] == -1:
            start = i - outlier_smooth_window
            end = i + outlier_smooth_window

            if start < 0:
                start = 0

            if end > df.shape[0]:
                end = df.shape[0]

            scaled_df.loc[i, 'stabilize_dx'] = df.loc[start:end, 'stabilize_dx'].mean()
            scaled_df.loc[i, 'stabilize_dy'] = df.loc[start:end, 'stabilize_dy'].mean()
            scaled_df.loc[i, 'stabilize_da'] = df.loc[start:end, 'stabilize_da'].mean()
    
    # select all by the first column
    # trajectory = transforms[:, 1:]
    # smoothed_trajectory = rolling_mean(trajectory, n=30)
    # trajectory = trajectory + (smoothed_trajectory - trajectory)
    # transforms[:, 1:] = trajectory

    smoothed = scaled_df[['stabilize_dx', 'stabilize_dy', 'stabilize_da']].transform(lambda x: moving_average(x, smooth_window)) # .rolling(smooth_window).mean()
    smoothed['frame_index'] = df['frame_index']

    return smoothed[['frame_index', 'stabilize_dx', 'stabilize_dy', 'stabilize_da']].values


def update_stabilization(capture, transforms):
    n_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

    #out = cv2.VideoWriter('./stablized_video.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 60, (width, height))

    for i in tqdm(range(n_frames-2), desc="Applying Stabilization"):

        ret, frame = capture.read() 
        if not ret:
            break

        dx = transforms[i,1]
        dy = transforms[i,2]
        da = transforms[i,3]

        transform = np.zeros((2,3), np.float32)
        transform[0,0] = np.cos(da)
        transform[0,1] = -np.sin(da)
        transform[1,0] = np.sin(da)
        transform[1,1] = np.cos(da)
        transform[0,2] = dx
        transform[1,2] = dy

        frame_stabilized = cv2.warpAffine(
            frame,
            transform,
            dsize=(width, height),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_REPLICATE,
        )
        frame_stabilized = zoom(frame_stabilized, 0.04)

        #out.write(frame_stabilized)

        cv2.imshow('frame', frame_stabilized)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
   # out.release()


class Stabilize():

    def __init__(self, config):
        self.config = config

    def __call__(self, capture):

        # calculate the transformations
        transforms = calculate_stabilization(capture)

        # smooth outliers and smooth the trajectory
        transforms = smooth_stablization(transforms)

        # apply the now smoothed transformations
        update_stabilization(capture, transforms)


        #self.trajectory = np.array(self._trajectory)
        #self.smoothed_trajectory = general_utils.bfill_rolling_mean(self.trajectory, n=self._smoothing_window)
        #self.transforms = np.array(self._raw_transforms) + (self.smoothed_trajectory - self.trajectory)

        # trajectory = np.cumsum(transforms, axis=0)
        # smoothed_trajectory = smooth(trajectory)
        # difference = smoothed_trajectory - trajectory
        # transforms_smooth = transforms + difference