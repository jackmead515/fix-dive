import subprocess
import shlex

import s3fs

# ffmpeg 
#     -re 
#     -f concat 
#     -i concat.txt 
#     -c:v libx264 
#     -vbsf h264_mp4toannexb 
#     -r 25 -g 75 -c:a libfdk_aac -hls_time 3 playlist.m3u8

def get_command(url1, url2):
    return f"""
    ffmpeg \
        -y \
        -protocol_whitelist file,http,https,tcp,tls,crypto \
        -f concat \
        -i concat.txt \
        -c:v copy \
        -c:a copy \
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
    
    s3_key_1 = 'http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/Y2h1bmsubXA0MTUxZGI3ODQ2NjJjOTU3ZGY1NDMwNDY5YWRkMmU4NTE=/video.m3u8'
    s3_key_2 = 'http://172.23.0.100:30140/fix-dive-storage/projects/1234567890/playlists/Y2h1bmsubXA0MTUxZGI3ODQ2NjJjOTU3ZGY1NDMwNDY5YWRkMmU4NTE=/video.m3u8'
    
    with open('concat.txt', 'wb') as f:
        f.write(f"file {s3_key_1}\n".encode('utf-8'))
        f.write(f"file {s3_key_2}\n".encode('utf-8'))
    
    command = get_command(shlex.quote(s3_key_1), shlex.quote(s3_key_2))
    
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