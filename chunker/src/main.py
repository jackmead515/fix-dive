import logging
import uuid
import shlex
import os
import subprocess
from urllib.parse import urlparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import tempfile
import json
import sys

import s3fs
import cv2
import requests

sys.path.append('../..')

from common.project import Project
from common.s3_project import convert_to_http
import common.video_info as video_info

import config


def process_video_to_stream(http_url, output_dir):
    command = f"""
    ffmpeg \
        -y \
        -i {shlex.quote(http_url)} \
        -x264-params opencl=true \
        -filter_complex '[0:v]split=2[o1][o2];[o1]scale=iw/2:ih/2[view];[o2]scale=iw/2:ih/2[low]' \
            -map '[view]' \
                -crf 25 \
                -preset fast \
                -tune film \
                -movflags +faststart \
                -threads 6 \
                -x264-params opencl=true \
                -r 60 \
                -f hls \
                -hls_time 5 \
                -hls_playlist_type vod \
                -hls_flags independent_segments \
                -hls_segment_type mpegts \
                -hls_segment_filename {output_dir}/view/video_%d.ts \
                {output_dir}/view/video.m3u8 \
            -map '[low]' \
                -crf 30 \
                -preset veryfast \
                -tune zerolatency \
                -movflags +faststart \
                -threads 6 \
                -x264-params opencl=true \
                -r 60 \
                -f hls \
                -hls_time 5 \
                -hls_playlist_type vod \
                -hls_flags independent_segments \
                -hls_segment_type mpegts \
                -hls_segment_filename {output_dir}/low/video_%d.ts \
                {output_dir}/low/video.m3u8
    """
    
    logging.info(f'running command: {command}')
    
    ffmpeg_process = subprocess.Popen(
        command,
        shell=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    ffmpeg_process.wait()


def mount_s3_bucket_command(temp_dir, s3_path):
    command = f"""
    echo "{config.S3_ACCESS_KEY_ID}:{config.S3_SECRET_ACCESS_KEY}" > /tmp/dive/s3credentials \
        && chmod 600 /tmp/dive/s3credentials
    """
    
    logging.info(f'running command: {command}')
    
    subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
    ).wait()
        
    command = f"""
    s3fs \
        {config.S3_BUCKET}:{s3_path} \
        {temp_dir} \
        -o passwd_file=/tmp/dive/s3credentials,use_path_request_style,url={config.S3_ENDPOINT_URL},parallel_count=16 \
    """

    logging.info(f'running command: {command}')
    
    subprocess.Popen(
        command,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        shell=True,
    ).wait()


def unmount_s3_bucket(temp_dir):
    subprocess.Popen(
        f"sudo umount {temp_dir}",
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    ).wait()


def verify_playlist(s3_client, project: Project, playlist_path) -> bool:
    """
    Verify if all the chunks found in the m3u8 file are uploaded to S3.
    If the playlist file is not found, or any one the chunks inside of
    the m3u8 file is not found, return False.
    """
    
    for variant in project.playlist_variants:

        playlist_file = os.path.join(playlist_path, variant, 'video.m3u8')

        with tempfile.NamedTemporaryFile(dir='/tmp/dive/') as f:

            try:
                with s3_client.open(playlist_file, 'rb') as g:
                    f.write(g.read())
            except FileNotFoundError:
                return False

            lines = f.read().decode('utf-8')
            
            for line in lines:
                if line.endswith('.ts'):
                    chunk_file = os.path.join(playlist_path, line)
                    if not s3_client.exists(chunk_file):
                        return False

    return True


def generate_playlist(project: Project, raw_file: str, playlist_path: str, options: dict):
    
    logging.info(f'generating playlist for: {raw_file}')
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )
    
    # if the option to force_recompute is not set, verify the playlist
    # by checking if all the chunks are uploaded. If not, recompute
    # the playlist. This might be due to a failed upload or corruption.
    if not options.get('force_recompute'): 
        if verify_playlist(s3, project, playlist_path):
            logging.info('playlist already exists')
            return
    
    # Create temporary in-memory directory to store the chunks
    temp_dir = f'/tmp/dive/{uuid.uuid4()}'
    os.makedirs(temp_dir, exist_ok=True)
    
    mount_s3_bucket_command(temp_dir, urlparse(playlist_path).path)
    
    os.makedirs(os.path.join(temp_dir, 'view'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'low'), exist_ok=True)

    # convert s3 url to http url. Don't want a presigned url because it may expire
    raw_http_url = convert_to_http(raw_file, config.S3_ENDPOINT_URL.replace('http://', ''))

    # process the video to stream saving to the temp_dir
    process_video_to_stream(raw_http_url, temp_dir)
    
    unmount_s3_bucket(temp_dir)


def generate_master_playlist(project: Project, playlist_folders):
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )

    

    for variant in project.playlist_variants:
        
        m3u8_variant_path = project.get_variant_playlist_path(variant)
        
        m3u8_lines = """#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-INDEPENDENT-SEGMENTS
"""

        for playlist_folder in playlist_folders:
            
            m3u8_file = os.path.join(playlist_folder, variant, 'video.m3u8')
            
            http_folder = convert_to_http(playlist_folder + "/" + variant, config.S3_ENDPOINT_URL.replace('http://', ''))
            
            with s3.open(m3u8_file, 'rb') as f:
                lines = [line.decode('utf-8') for line in f.readlines()]
                
                # skip to first #EXTINF, line
                li = 0
                while not lines[li].startswith('#EXTINF:'):
                    li += 1
                
                while True:
                    ext_line = lines[li]
                    
                    if ext_line.startswith('#EXT-X-ENDLIST'):
                        break
                    
                    chunk_line = lines[li + 1]
                    chunk_file = os.path.join(http_folder, chunk_line)
                    m3u8_lines += ext_line + chunk_file
                    li += 2
                
                m3u8_lines += '#EXT-X-ENDLIST'

        logging.info(f'uploading: {m3u8_variant_path}')

        with s3.open(m3u8_variant_path, 'wb') as f:
            f.write(m3u8_lines.encode('utf-8'))


def get_video_info(file_path: str) -> dict:
    capture = cv2.VideoCapture(file_path)
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.release()
    
    return {
        'file_path': file_path,
        'total_frames': total_frames,
    }


def read_playlist_segments(http_playlist_path: str) -> list:
    """
    From the m3u8 playlist file, read all the video chunks and
    return information about the total frames and starting frame
    of each chunk.
    """

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
    
    print(project)
    
    s3_client = s3fs.S3FileSystem(
        anon=False,
        key=config.S3_ACCESS_KEY_ID,
        secret=config.S3_SECRET_ACCESS_KEY,
        use_ssl=False,
        client_kwargs={
            'endpoint_url': config.S3_ENDPOINT_URL
        }
    )

    options = {
        'force_recompute': False
    }
    
    os.makedirs('/tmp/dive', exist_ok=True)

    raw_files = project.list_raw_videos_files(s3_client)
    playlist_paths = project.list_playlist_folders(s3_client)

    # For each raw video file, generate the HLS streams for the video
    for raw_file, playlist_path in zip(raw_files, playlist_paths):
        generate_playlist(project, raw_file, playlist_path, options)

    # Generate the master playlist for each variant stream to make
    # a single playable video
    generate_master_playlist(project, playlist_paths)
    
    # For each variant, generate the video details and segments details
    # that show the total number of frames, the starting frames of each
    # chunk, and the path to each chunk.
    for variant in project.playlist_variants:
        
        variant_playlist_path = project.get_variant_playlist_path(variant)
        http_variant_playlist_path = convert_to_http(variant_playlist_path, config.S3_ENDPOINT_URL.replace('http://', ''))

        playlist_details_path = project.get_variant_playlist_details(variant)
        playlist_segments_path = project.get_variant_playlist_segments(variant)
        
        if (
            options.get('force_recompute')
            or not s3_client.exists(playlist_segments_path)
            or not s3_client.exists(playlist_details_path)
        ):
            logging.info(f'computing video segments for: {http_variant_playlist_path}')
            video_segments = read_playlist_segments(http_variant_playlist_path)
            
            total_frames = sum([segment['total_frames'] for segment in video_segments])
            
            logging.info(f'computing video details for: {http_variant_playlist_path}')
            video_details = video_info.details(http_variant_playlist_path)
            video_details['custom'] = {
                'total_frames': total_frames,
            }
            
            with s3_client.open(playlist_details_path, 'wb') as f:
                f.write(json.dumps(video_details).encode('utf-8'))
            
            with s3_client.open(playlist_segments_path, 'wb') as f:
                f.write(json.dumps(video_segments).encode('utf-8'))