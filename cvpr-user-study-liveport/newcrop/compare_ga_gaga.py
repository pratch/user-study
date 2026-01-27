#!/usr/bin/env python3
"""
Generate side-by-side comparison images of cropped GA vs original GAGA
for all subjects with face detection markers.
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

def draw_markers(frame, face_bbox, label):
    """Draw face markers on frame."""
    if face_bbox is None:
        return frame
    
    frame_copy = frame.copy()
    height, width = frame.shape[:2]
    x, y, w, h = face_bbox
    
    # Draw face bounding box (green)
    cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # Draw chin position (red horizontal line)
    chin_y = y + h
    cv2.line(frame_copy, (0, chin_y), (width, chin_y), (0, 0, 255), 2)
    
    # Draw center of face (blue circle)
    center_x = x + w // 2
    center_y = y + h // 2
    cv2.circle(frame_copy, (center_x, center_y), 8, (255, 0, 0), -1)
    
    # Calculate metrics
    chin_normalized = chin_y / height
    center_normalized = center_y / height
    face_area = w * h
    frame_area = width * height
    face_ratio = face_area / frame_area
    
    # Add text info
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    
    info_lines = [
        f"{label}",
        f"Size: {width}x{height}",
        f"Face: {w}x{h}",
        f"Chin Y: {chin_normalized:.3f}",
        f"Center Y: {center_normalized:.3f}",
        f"Ratio: {face_ratio:.3f}"
    ]
    
    y_offset = 20
    for line in info_lines:
        # White outline
        cv2.putText(frame_copy, line, (10, y_offset), font, font_scale, (255, 255, 255), thickness + 1, cv2.LINE_AA)
        # Black text
        cv2.putText(frame_copy, line, (10, y_offset), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)
        y_offset += 25
    
    return frame_copy

def get_first_frame(video_path):
    """Get the first frame from a video."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    return frame

def compare_all_subjects():
    """Generate comparison images for all subjects."""
    base_dir = Path(__file__).parent
    ga_cropped_dir = base_dir / 'cropped' / 'ga' / 'front'
    gaga_dir = base_dir / 'FINAL_BASELINES_V2_CRF' / 'gaga' / 'gaga'
    output_dir = base_dir / 'compare_ga_gaga'
    
    output_dir.mkdir(exist_ok=True)
    
    if not ga_cropped_dir.exists():
        print(f"Error: GA cropped directory not found: {ga_cropped_dir}")
        return
    
    if not gaga_dir.exists():
        print(f"Error: GAGA directory not found: {gaga_dir}")
        return
    
    # Get all GA cropped videos
    ga_videos = sorted(ga_cropped_dir.glob('*.mp4'))
    
    print(f"Found {len(ga_videos)} GA cropped videos")
    print(f"Generating comparisons...\n")
    
    successful = 0
    failed = 0
    
    for ga_video in ga_videos:
        # Extract subject info (e.g., ga_heygen_A_104.mp4 -> A_104)
        filename = ga_video.name
        # Parse: ga_heygen_{sentence}_{subject}.mp4
        parts = filename.replace('.mp4', '').split('_')
        if len(parts) >= 4:
            sentence = parts[2]  # A or B
            subject = parts[3]   # 074, 104, etc.
            subject_id = f"{sentence}_{subject}"
        else:
            print(f"  Warning: Could not parse filename: {filename}")
            continue
        
        # Find corresponding gaga video
        gaga_video = gaga_dir / f"gaga_heygen_{sentence}_{subject}.mp4"
        
        if not gaga_video.exists():
            print(f"  Warning: GAGA video not found for {subject_id}: {gaga_video}")
            failed += 1
            continue
        
        print(f"Processing {subject_id}...")
        
        # Get first frames
        ga_frame = get_first_frame(ga_video)
        gaga_frame = get_first_frame(gaga_video)
        
        if ga_frame is None or gaga_frame is None:
            print(f"  Error: Could not read frames for {subject_id}")
            failed += 1
            continue
        
        # Detect faces
        ga_face = detect_face_in_frame(ga_frame)
        gaga_face = detect_face_in_frame(gaga_frame)
        
        if ga_face is None:
            print(f"  Warning: No face detected in GA for {subject_id}")
        if gaga_face is None:
            print(f"  Warning: No face detected in GAGA for {subject_id}")
        
        # Draw markers
        ga_vis = draw_markers(ga_frame, ga_face, f"GA Cropped")
        gaga_vis = draw_markers(gaga_frame, gaga_face, f"GAGA Original")
        
        # Both should be 512x512 now, so we can stack horizontally
        combined = np.hstack([ga_vis, gaga_vis])
        
        # Add separator line
        separator_x = 512
        cv2.line(combined, (separator_x, 0), (separator_x, 512), (255, 255, 255), 3)
        
        # Add title
        title_frame = np.ones((60, 1024, 3), dtype=np.uint8) * 255
        title_text = f"Subject {subject_id} Comparison: GA Cropped (Left) vs GAGA Original (Right)"
        cv2.putText(title_frame, title_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
        
        # Combine title and images
        final = np.vstack([title_frame, combined])
        
        # Save
        output_path = output_dir / f'comparison_{subject_id}.jpg'
        cv2.imwrite(str(output_path), final)
        
        # Print face info if detected
        if ga_face and gaga_face:
            ga_x, ga_y, ga_w, ga_h = ga_face
            gaga_x, gaga_y, gaga_w, gaga_h = gaga_face
            
            ga_chin_norm = (ga_y + ga_h) / 512
            gaga_chin_norm = (gaga_y + gaga_h) / 512
            
            ga_center_norm = (ga_y + ga_h / 2) / 512
            gaga_center_norm = (gaga_y + gaga_h / 2) / 512
            
            chin_diff = abs(ga_chin_norm - gaga_chin_norm)
            center_diff = abs(ga_center_norm - gaga_center_norm)
            
            print(f"  GA chin Y: {ga_chin_norm:.3f}, GAGA chin Y: {gaga_chin_norm:.3f}, diff: {chin_diff:.3f}")
            print(f"  GA center Y: {ga_center_norm:.3f}, GAGA center Y: {gaga_center_norm:.3f}, diff: {center_diff:.3f}")
        
        print(f"  ✓ Saved to {output_path.name}\n")
        successful += 1
    
    print(f"\n{'='*80}")
    print(f"Comparison complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*80}")

if __name__ == "__main__":
    compare_all_subjects()
