import cv2
from PIL import Image

def convert_to_gif(images, file_name):
    frames = [Image.fromarray(frame) for frame in images]
    frames[0].save(file_name, format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=0)


if __name__ == "__main__":

    capture = cv2.VideoCapture('../test2_original.mp4')
    capture.set(cv2.CAP_PROP_FPS, 0.1)

    frame_count = 0

    high_interesting = []
    low_uninteresting = []
    low_interesting = []

    while True:
        ret, frame = capture.read()
        if not ret:
            break
            
        frame_count += 1

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2, interpolation=cv2.INTER_LANCZOS4)
        
        if frame_count >= 1050 and frame_count <= 1200:
            high_interesting.append(frame)
        
        if frame_count >= 1250 and frame_count <= 1350:
            low_uninteresting.append(frame)

        if frame_count >= 200 and frame_count <= 300:
            low_interesting.append(frame)

    capture.release()

    # create a video from frames
    convert_to_gif(low_interesting, 'low_objects_interesting.mp4')
    convert_to_gif(high_interesting, 'high_objects_interesting.mp4')
    convert_to_gif(low_uninteresting, 'low_objects_uninteresting.mp4')

