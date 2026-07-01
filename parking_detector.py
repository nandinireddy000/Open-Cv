import cv2
import pickle
import numpy as np
from database_manager import DatabaseManager

class ParkingDetector:
    def __init__(self, pos_file='source/CarParkPos.txt', db_manager=None):
        self.pos_file = pos_file
        self.width, self.height = 107, 48
        self.pos_list = self._load_positions()
        self.db = db_manager
        
        # State tracking to avoid DB spam
        self.slot_status_cache = {} # slot_index -> 'Empty'/'Occupied'

    def _load_positions(self):
        try:
            with open(self.pos_file, 'rb') as f:
                return pickle.load(f)
        except:
            return []

    def preprocess_frame(self, img):
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
        img_thresh = cv2.adaptiveThreshold(
            img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 16
        )
        img_median = cv2.medianBlur(img_thresh, 5)
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(img_median, kernel, iterations=1)
        return img_dilate

    def process_frame(self, img):
        # Allow reusing the same image object by copying if necessary, 
        # but here we draw on the original img.
        img_processed = self.preprocess_frame(img)
        
        empty_slots = 0
        total_slots = len(self.pos_list)
        slot_data = []

        for i, pos in enumerate(self.pos_list):
            x, y = pos
            
            # Crop the slot
            img_crop = img_processed[y:y + self.height, x:x + self.width]
            count = cv2.countNonZero(img_crop)
            
            # Threshold for occupancy (tuning needed usually, 900 is a safe start for this dataset)
            if count < 900:
                color = (0, 255, 0) # Green
                thickness = 5
                status = "Empty"
                empty_slots += 1
            else:
                color = (0, 0, 255) # Red
                thickness = 2
                status = "Occupied"

            # Draw rectangle
            cv2.rectangle(img, (x, y), (x + self.width, y + self.height), color, thickness)
            cv2.putText(img, str(count), (x, y + self.height - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Update DB if status changed
            if self.db:
                self._update_db_if_needed(i, status)
            
            slot_data.append({
                "id": i,
                "status": status,
                "pixel_count": count
            })

        # Dashboard overlay
        cv2.rectangle(img, (40, 20), (450, 70), (0, 200, 0), -1)
        cv2.putText(img, f'Free: {empty_slots}/{total_slots}', (50, 60), 
                    cv2.FONT_HERSHEY_TRIPLEX, 1.5, (255, 255, 255), 2)

        return img, slot_data

    def _update_db_if_needed(self, slot_id, status):
        # Only update if status changed from last known state
        if self.slot_status_cache.get(slot_id) != status:
            self.db.update_slot_status(slot_id, status)
            self.slot_status_cache[slot_id] = status
