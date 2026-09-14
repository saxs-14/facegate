import numpy as np
import cv2
from app.face_engine import detect_faces


def test_detect_faces_returns_empty_on_blank_frame():
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    assert detect_faces(frame) == []


def test_lbph_roundtrip_recovers_correct_label():
    """Validates our usage of cv2.face.LBPHFaceRecognizer: train on two
    distinct synthetic patterns, confirm each is correctly re-identified.
    Uses synthetic patterns (not real face photos) to keep the test suite
    free of any real person's biometric data."""
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    pattern_a = np.tile(np.array([[0, 255], [255, 0]], dtype=np.uint8), (100, 100))
    pattern_b = np.tile(np.array([[255, 255], [0, 0]], dtype=np.uint8), (100, 100))

    recognizer.train([pattern_a, pattern_b], np.array([1, 2]))

    label, distance = recognizer.predict(pattern_a)
    assert label == 1
    label, distance = recognizer.predict(pattern_b)
    assert label == 2
