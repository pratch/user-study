#!/usr/bin/env python3
"""
Debug script to show exactly what reference values were used during cropping
vs what the comparison sees.
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

def main():
    base_dir = Path(__file__).parent / 'FINAL_BASELINES_V2_CRF'
    
    print("="*80)
    print("REFERENCE CALCULATION (What crop_face_matched.py does)")
    print("="*80)
    
    # Calculate reference from ar and gaga (first 3 videos of each)
    reference_methods = [
        ('ar', 'ar'),
        ('gaga', 'gaga')
    ]
    
    ratios = []
    y_positions = []
    
    print("\nCalculating reference from first 3 videos of ar and gaga:")
    
    for method, subdir in reference_methods:
        method_dir = base_dir / method / subdir
        video_files = sorted(method_dir.glob('*.mp4'))[:3]
        
        print(f"\n{method.upper()}:")
        for video_file in video_files:
            print(f"  {video_file.name}")
            face = detect_face_first_frame(video_file)
            if face:
                x, y, w, h = face
                width = 512
                height = 512
                face_area = w * h
                frame_area = width * height
                ratio = face_area / frame_area
                chin_y = y + h
                normalized_chin_y = chin_y / height
                
                ratios.append(ratio)
                y_positions.append(normalized_chin_y)
                
                print(f"    Face: ({x}, {y}) {w}x{h}")
                print(f"    Chin Y: {chin_y} (norm: {normalized_chin_y:.4f})")
                print(f"    Ratio: {ratio:.4f}")
    
    avg_ratio = sum(ratios) / len(ratios)
    avg_chin_y = sum(y_positions) / len(y_positions)
    
    print(f"\n>>> REFERENCE VALUES USED FOR CROPPING:")
    print(f"    Average face ratio: {avg_ratio:.4f}")
    print(f"    Average chin Y: {avg_chin_y:.4f}")
    
    # Now check a specific problematic subject
    print("\n" + "="*80)
    print("CHECKING SUBJECT A_104")
    print("="*80)
    
    gaga_video = base_dir / 'gaga' / 'gaga' / 'gaga_heygen_A_104.mp4'
    cropped_video = Path(__file__).parent / 'cropped' / 'ga' / 'front' / 'ga_heygen_A_104.mp4'
    
    print(f"\nGAGA (reference, first frame):")
    gaga_face = detect_face_first_frame(gaga_video)
    if gaga_face:
        x, y, w, h = gaga_face
        chin_y = y + h
        chin_norm = chin_y / 512
        ratio = (w * h) / (512 * 512)
        print(f"  Face: ({x}, {y}) {w}x{h}")
        print(f"  Chin Y: {chin_y} (norm: {chin_norm:.4f})")
        print(f"  Ratio: {ratio:.4f}")
        print(f"  Difference from reference chin: {abs(chin_norm - avg_chin_y):.4f}")
    
    print(f"\nCropped GA (result, first frame):")
    cropped_face = detect_face_first_frame(cropped_video)
    if cropped_face:
        x, y, w, h = cropped_face
        chin_y = y + h
        chin_norm = chin_y / 512
        ratio = (w * h) / (512 * 512)
        print(f"  Face: ({x}, {y}) {w}x{h}")
        print(f"  Chin Y: {chin_y} (norm: {chin_norm:.4f})")
        print(f"  Ratio: {ratio:.4f}")
        print(f"  Difference from reference chin: {abs(chin_norm - avg_chin_y):.4f}")
    
    print(f"\nComparison:")
    if gaga_face and cropped_face:
        _, gy, _, gh = gaga_face
        _, cy, _, ch = cropped_face
        gaga_chin = (gy + gh) / 512
        cropped_chin = (cy + ch) / 512
        print(f"  GAGA chin: {gaga_chin:.4f}")
        print(f"  Cropped GA chin: {cropped_chin:.4f}")
        print(f"  Difference: {abs(gaga_chin - cropped_chin):.4f}")
        
        print(f"\n>>> EXPLANATION:")
        print(f"    Both are matched to reference chin ({avg_chin_y:.4f}), NOT to each other!")
        print(f"    GAGA A_104 is {abs(gaga_chin - avg_chin_y):.4f} away from reference")
        print(f"    Cropped GA A_104 is {abs(cropped_chin - avg_chin_y):.4f} away from reference")
        print(f"    The difference you see ({abs(gaga_chin - cropped_chin):.4f}) is because")
        print(f"    GAGA A_104 itself doesn't match the average reference!")

if __name__ == "__main__":
    main()
