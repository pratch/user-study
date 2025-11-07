#!/usr/bin/env python3
"""
Debug why chin alignment isn't working as expected.
Compare the reference chin position used during cropping vs actual results.
"""

import cv2
import numpy as np
from pathlib import Path

def detect_face_in_video(video_path, num_samples=10):
    """Detect face by sampling multiple frames (same as main script)."""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        return None
    
    frame_indices = np.linspace(0, total_frames - 1, min(num_samples, total_frames), dtype=int)
    detected_faces = []
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5,
            minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) > 0:
            faces_with_area = [(x, y, w, h, w*h) for x, y, w, h in faces]
            faces_with_area.sort(key=lambda x: x[4], reverse=True)
            x, y, w, h, _ = faces_with_area[0]
            detected_faces.append((x, y, w, h))
    
    cap.release()
    
    if not detected_faces:
        return None
    
    avg_x = int(sum(face[0] for face in detected_faces) / len(detected_faces))
    avg_y = int(sum(face[1] for face in detected_faces) / len(detected_faces))
    avg_w = int(sum(face[2] for face in detected_faces) / len(detected_faces))
    avg_h = int(sum(face[3] for face in detected_faces) / len(detected_faces))
    
    return (avg_x, avg_y, avg_w, avg_h)

def detect_face_in_first_frame(video_path):
    """Detect face in just the first frame."""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5,
        minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    if len(faces) > 0:
        faces_with_area = [(x, y, w, h, w*h) for x, y, w, h in faces]
        faces_with_area.sort(key=lambda x: x[4], reverse=True)
        x, y, w, h, _ = faces_with_area[0]
        return (x, y, w, h)
    
    return None

def investigate_chin_mismatch():
    """Investigate why chin positions don't match."""
    base_dir = Path(__file__).parent / 'FINAL_BASELINES_V2_CRF'
    cropped_dir = Path(__file__).parent / 'cropped' / 'ga' / 'front'
    
    # Calculate reference from gaga
    print("="*80)
    print("CALCULATING REFERENCE FROM GAGA")
    print("="*80)
    
    gaga_dir = base_dir / 'gaga' / 'gaga'
    gaga_videos = list(gaga_dir.glob('*.mp4'))[:3]
    
    ref_chin_positions = []
    
    for gaga_video in gaga_videos:
        print(f"\n{gaga_video.name}:")
        face = detect_face_in_video(gaga_video)
        if face:
            x, y, w, h = face
            chin_y = y + h
            chin_norm = chin_y / 512  # GAGA is 512x512
            ref_chin_positions.append(chin_norm)
            print(f"  Face (averaged over 10 frames): {face}")
            print(f"  Chin Y (normalized): {chin_norm:.4f}")
        
        # Also check first frame
        face_first = detect_face_in_first_frame(gaga_video)
        if face_first:
            x, y, w, h = face_first
            chin_y = y + h
            chin_norm = chin_y / 512
            print(f"  Face (first frame only): {face_first}")
            print(f"  Chin Y first frame (normalized): {chin_norm:.4f}")
    
    target_chin_norm = sum(ref_chin_positions) / len(ref_chin_positions)
    print(f"\n>>> TARGET CHIN Y (normalized): {target_chin_norm:.4f}")
    
    # Now check problematic subjects
    print("\n" + "="*80)
    print("CHECKING PROBLEMATIC SUBJECTS (104, 264)")
    print("="*80)
    
    problematic = ['A_104', 'B_104', 'A_264', 'B_264']
    
    for subject_id in problematic:
        sentence, subject = subject_id.split('_')
        
        print(f"\n{'='*60}")
        print(f"SUBJECT {subject_id}")
        print(f"{'='*60}")
        
        # Check cropped result
        cropped_video = cropped_dir / f"ga_heygen_{sentence}_{subject}.mp4"
        gaga_video = gaga_dir / f"gaga_heygen_{sentence}_{subject}.mp4"
        
        if not cropped_video.exists():
            print(f"Cropped video not found: {cropped_video}")
            continue
        
        # Face detection on CROPPED result (averaged)
        print("\nCROPPED GA (averaged over 10 frames):")
        cropped_face_avg = detect_face_in_video(cropped_video)
        if cropped_face_avg:
            x, y, w, h = cropped_face_avg
            chin_y = y + h
            chin_norm = chin_y / 512
            print(f"  Face: {cropped_face_avg}")
            print(f"  Chin Y: {chin_y} (normalized: {chin_norm:.4f})")
            print(f"  Expected: {target_chin_norm:.4f}")
            print(f"  Difference: {abs(chin_norm - target_chin_norm):.4f}")
        
        # Face detection on CROPPED result (first frame)
        print("\nCROPPED GA (first frame only):")
        cropped_face_first = detect_face_in_first_frame(cropped_video)
        if cropped_face_first:
            x, y, w, h = cropped_face_first
            chin_y = y + h
            chin_norm = chin_y / 512
            print(f"  Face: {cropped_face_first}")
            print(f"  Chin Y: {chin_y} (normalized: {chin_norm:.4f})")
            print(f"  Difference from target: {abs(chin_norm - target_chin_norm):.4f}")
        
        # Face detection on GAGA (averaged)
        print("\nGAGA ORIGINAL (averaged over 10 frames):")
        gaga_face_avg = detect_face_in_video(gaga_video)
        if gaga_face_avg:
            x, y, w, h = gaga_face_avg
            chin_y = y + h
            chin_norm = chin_y / 512
            print(f"  Face: {gaga_face_avg}")
            print(f"  Chin Y: {chin_y} (normalized: {chin_norm:.4f})")
        
        # Face detection on GAGA (first frame)
        print("\nGAGA ORIGINAL (first frame only):")
        gaga_face_first = detect_face_in_first_frame(gaga_video)
        if gaga_face_first:
            x, y, w, h = gaga_face_first
            chin_y = y + h
            chin_norm = chin_y / 512
            print(f"  Face: {gaga_face_first}")
            print(f"  Chin Y: {chin_y} (normalized: {chin_norm:.4f})")
        
        # Compare
        if cropped_face_first and gaga_face_first:
            _, cy, _, ch = cropped_face_first
            _, gy, _, gh = gaga_face_first
            
            c_chin = (cy + ch) / 512
            g_chin = (gy + gh) / 512
            
            print(f"\n>>> FIRST FRAME COMPARISON:")
            print(f"    Cropped GA chin: {c_chin:.4f}")
            print(f"    GAGA chin: {g_chin:.4f}")
            print(f"    Difference: {abs(c_chin - g_chin):.4f}")
            
            if abs(c_chin - g_chin) > 0.03:
                print(f"    ⚠️ LARGE MISMATCH!")
                print(f"    This suggests face detection is inconsistent between:")
                print(f"    - The averaged detection used during cropping")
                print(f"    - The single-frame detection in the comparison script")

if __name__ == "__main__":
    investigate_chin_mismatch()
