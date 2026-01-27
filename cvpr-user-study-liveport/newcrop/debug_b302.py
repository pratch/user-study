#!/usr/bin/env python3
"""
Debug why subject B_302 doesn't align perfectly.
"""

import cv2
from pathlib import Path

def detect_face_first_frame(video_path):
    """Detect face in first frame."""
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
        return (int(x), int(y), int(w), int(h))
    
    return None

def investigate_b302():
    """Investigate B_302 mismatch."""
    base_dir = Path(__file__).parent / 'FINAL_BASELINES_V2_CRF'
    
    print("="*80)
    print("INVESTIGATING SUBJECT B_302")
    print("="*80)
    
    # Check AR
    ar_video = base_dir / 'ar' / 'ar' / 'ar_heygen_B_302.mp4'
    print(f"\n1. AR B_302:")
    if ar_video.exists():
        ar_face = detect_face_first_frame(ar_video)
        if ar_face:
            x, y, w, h = ar_face
            chin_y = y + h
            chin_norm = chin_y / 512
            ratio = (w * h) / (512 * 512)
            print(f"   Face: ({x}, {y}) {w}x{h}")
            print(f"   Chin Y: {chin_y} (norm: {chin_norm:.4f})")
            print(f"   Ratio: {ratio:.4f}")
        else:
            print(f"   ⚠️ No face detected!")
    else:
        print(f"   ⚠️ Video not found!")
    
    # Check GAGA
    gaga_video = base_dir / 'gaga' / 'gaga' / 'gaga_heygen_B_302.mp4'
    print(f"\n2. GAGA B_302:")
    if gaga_video.exists():
        gaga_face = detect_face_first_frame(gaga_video)
        if gaga_face:
            x, y, w, h = gaga_face
            chin_y = y + h
            chin_norm = chin_y / 512
            ratio = (w * h) / (512 * 512)
            print(f"   Face: ({x}, {y}) {w}x{h}")
            print(f"   Chin Y: {chin_y} (norm: {chin_norm:.4f})")
            print(f"   Ratio: {ratio:.4f}")
        else:
            print(f"   ⚠️ No face detected!")
    else:
        print(f"   ⚠️ Video not found!")
    
    # Calculate average (what the script should use as target)
    if ar_face and gaga_face:
        ar_x, ar_y, ar_w, ar_h = ar_face
        gaga_x, gaga_y, gaga_w, gaga_h = gaga_face
        
        ar_chin = (ar_y + ar_h) / 512
        gaga_chin = (gaga_y + gaga_h) / 512
        ar_ratio = (ar_w * ar_h) / (512 * 512)
        gaga_ratio = (gaga_w * gaga_h) / (512 * 512)
        
        avg_chin = (ar_chin + gaga_chin) / 2
        avg_ratio = (ar_ratio + gaga_ratio) / 2
        
        print(f"\n3. TARGET (average of AR and GAGA):")
        print(f"   Chin Y: {avg_chin:.4f}")
        print(f"   Ratio: {avg_ratio:.4f}")
        
        print(f"\n4. DIFFERENCE BETWEEN AR AND GAGA:")
        print(f"   Chin Y diff: {abs(ar_chin - gaga_chin):.4f}")
        print(f"   Ratio diff: {abs(ar_ratio - gaga_ratio):.4f}")
        
        if abs(ar_chin - gaga_chin) > 0.02:
            print(f"   ⚠️ Large difference! AR and GAGA don't match well for this subject")
    
    # Check cropped GA result
    cropped_video = Path(__file__).parent / 'cropped' / 'ga' / 'front' / 'ga_heygen_B_302.mp4'
    print(f"\n5. CROPPED GA B_302:")
    if cropped_video.exists():
        cropped_face = detect_face_first_frame(cropped_video)
        if cropped_face:
            x, y, w, h = cropped_face
            chin_y = y + h
            chin_norm = chin_y / 512
            ratio = (w * h) / (512 * 512)
            print(f"   Face: ({x}, {y}) {w}x{h}")
            print(f"   Chin Y: {chin_y} (norm: {chin_norm:.4f})")
            print(f"   Ratio: {ratio:.4f}")
            
            if ar_face and gaga_face:
                print(f"\n   Difference from target: {abs(chin_norm - avg_chin):.4f}")
                print(f"   Difference from AR: {abs(chin_norm - ar_chin):.4f}")
                print(f"   Difference from GAGA: {abs(chin_norm - gaga_chin):.4f}")
        else:
            print(f"   ⚠️ No face detected!")
    else:
        print(f"   ⚠️ Video not found!")
    
    print(f"\n" + "="*80)
    print("EXPLANATION:")
    print("="*80)
    print("The cropped GA is matched to the AVERAGE of AR and GAGA.")
    print("If AR and GAGA have different chin positions, the cropped GA")
    print("will be in between, so it won't match either one exactly.")
    print("This is expected when AR and GAGA don't align perfectly.")

if __name__ == "__main__":
    investigate_b302()
