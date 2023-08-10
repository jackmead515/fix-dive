import subprocess
import json

def details(file_path) -> dict:
    """
    Retrieves video information using ffprobe from a local file path.
    """
    command = f"ffprobe -v quiet -print_format json -show_format -show_streams {file_path}"

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    output = process.stdout.read().decode('utf-8').strip()
    
    output = json.loads(output)
    
    return output