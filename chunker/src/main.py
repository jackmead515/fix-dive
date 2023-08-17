import logging
import uuid
import shlex
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import tempfile

import s3fs
import inotify_simple

import config
import util.s3_project as s3_project
from util.dir_watcher import DirWatcher
from models.project import Project


def upload_chunk(s3_client, file_path, s3_path):
    logging.info(f'uploading: {s3_path}')
    
    with s3_client.open(s3_path, 'wb') as f:
        with open(file_path, 'rb') as g:
            while True:
                chunk = g.read(config.READ_BUFFER_SIZE)
                if not chunk:
                    break
                f.write(chunk)

    os.remove(file_path)
    
    logging.info(f'finished uploading: {s3_path}')


def get_hls_command(url, output_dir):
    return f"""
    ffmpeg \
        -y \
        -i {url} \
        -c:v copy \
        -f hls \
        -hls_time 5 \
        -hls_playlist_type vod \
        -hls_flags independent_segments \
        -hls_segment_type mpegts \
        -hls_segment_filename {output_dir}/video_%d.ts \
        {output_dir}/video.m3u8
    """


def verify_playlist(s3_client, playlist_path) -> bool:
    """
    Verify if all the chunks found in the m3u8 file are uploaded to S3.
    If the playlist file is not found, or any one the chunks inside of
    the m3u8 file is not found, return False.
    """

    playlist_file = os.path.join(playlist_path, 'video.m3u8')

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

    # convert s3 url to http url. Don't want a presigned url because it may expire
    raw_http_url = s3_project.convert_to_http(raw_file, config.S3_ENDPOINT_URL.replace('http://', ''))

    upload_pool = ThreadPoolExecutor(max_workers=16)
    
    with DirWatcher(temp_dir, inotify_simple.flags.CLOSE_WRITE) as watcher:
        
        ffmpeg_process = subprocess.Popen(
            get_hls_command(shlex.quote(raw_http_url), temp_dir),
            shell=True,
        )
        
        ffmpeg_alive = lambda: ffmpeg_process.poll() is None
        
        while True:

            for event in watcher.next(timeout=1):
                
                file_path = os.path.join(temp_dir, event.name)
                playlist_file = os.path.join(playlist_path, os.path.basename(file_path))

                logging.info(f'done processing: {playlist_file}')
                
                upload_pool.submit(upload_chunk, s3, file_path, playlist_file)

            if not ffmpeg_alive():
                break

        ffmpeg_process.wait()

        # TODO: if the uploading is too slow, ffmpeg may be paused
        # in order to reduce the memory usage
        
        # sent STOP signal to pause ffmpeg
        # ffmpeg_process.send_signal(signal.SIGSTOP)
        
        # sent CONT signal to resume ffmpeg
        # ffmpeg_process.send_signal(signal.SIGCONT)
    
    upload_pool.shutdown(wait=True)


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
        
        m3u8_file = os.path.join(playlist_folder, 'video.m3u8')
        
        http_folder = s3_project.convert_to_http(playlist_folder, config.S3_ENDPOINT_URL.replace('http://', ''))
        
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
        pool.submit(generate_playlist, project, raw_file, playlist_path, options)

    pool.shutdown(wait=True)

    generate_master_playlist(project, playlist_paths)
    
    