#!/usr/bin/env python3
"""
Detailed analysis of why subject 104 chin matching fails.
Analyzes the relationship between face detection and actual head bounds.
"""

import cv2
import numpy as np
from pathlib import Path
import json

def detect_face_in_video(video_path, num_samples=10):
    """Detect face by sampling multiple frames."""
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
    
    # Calculate average
    avg_x = int(sum(face[0] for face in detected_faces) / len(detected_faces))
    avg_y = int(sum(face[1] for face in detected_faces) / len(detected_faces))
    avg_w = int(sum(face[2] for face in detected_faces) / len(detected_faces))
    avg_h = int(sum(face[3] for face in detected_faces) / len(detected_faces))
    
    return (avg_x, avg_y, avg_w, avg_h)

def get_video_info(video_path):
    """Get video dimensions."""
    cap = cv2.VideoCapture(str(video_path))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def analyze_subject():
    """Analyze why subject 104 chin matching fails."""
    base_dir = Path(__file__).parent / 'FINAL_BASELINES_V2_CRF'
    
    print("="*80)
    print("ANALYZING SUBJECT 104 CHIN MATCHING ISSUE")
    print("="*80)
    
    # Analyze reference (gaga)
    gaga_video = base_dir / 'gaga' / 'gaga' / 'gaga_heygen_A_104.mp4'
    print("\n1. REFERENCE VIDEO (GAGA):")
    print(f"   Path: {gaga_video}")
    
    gaga_width, gaga_height = get_video_info(gaga_video)
    print(f"   Video size: {gaga_width}x{gaga_height}")
    
    gaga_face = detect_face_in_video(gaga_video)
    if gaga_face:
        gx, gy, gw, gh = gaga_face
        print(f"   Face bbox: ({gx}, {gy}) size {gw}x{gh}")
        print(f"   Face top: {gy} pixels from top")
        print(f"   Face bottom (chin): {gy + gh} pixels from top")
        print(f"   Space above face: {gy} pixels")
        print(f"   Space below face: {gaga_height - (gy + gh)} pixels")
        
        gaga_chin_y = gy + gh
        gaga_chin_norm = gaga_chin_y / gaga_height
        gaga_face_area = gw * gh
        gaga_frame_area = gaga_width * gaga_height
        gaga_ratio = gaga_face_area / gaga_frame_area
        
        print(f"   Normalized chin Y: {gaga_chin_norm:.4f}")
        print(f"   Face-to-frame ratio: {gaga_ratio:.4f}")
    
    # Analyze target (ga)
    ga_video = base_dir / 'ga' / 'ga_scale1.5' / 'ga_heygen_A_104_scale1.5.mp4'
    print("\n2. TARGET VIDEO (GA scale1.5):")
    print(f"   Path: {ga_video}")
    
    ga_width, ga_height = get_video_info(ga_video)
    print(f"   Video size: {ga_width}x{ga_height}")
    
    ga_face = detect_face_in_video(ga_video)
    if ga_face:
        fx, fy, fw, fh = ga_face
        print(f"   Face bbox: ({fx}, {fy}) size {fw}x{fh}")
        print(f"   Face top: {fy} pixels from top")
        print(f"   Face bottom (chin): {fy + fh} pixels from top")
        print(f"   Space above face: {fy} pixels")
        print(f"   Space below face: {ga_height - (fy + fh)} pixels")
        
        ga_chin_y = fy + fh
        ga_chin_norm = ga_chin_y / ga_height
        ga_face_area = fw * fh
        ga_frame_area = ga_width * ga_height
        ga_ratio = ga_face_area / ga_frame_area
        
        print(f"   Normalized chin Y: {ga_chin_norm:.4f}")
        print(f"   Face-to-frame ratio: {ga_ratio:.4f}")
    
    # Now simulate what the crop algorithm does
    print("\n3. CROP ALGORITHM SIMULATION:")
    print(f"   Target ratio: {gaga_ratio:.4f} (from gaga)")
    print(f"   Target chin Y: {gaga_chin_norm:.4f} (from gaga)")
    
    if ga_face and gaga_face:
        # Calculate required crop box size for ga
        target_box_area = ga_face_area / gaga_ratio
        target_box_size = int(np.sqrt(target_box_area))
        
        print(f"\n   For GA to match GAGA ratio:")
        print(f"   GA face area: {ga_face_area} pixels²")
        print(f"   Required box area: {target_box_area:.0f} pixels²")
        print(f"   Required box size: {target_box_size}x{target_box_size}")
        
        # Ensure it doesn't exceed video bounds
        max_box_size = min(ga_width, ga_height)
        crop_size = min(target_box_size, max_box_size)
        min_box_size = int(max(fw, fh) * 1.5)
        crop_size = max(crop_size, min_box_size)
        crop_size = min(crop_size, max_box_size)
        
        print(f"   After constraints: {crop_size}x{crop_size}")
        
        # Calculate crop position based on chin
        face_center_x = fx + fw // 2
        face_chin_y = fy + fh
        
        # Position crop so chin is at target normalized position
        crop_y = int(face_chin_y - (gaga_chin_norm * crop_size))
        crop_x = face_center_x - crop_size // 2
        
        print(f"\n   Crop calculation:")
        print(f"   Face chin at: {face_chin_y} pixels")
        print(f"   Target chin at: {gaga_chin_norm:.4f} * {crop_size} = {gaga_chin_norm * crop_size:.1f} pixels from crop top")
        print(f"   Initial crop_y: {crop_y}")
        print(f"   Initial crop_x: {crop_x}")
        
        # Apply bounds
        if crop_y < 0:
            print(f"   ⚠ crop_y < 0, clamping to 0")
            crop_y = 0
        elif crop_y + crop_size > ga_height:
            print(f"   ⚠ crop_y + size > height, adjusting")
            crop_y = ga_height - crop_size
        
        if crop_x < 0:
            print(f"   ⚠ crop_x < 0, clamping to 0")
            crop_x = 0
        elif crop_x + crop_size > ga_width:
            print(f"   ⚠ crop_x + size > width, adjusting")
            crop_x = ga_width - crop_size
        
        print(f"   Final crop box: ({crop_x}, {crop_y}) size {crop_size}x{crop_size}")
        
        # Check what happens to the face
        face_top_in_crop = fy - crop_y
        face_chin_in_crop = face_chin_y - crop_y
        
        print(f"\n   Result in cropped frame:")
        print(f"   Face top at: {face_top_in_crop} pixels from crop top")
        print(f"   Face chin at: {face_chin_in_crop} pixels from crop top")
        print(f"   Space above face: {face_top_in_crop} pixels")
        print(f"   Space below chin: {crop_size - face_chin_in_crop} pixels")
        
        actual_chin_norm = face_chin_in_crop / crop_size
        print(f"   Actual chin Y (normalized): {actual_chin_norm:.4f}")
        print(f"   Target chin Y (normalized): {gaga_chin_norm:.4f}")
        print(f"   Difference: {abs(actual_chin_norm - gaga_chin_norm):.4f}")
        
        # Check if face extends beyond crop
        if face_top_in_crop < 0:
            print(f"\n   ⚠️ ISSUE: Face top ({fy}) is ABOVE crop top ({crop_y})")
            print(f"   Top of face is cut off by {-face_top_in_crop} pixels")
            print(f"   This is why hair/head appears cut off!")
        
        # Compare with gaga
        print(f"\n4. COMPARISON WITH GAGA:")
        print(f"   GAGA space above face: {gy} pixels ({gy/gaga_height*100:.1f}% of frame)")
        print(f"   GA space above face in crop: {face_top_in_crop} pixels ({face_top_in_crop/crop_size*100:.1f}% of crop)")
        
        if face_top_in_crop < gy:
            print(f"   ⚠️ GA has LESS space above face than GAGA!")
            print(f"   Difference: {gy - face_top_in_crop} pixels less")
        
        print(f"\n5. ROOT CAUSE:")
        print(f"   The face detector found face at different relative positions:")
        print(f"   - In GAGA (512x512): face starts at {gy/gaga_height*100:.1f}% from top")
        print(f"   - In GA (826x1204): face starts at {fy/ga_height*100:.1f}% from top")
        print(f"   ")
        print(f"   When we crop GA to match GAGA's chin position ({gaga_chin_norm:.4f}),")
        print(f"   we're forced to position the crop at y={crop_y},")
        print(f"   which cuts off the top of the head because the face")
        print(f"   detection box doesn't include the full hair/head.")

if __name__ == "__main__":
    analyze_subject()
