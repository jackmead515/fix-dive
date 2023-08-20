import sys
import logging
import psutil
import os
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor

import s3fs
import cv2
import numpy as np
import pandas as pd
from dask import dataframe as dd
import dask

sys.path.append('../..')

from common.project import Project
from common.s3_project import convert_to_http
import common.video_info as video_info

import config
import dask_util

preprocess_columns = [
    'frame_index',
    'blur',
    'total_objects',
    'median_motion',
    'std_motion',
    'red',
    'orange',
    'yellow',
    'green',
    'blue',
    'purple',
    'white',
    'black',
    'brown'
]

objects_columns = [
    'frame_index',
    'x',
    'y',
    'width',
    'height'
]

def save_dataframe(data, columns, s3_client, s3_file_path):
    df = pd.DataFrame(data, columns=columns)
    with s3_client.open(s3_file_path, 'wb') as f:
        df.to_parquet(f, index=False, compression='gzip')


@dask.delayed
def read_stream(
    options: dict,
    video_segment: dict
):
    
    # will get included as part of the dask worker
    from motion import Motion
    from objects import Objects
    from blur import Blur
    from colors import Colors
    
    logging.basicConfig(level=logging.INFO)

    motion_model = Motion({})
    objects_model = Objects({ 'resize': 0.2 })
    blur_model = Blur({})
    colors_model = Colors({})
    
    start_frame = video_segment['start_frame']
    frames_to_read = video_segment['total_frames']
    http_segment_path = video_segment['file_path']

    capture = cv2.VideoCapture(http_segment_path)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 10)
    
    frame_index = start_frame
    frames_read = 0
    
    preprocess_data = []
    objects_data = []
    
    skip_frames = options.get('skip_frames', 1)
    resize = options.get('resize', 1.0)
    
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) * resize)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) * resize)
    video_area = width * height
    
    small_area_threshold = 0.01 * video_area
    large_area_threshold = 0.95 * video_area
    
    logging.info('starting compute features')
    
    while True:
        
        if frames_read >= frames_to_read:
            break

        success = capture.grab()
        
        if not success:
            break

        if frame_index % skip_frames != 0:
            frames_read += 1
            frame_index += 1
            continue
        
        success, frame = capture.retrieve()
        
        if not success:
            break

        if resize != 1.0:
            frame = cv2.resize(frame, (0,0), fx=resize, fy=resize, interpolation=cv2.INTER_LANCZOS4)
        
        # compute all the features
        motion = motion_model(frame)
        objects = objects_model(frame)
        blur = blur_model(frame)
        colors = colors_model(frame)

        median_motion = np.nan if motion is None else np.median(motion)
        std_motion = np.nan if motion is None else np.std(motion)

        preprocess_data.append([
            frame_index,
            blur,
            len(objects),
            median_motion,
            std_motion,
            *colors,
        ])
        
        # save the objects to a seperate dataset
        for object in objects:
            x, y, w, h = object
            area = w * h
            if area < small_area_threshold or area > large_area_threshold:
                continue
            objects_data.append([frame_index, x, y, w, h])

        progress = round((frame_index / frames_to_read) * 100, 2)
        logging.info(f'compute features progress: {progress}%')

        frames_read += 1
        frame_index += 1

    capture.release()
    
    pre_df = pd.DataFrame(preprocess_data, columns=preprocess_columns)
    obj_df = pd.DataFrame(objects_data, columns=objects_columns)
    
    return pre_df, obj_df


def get_video_info(file_path: str) -> dict:
    capture = cv2.VideoCapture(file_path)
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.release()
    
    return {
        'file_path': file_path,
        'total_frames': total_frames,
    }


def read_playlist(http_playlist_path: str):

    response = requests.get(http_playlist_path)
    
    m3u8_lines = response.content.decode('utf-8')
    m3u8_lines = m3u8_lines.split('\n')
    
    chunks = []
    
    pool = ThreadPoolExecutor(max_workers=16)
    futures = []
    
    for index, line in enumerate(m3u8_lines):
        
        if line.startswith('#EXTINF'):
            file_path = m3u8_lines[index + 1]
            
            futures.append(pool.submit(get_video_info, file_path))

    pool.shutdown(wait=True)
    chunks = [future.result() for future in futures]
    
    start_frame = 0
    
    for chunk in chunks:
        chunk['start_frame'] = start_frame
        start_frame += chunk['total_frames']
    
    return chunks


if __name__ == "__main__":

    config.initialize()
    
    logging.basicConfig(level=logging.INFO)
    
    project = Project(
        bucket_name=config.S3_BUCKET,
        project_id=config.PROJECT_ID,
    )
    
    logging.info(f'Processing Project: {project}')
    
    options = {
        'skip_frames': 5,
        'resize': 1.0,
        'force_recompute': False,
    }
    
    logging.info('capturing video information')
    start_processing = time.perf_counter()
    
    http_playlist_path = convert_to_http(project.main_playlist_path, config.S3_ENDPOINT_URL.replace('http://', ''))
    
    if not os.path.exists('video_info.json') or not os.path.exists('video_segments.json'):
        
        video_segments = read_playlist(http_playlist_path)
        
        video_info = video_info.details(http_playlist_path)

    else:
        with open('video_info.json', 'r') as f:
            video_info = json.loads(f.read())
        
        with open('video_segments.json', 'r') as f:
            video_segments = json.loads(f.read())

    # capture = cv2.VideoCapture(http_playlist_path)
    
    # total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    
    # chunk_read_frames = total_frames * config.PARALLEL_CHUNK_RATIO
    
    # chunks = []
    # for i in range(0, int(total_frames), int(chunk_read_frames)):
    #     chunks.append((i, int(chunk_read_frames)))
    
    # capture.release()
    
    logging.info(f'video path: {http_playlist_path}')
    logging.info(f'video info: {video_info}')
    logging.info(f'video segments: {video_segments}')

    with open('video_info.json', 'w') as f:
        f.write(json.dumps(video_info))
    
    with open('video_segments.json', 'w') as f:
        f.write(json.dumps(video_segments))

    logging.info('finished capturing video information')
    logging.info(f'capturing video information time: {time.perf_counter() - start_processing} seconds')
    
    logging.info('starting distributed processing')
    start_processing = time.perf_counter()
    
    dask_client = dask_util.get_dask_client()
    
    features = []

    for video_segment in video_segments:
        features.append(read_stream(options, video_segment))
        
    dask_client.upload_file('models/motion.py')
    dask_client.upload_file('models/objects.py')
    dask_client.upload_file('models/blur.py')
    dask_client.upload_file('models/colors.py')

    features = dask.compute(*features)
    
    logging.info('finished distributed processing')
    logging.info(f'processing time: {time.perf_counter() - start_processing} seconds')

    features_path = project.features_path
    preprocess_file_path = f'{features_path}/preprocess/preprocess.gzip.parquet'
    objects_file_path = f'{features_path}/objects/objects.gzip.parquet'
    
    preprocess_data = []
    objects_data = []
    
    for pre_data, obj_data in features:
        preprocess_data.extend(pre_data)
        objects_data.extend(obj_data)
        
    s3_client = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )
    
    logging.info(f'writing objects features to {objects_file_path}')
    
    save_dataframe(objects_data, objects_columns, s3_client, objects_file_path)
    
    logging.info(f'writing preprocess features to {preprocess_file_path}')
    
    save_dataframe(preprocess_data, preprocess_columns, s3_client, preprocess_file_path)