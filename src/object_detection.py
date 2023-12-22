import cv2
from ultralytics import YOLO
import torch

device = torch.device(
    'cuda') if torch.cuda.is_available() else torch.device('cpu')


class ObjectDetector:
    def __init__(self, weights="yolov8s.pt"):
        self.model = YOLO(weights).to(device)

    def detect(self, image):
        # Run detection
        results = self.model(image)
        boxes = []
        objects_detected = []
        for obj in results:
            for box in obj.boxes:
                # printing the name of the detected object
                conf = box.conf.item()
                if conf < 0.3:
                    continue
                # Get bounding box coordinates
                xyxy = box.xyxy[0].cpu().numpy()
                x_min, y_min, x_max, y_max = map(int, xyxy)

                # Draw bounding box
                cv2.rectangle(image, (x_min, y_min),
                              (x_max, y_max), (0, 255, 0), 2)

                # Get label and confidence score
                label = self.model.names[int(box.cls)]
                conf = box.conf.item()

                # Draw label and confidence score on the image
                text = f"{label} {conf:.2f}"
                cv2.putText(image, text, (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # Append box coordinates to list
                boxes.append((x_min, y_min, x_max, y_max, label))
                objects_detected.append(label)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image, objects_detected
