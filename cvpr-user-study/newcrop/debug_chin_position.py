#!/usr/bin/env python3
"""
Debug script to visualize face detection and chin position for subject 104.
Compares ga (scale1.5) and gaga (front) side by side.
"""

import cv2
import numpy as np
from pathlib import Path

def detect_face_in_frame(frame):
    """Detect face in a single frame."""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    if len(faces) > 0:
        # Take the largest face
        faces_with_area = [(x, y, w, h, w*h) for x, y, w, h in faces]
        faces_with_area.sort(key=lambda x: x[4], reverse=True)
        x, y, w, h, _ = faces_with_area[0]
        return (x, y, w, h)
    return None

def draw_face_info(frame, face_bbox, label):
    """Draw face bounding box and chin marker on frame."""
    if face_bbox is None:
        return frame
    
    frame_copy = frame.copy()
    height, width = frame.shape[:2]
    x, y, w, h = face_bbox
    
    # Draw face bounding box (green)
    cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 3)
    
    # Draw chin position (red horizontal line)
    chin_y = y + h
    cv2.line(frame_copy, (0, chin_y), (width, chin_y), (0, 0, 255), 3)
    
    # Draw center of face (blue circle)
    center_x = x + w // 2
    center_y = y + h // 2
    cv2.circle(frame_copy, (center_x, center_y), 10, (255, 0, 0), -1)
    
    # Calculate normalized positions
    chin_normalized = chin_y / height
    center_normalized = center_y / height
    face_area = w * h
    frame_area = width * height
    face_ratio = face_area / frame_area
    
    # Add text info
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    
    info_lines = [
        f"{label}",
        f"Size: {width}x{height}",
        f"Face: ({x},{y}) {w}x{h}",
        f"Chin Y: {chin_y} (norm: {chin_normalized:.4f})",
        f"Center Y: {center_y} (norm: {center_normalized:.4f})",
        f"Face ratio: {face_ratio:.4f}"
    ]
    
    y_offset = 30
    for line in info_lines:
        cv2.putText(frame_copy, line, (10, y_offset), font, font_scale, (255, 255, 255), thickness + 1, cv2.LINE_AA)
        cv2.putText(frame_copy, line, (10, y_offset), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)
        y_offset += 35
    
    return frame_copy

def visualize_subject_104():
    """Visualize face detection for subject 104 from ga and gaga."""
    base_dir = Path(__file__).parent / 'FINAL_BASELINES_V2_CRF'
    output_dir = Path(__file__).parent / 'debug_output'
    output_dir.mkdir(exist_ok=True)
    
    # Paths to the videos
    ga_video = base_dir / 'ga' / 'ga_scale1.5' / 'ga_heygen_A_104_scale1.5.mp4'
    gaga_video = base_dir / 'gaga' / 'gaga' / 'gaga_heygen_A_104.mp4'
    
    # Also check B_104
    ga_video_b = base_dir / 'ga' / 'ga_scale1.5' / 'ga_heygen_B_104_scale1.5.mp4'
    gaga_video_b = base_dir / 'gaga' / 'gaga' / 'gaga_heygen_B_104.mp4'
    
    videos_to_process = [
        (ga_video, gaga_video, 'A_104'),
        (ga_video_b, gaga_video_b, 'B_104')
    ]
    
    for ga_path, gaga_path, subject in videos_to_process:
        if not ga_path.exists() or not gaga_path.exists():
            print(f"Warning: Videos not found for {subject}")
            continue
        
        print(f"\nProcessing subject {subject}...")
        
        # Read middle frame from each video
        ga_cap = cv2.VideoCapture(str(ga_path))
        gaga_cap = cv2.VideoCapture(str(gaga_path))
        
        # Get middle frame
        ga_total = int(ga_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        gaga_total = int(gaga_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        ga_cap.set(cv2.CAP_PROP_POS_FRAMES, ga_total // 2)
        gaga_cap.set(cv2.CAP_PROP_POS_FRAMES, gaga_total // 2)
        
        ret_ga, ga_frame = ga_cap.read()
        ret_gaga, gaga_frame = gaga_cap.read()
        
        ga_cap.release()
        gaga_cap.release()
        
        if not ret_ga or not ret_gaga:
            print(f"  Error: Could not read frames for {subject}")
            continue
        
        # Detect faces
        print(f"  Detecting faces...")
        ga_face = detect_face_in_frame(ga_frame)
        gaga_face = detect_face_in_frame(gaga_frame)
        
        if ga_face:
            print(f"  GA face: {ga_face}")
        else:
            print(f"  GA face: Not detected")
            
        if gaga_face:
            print(f"  GAGA face: {gaga_face}")
        else:
            print(f"  GAGA face: Not detected")
        
        # Draw face info on frames
        ga_vis = draw_face_info(ga_frame, ga_face, f"GA {subject}")
        gaga_vis = draw_face_info(gaga_frame, gaga_face, f"GAGA {subject}")
        
        # Resize gaga to match ga height for side-by-side comparison
        ga_height, ga_width = ga_vis.shape[:2]
        gaga_height, gaga_width = gaga_vis.shape[:2]
        
        # Scale gaga to match ga height
        scale = ga_height / gaga_height
        new_gaga_width = int(gaga_width * scale)
        gaga_vis_resized = cv2.resize(gaga_vis, (new_gaga_width, ga_height))
        
        # Create side-by-side comparison
        combined = np.hstack([ga_vis, gaga_vis_resized])
        
        # Add separator line
        separator_x = ga_width
        cv2.line(combined, (separator_x, 0), (separator_x, ga_height), (255, 255, 255), 5)
        
        # Save the visualization
        output_path = output_dir / f'chin_comparison_{subject}.jpg'
        cv2.imwrite(str(output_path), combined)
        print(f"  Saved visualization to: {output_path}")
        
        # Also save individual frames for closer inspection
        cv2.imwrite(str(output_dir / f'ga_{subject}.jpg'), ga_vis)
        cv2.imwrite(str(output_dir / f'gaga_{subject}.jpg'), gaga_vis)
        
    print(f"\nAll visualizations saved to: {output_dir}")

if __name__ == "__main__":
    visualize_subject_104()
