import cv2
from tensorflow.keras.applications.resnet_v2 import ResNet50V2, preprocess_input

class Features():


    def __init__(self, config):
        self.config = config
        self.model = ResNet50V2(
            input_shape=(224, 224, 3),
            include_top=False,
            weights='imagenet',
            pooling='avg'
        )
        self.frame_skip = 0
        


    def __call__(self, frame):
        self.frame_skip += 1
        
        if self.frame_skip % self.config['skip_frames'] != 0:
            return None
        
        resized = cv2.resize(frame, (224, 224))
        resized = resized.reshape(1, 224, 224, 3)
        resized = preprocess_input(resized)
        return self.model.predict(resized, verbose=0)