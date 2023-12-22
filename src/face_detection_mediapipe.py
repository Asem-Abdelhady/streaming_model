import cv2
import mediapipe as mp


class FaceDetection:
    def __init__(self, min_detection_confidence=0.5):
        self.mp_face_detection = mp.solutions.face_detection
        self.mpdrawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection()
        self.min_detection_confidence = min_detection_confidence

    def detect(self, image):

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  
        results = self.face_detection.process(image)
        
        if results.detections:
            for detection in results.detections:
                if detection.score[0] < self.min_detection_confidence:
                    continue
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, ic = image.shape
                bbox = int(bboxC.xmin * iw), int(bboxC.ymin * ih), \
                    int(bboxC.width * iw), int(bboxC.height * ih)
                cv2.rectangle(image, bbox, (255, 255, 255), 2)
                cv2.putText(image, f'{int(detection.score[0]*100)}%',
                            (bbox[0], bbox[1] - 20), cv2.FONT_HERSHEY_PLAIN,
                            2, (255, 255, 255), 2)
        else:
            print("No face detected")
        return image
    