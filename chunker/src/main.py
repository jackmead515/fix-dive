import logging
import uuid
import shlex
import os
import subprocess
from urllib.parse import urlparse
from concurrent.futures import ProcessPoolExecutor
import tempfile
import sys

import s3fs
import inotify_simple

sys.path.append('../..')

from common.project import Project
from common.s3_project import convert_to_http

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


def verify_playlist(s3_client, playlist_path) -> bool:
    """
    Verify if all the chunks found in the m3u8 file are uploaded to S3.
    If the playlist file is not found, or any one the chunks inside of
    the m3u8 file is not found, return False.
    """
    
    variants = ['view', 'low']
    
    for variant in variants:

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
        if verify_playlist(s3, playlist_path):
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

    m3u8_main = """#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:6
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-INDEPENDENT-SEGMENTS
"""

    for playlist_folder in playlist_folders:
        
        m3u8_file = os.path.join(playlist_folder, 'view', 'video.m3u8')
        
        http_folder = convert_to_http(playlist_folder, config.S3_ENDPOINT_URL.replace('http://', ''))
        
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
                m3u8_main += ext_line + chunk_file
                li += 2
            
            m3u8_main += '#EXT-X-ENDLIST'

    logging.info(f'uploading: {project.main_playlist_path}')
    
    with s3.open(project.main_playlist_path, 'wb') as f:
        f.write(m3u8_main.encode('utf-8'))


if __name__ == "__main__":

    config.initialize()

    logging.basicConfig(level=logging.INFO)
    
    project = Project(
        bucket_name=config.S3_BUCKET,
        project_id=config.PROJECT_ID,
    )
    
    print(project)
    
    s3 = s3fs.S3FileSystem(
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

    pool = ProcessPoolExecutor(max_workers=config.MAX_WORKERS)
    
    raw_files = project.list_raw_videos_files(s3)
    playlist_paths = project.list_playlist_folders(s3)

    for raw_file, playlist_path in zip(raw_files, playlist_paths):
        generate_playlist(project, raw_file, playlist_path, options)
        #pool.submit(generate_playlist, project, raw_file, playlist_path, options)

    #pool.shutdown(wait=True)

    #generate_master_playlist(project, playlist_paths)