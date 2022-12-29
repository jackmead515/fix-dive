import cv2
from PIL import Image

def convert_mp4_to_gif(input_file, output_file):
    capture = cv2.VideoCapture(input_file)
    capture.set(cv2.CAP_PROP_FPS, 0.1)

    frame_count = 0
    frames = []

    while True:
        ret, frame = capture.read()
        if not ret:
            break
            
        frame_count += 1

        if frame_count % 5 != 0:
            continue



        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2, interpolation=cv2.INTER_LANCZOS4)
        frames.append(frame)

    capture.release()

    # convert to a gif

    frames = [Image.fromarray(frame) for frame in frames]
    frames[0].save(output_file, format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=0)



if __name__ == "__main__":
    convert_mp4_to_gif('./interesting_stabilized.mp4', './interesting_stabilized.gif')