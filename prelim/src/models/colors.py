import numpy as np
import cv2

from util.profile_time import profile_time

color_map = {
    'red': [
        {
            'lower': np.array([0, 50, 50]),
            'upper': np.array([10, 255, 255])
        },
        {
            'lower': np.array([161, 50, 50]),
            'upper': np.array([179, 255, 255])
        }
    ],
    'orange': {
        'lower': np.array([11, 50, 50]),
        'upper': np.array([25, 255, 255])
    },
    'yellow': {
        'lower': np.array([26, 50, 50]),
        'upper': np.array([34, 255, 255])
    },
    'green': {
        'lower': np.array([35, 50, 50]),
        'upper': np.array([77, 255, 255])
    },
    'blue': {
        'lower': np.array([78, 50, 50]),
        'upper': np.array([125, 255, 255])
    },
    'purple': {
        'lower': np.array([126, 50, 50]),
        'upper': np.array([160, 255, 255])
    },
    'white': {
        'lower': np.array([0, 0, 200]),
        'upper': np.array([179, 30, 255])
    },
    'black': {
        'lower': np.array([0, 0, 0]),
        'upper': np.array([179, 255, 30])
    },
    'brown': {
        'lower': np.array([0, 0, 31]),
        'upper': np.array([179, 255, 100])
    },
}

def get_colored_pixels(color, frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mapp = color_map[color]

    if isinstance(mapp, list):
        mask = cv2.inRange(hsv, mapp[0]['lower'], mapp[0]['upper'])
        mask += cv2.inRange(hsv, mapp[1]['lower'], mapp[1]['upper'])
    else:
        mask = cv2.inRange(hsv, mapp['lower'], mapp['upper'])

    masked = cv2.bitwise_and(frame, frame, mask=mask)
    return masked


class Colors():
    
    def __init__(self, config):
        self.config = config

    @profile_time('colors')
    def __call__(self, frame):
        
        data = {}
        
        for color in color_map.keys():
            mask = get_colored_pixels(color, frame)

            # convert to grayscale
            gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)

            # get the total number of pixels
            total = gray.shape[0] * gray.shape[1]

            # get the total number of pixels with color
            total_color = np.count_nonzero(gray)

            # get the percentage of pixels with color
            percentage = total_color / total
            
            data[color] = percentage

        return data