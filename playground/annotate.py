import cv2
import numpy as np

import random

if __name__ == "__main__":

    import pandas as pd

    capture = cv2.VideoCapture('../test2_original.mp4')
    capture.set(cv2.CAP_PROP_FPS, 0.1)

    frame_count = 0
    data = []

    #data = pd.read_csv('rects.csv')

    while True:
        ret, frame = capture.read()
        if not ret:
            break
            
        frame_count += 1

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if random.random() >= 0.9:

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            rating = int(input("Enter score for the previous image... (1-10)"))

            data.append([frame_count, rating])

        # total_rects = data['rolling'].iloc[frame_count - 1]
        # if total_rects > 80 or total_rects < 60:
        #     cv2.imshow('frame', frame)
        #     if cv2.waitKey(1) & 0xFF == ord('q'):
        #         break

        # for rect in rects:
        #     x, y, w, h = rect
        #     cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        # cv2.imshow('frame', frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    capture.release()

    df = pd.DataFrame(data, columns=['frame_index', 'rating'])
    #df['rolling'] = df['rects'].rolling(60).mean()
    df.to_csv('annotated.csv', index=False)