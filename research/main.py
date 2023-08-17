import cv2
import numpy as np
import math
import pandas as pd

from features.motion import Motion
from features.objects import Objects
from clean.stabilize import Stabilize

if __name__ == "__main__":
    
    motion_detector = Motion(None)
    object_detector = Objects(None)

    # TODO - calculate the total motion before hand and identify the
    #        footage that is too shaky to be used. That way we can
    #        skip the stabilization step and save time.
    #stabilize = Stabilize(None)

    capture = cv2.VideoCapture('../clean_raw/chunk_0.mp4')

    print("total frames", capture.get(cv2.CAP_PROP_FRAME_COUNT))

    data = []
    frame_index = 0

    while True:
        ret, frame = capture.read()
        if not ret:
            break
        
        #motion = motion_detector(frame)
        objects = object_detector(frame)

        print(len(objects))
        data.append([frame_index, len(objects)])
        frame_index += 1

    # save data to csv
    df = pd.DataFrame(data, columns=['frame_index', 'objects'])
    df.to_csv("objects.csv", index=False)

    capture.release()