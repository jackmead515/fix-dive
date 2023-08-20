import subprocess
import json

def details(file_path) -> dict:
    """
    Retrieves video information using ffprobe from a local file path.
    """
    command = f"""
        ffprobe \
            -v quiet \
            -print_format json \
            -show_format \
            -show_streams {file_path}
    """

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    output = process.stdout.read().decode('utf-8').strip()
    
    output = json.loads(output)
    
    return output


# def launch_video_pipe():
#     # ffmpeg pipe accept from stdin and pipe to video.mp4
#     # command = "ffmpeg -i - -vcodec copy -an -sn -f mpegts video.mp4"

#     # ffmpeg pipe accept from stdin and pipe to tcp stream
#     # command = "ffmpeg -i - -vcodec copy -an -sn -f mpegts tcp://127.0.0.1:1234\?listen"

#     # ffmpeg pipe to http stream
#     # command = "ffmpeg -i - -listen 1 -vcodec copy -an -sn -f mp4 -movflags frag_keyframe+empty_moov http://127.0.0.1:1234"
    
#     return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
