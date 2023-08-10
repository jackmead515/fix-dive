import logging
import os
import math

import boto3
import cv2

import sync_api.src.util.video_info as video_info

def organize(
    s3_file_paths=[],
    bucket_name='',
    target_video_length=10,
    s3_client=None,
):

    if len(s3_file_paths) == 0:
        raise ValueError('No s3_file_paths provided')
    
    if target_video_length <= 0:
        raise ValueError('target_video_length must be greater than 0')

    # Get the first file's metadata
    first_file = s3_client.head_object(
        Bucket=bucket_name,
        Key=s3_file_paths[0],
    )

    print(first_file)


if __name__ == '__main__':
    
    video_info = video_info.video_info('./video.mp4')
    
    print(video_info)
    
    exit()
    

    bucket_name = 'jam-general-storage'

    client = boto3.client(
        's3',
        aws_access_key_id='AKIAQFVMQCMQCPUGCAYA',
        aws_secret_access_key='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',
    )

    objects = client.list_objects_v2(
        Bucket=bucket_name,
        Prefix='unfinished/2021-06-13',
    )

    videos = []

    for obj in objects['Contents']:
        
        obj = {
            'key': obj['Key'],
            'size': obj['Size'],
            'etag': obj['ETag'].replace('"', ''),
        }

        file_name = os.path.basename(obj['key'])
        file_type = file_name.split('.')[-1]

        obj['file_name'] = file_name
        obj['file_type'] = file_type

        videos.append(obj)

    video = videos[7]

    # create presigned url
    url = client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': video['key'],
        },
        ExpiresIn=60,
    )

    print(url)
    
    # download video file
    import requests
    request = requests.get(url, stream=True)
    
    with open('./video.mp4', 'wb') as f:
        f.write(request.content)
        
    exit()

    # play video in opencv

    #cap = cv2.VideoCapture(url, cv2.CAP_DSHOW)
    cap = cv2.VideoCapture(url)
    #cap.set(cv2.CAP_PROP_FPS, 120)

    chunk_seconds = 10

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps
    chunk_count = math.ceil(duration / chunk_seconds)
    chunk_frame_count = fps * chunk_seconds

    video['fps'] = fps
    video['frame_count'] = frame_count
    video['frame_width'] = frame_width
    video['frame_height'] = frame_height
    video['duration'] = duration
    video['chunk_count'] = chunk_count
    video['chunk_frame_count'] = chunk_frame_count

    estimate_chunk_size = video['size'] / chunk_count

    print(video)

    print('estimated chunk size', estimate_chunk_size)

    # split video into x second chunks
    frame_index = 0
    chunk_index = 0
    writer = None

    while True:

        success, frame = cap.read()

        if success == False:
            break

        if frame_index == 0:
            writer = cv2.VideoWriter(
                f'./chunk_{chunk_index}.mp4',
                cv2.VideoWriter_fourcc(*'mp4v'),
                fps,
                (frame_width, frame_height)
            )

        writer.write(frame)

        if frame_index > 0 and frame_index % chunk_frame_count == 0:
            print('chunk', chunk_index, 'complete')
            chunk_index += 1
            writer.release()

            if frame_index < frame_count:
                writer = cv2.VideoWriter(
                    f'./chunk_{chunk_index}.mp4',
                    cv2.VideoWriter_fourcc(*'mp4v'),
                    fps,
                    (frame_width, frame_height)
                )
        
        frame_index += 1

    writer.release()





