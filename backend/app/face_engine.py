"""
Face detection + recognition.

Detection: OpenCV DNN res10 SSD face detector (Caffe, ~5MB).
Recognition: OpenCV-contrib LBPH (Local Binary Patterns Histograms) face
recognizer - a classical, non-deep-learning algorithm bundled with
opencv-contrib. Chosen over `face_recognition`/dlib specifically to avoid a
C++ build toolchain dependency, and over deep embeddings (FaceNet/ArcFace)
to avoid a multi-hundred-MB model download - appropriate trade-offs for an
MVP, not for large-scale (1000s of identities) production deployment.

Privacy: enrollment never writes the original uploaded photo to disk. The
photo is decoded in memory, the face region is detected, converted to a
grayscale patch, fed into the recognizer's training set, and discarded.
Only the trained LBPH model file (a numeric representation, not a photo)
persists in MODEL_DIR.
"""
import os
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.config import settings

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
DEPLOY_PROTOTXT = os.path.join(MODEL_DIR, "deploy.prototxt")
DETECTOR_WEIGHTS = os.path.join(MODEL_DIR, "res10_300x300_ssd_iter_140000_fp16.caffemodel")
RECOGNIZER_PATH = os.path.join(settings.model_dir, "lbph_model.yml")
LABELS_PATH = os.path.join(settings.model_dir, "labels.npy")

_detector = None
_recognizer = None


def get_detector():
    global _detector
    if _detector is None:
        if not (os.path.exists(DEPLOY_PROTOTXT) and os.path.exists(DETECTOR_WEIGHTS)):
            raise FileNotFoundError("Face detector model files missing from backend/models/.")
        _detector = cv2.dnn.readNetFromCaffe(DEPLOY_PROTOTXT, DETECTOR_WEIGHTS)
    return _detector


def get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists(RECOGNIZER_PATH):
            _recognizer.read(RECOGNIZER_PATH)
    return _recognizer


def detect_faces(frame: np.ndarray, confidence_threshold: float = 0.6) -> List[Tuple[int, int, int, int]]:
    net = get_detector()
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    boxes = []
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < confidence_threshold:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)
        if x2 > x1 and y2 > y1:
            boxes.append((x1, y1, x2, y2))
    return boxes


def largest_face_patch(frame: np.ndarray) -> Optional[np.ndarray]:
    boxes = detect_faces(frame)
    if not boxes:
        return None
    x1, y1, x2, y2 = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    patch = gray[y1:y2, x1:x2]
    return cv2.resize(patch, (200, 200))


def _load_labels() -> dict:
    if os.path.exists(LABELS_PATH):
        return np.load(LABELS_PATH, allow_pickle=True).item()
    return {}


def _save_labels(labels: dict):
    np.save(LABELS_PATH, labels)


def enroll_face(patch: np.ndarray, label_id: int):
    """Incrementally trains (or updates) the LBPH recognizer with one new face patch."""
    recognizer = get_recognizer()
    if os.path.exists(RECOGNIZER_PATH):
        recognizer.update([patch], np.array([label_id]))
    else:
        recognizer.train([patch], np.array([label_id]))
    recognizer.save(RECOGNIZER_PATH)


def recognize_face(patch: np.ndarray) -> Tuple[Optional[int], float]:
    """Returns (label_id or None, distance). Lower distance = more confident match."""
    if not os.path.exists(RECOGNIZER_PATH):
        return None, 999.0
    recognizer = get_recognizer()
    label_id, distance = recognizer.predict(patch)
    if distance > settings.recognition_confidence_threshold:
        return None, distance
    return label_id, distance
