import subprocess
import shlex

import s3fs


def get_command(url):
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
        -hls_segment_filename video_%d.ts \
        video.m3u8
    """
    

if __name__ == "__main__":
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key='AKIAQFVMQCMQKBP446UI',
        secret='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',
    )
    
    s3_key = 's3://fix-dive-storage/projects/1234567890/raw_videos/video.mp4'
    
    url = s3.url(s3_key, expires=300)
    
    command = get_command(shlex.quote(url))
    
    print('\n\n')
    print(command)
    print('\n\n')
    
    
    
    process = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE
    )
    
    process.wait()
    
    # buffer = 1024 * 1024
    
    # with s3.open(s3_key, 'rb') as s3_file:
        
    #     while True:
    #         try:
    #             chunk = s3_file.read(buffer)
                
    #             if not chunk:
    #                 s3_file.seek(0)
    #                 continue
                
    #             print('chunk', len(chunk))
                
    #             process.stdin.write(chunk)
    #             process.stdin.flush()

    #         except KeyboardInterrupt:
    #             process.kill()
    #             break