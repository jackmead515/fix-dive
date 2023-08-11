import subprocess

import s3fs

import config

if __name__ == "__main__":

    config.initialize()
    
    s3_file_path = f's3://{config.S3_BUCKET}/video.mp4'
    
    s3 = s3fs.S3FileSystem(
        anon=False,
        key=config.AWS_ACCESS_KEY_ID,
        secret=config.AWS_SECRET_ACCESS_KEY,
    )

    # ffmpeg pipe accept from stdin and pipe to video.mp4
    command = "ffmpeg -i - -vcodec copy -an -sn -f mp4 video.mp4"

    # ffmpeg pipe accept from stdin and pipe to -f image2pipe
    # command = "ffmpeg -i - -vcodec copy -an -sn -f image2pipe -"

    pipe = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    with s3.open(s3_file_path, 'rb') as s3_file:

        chunk = s3_file.read(config.READ_BUFFER_SIZE)

        # write chunk to ffmpeg stdin
        pipe.stdin.write(chunk)