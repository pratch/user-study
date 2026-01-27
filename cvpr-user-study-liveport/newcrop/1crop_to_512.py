#!/usr/bin/env python3
"""
Video processing script to crop portrait videos to square and resize to 512x512.
Uses face detection to ensure faces are included in the cropped region.
Processes videos in final_videos_raw/<method>_rotated/ directories.
"""

import os
import shutil
import subprocess
import cv2
from pathlib import Path
import json
import numpy as np

def get_video_info(video_path):
    """Get video dimensions and other info using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Find video stream
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                width = int(stream['width'])
                height = int(stream['height'])
                return width, height
        
        return None, None
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        print(f"Error getting video info for {video_path}: {e}")
        return None, None

def detect_face_in_video(video_path, num_samples=10):
    """
    Detect face in video by sampling multiple frames.
    Returns the average face bounding box (x, y, w, h) or None if no face found.
    """
    # Initialize face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"      Error: Could not open video {video_path}")
        return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        return None
    
    # Sample frames evenly throughout the video
    frame_indices = np.linspace(0, total_frames - 1, min(num_samples, total_frames), dtype=int)
    
    detected_faces = []
    
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            continue
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Take the largest face if multiple faces detected
        if len(faces) > 0:
            # Sort by area and take the largest
            faces_with_area = [(x, y, w, h, w*h) for x, y, w, h in faces]
            faces_with_area.sort(key=lambda x: x[4], reverse=True)
            x, y, w, h, _ = faces_with_area[0]
            detected_faces.append((x, y, w, h))
    
    cap.release()
    
    if not detected_faces:
        print(f"      Warning: No faces detected in {video_path}")
        return None
    
    # Calculate average face position
    avg_x = sum(face[0] for face in detected_faces) / len(detected_faces)
    avg_y = sum(face[1] for face in detected_faces) / len(detected_faces)
    avg_w = sum(face[2] for face in detected_faces) / len(detected_faces)
    avg_h = sum(face[3] for face in detected_faces) / len(detected_faces)
    
    return (int(avg_x), int(avg_y), int(avg_w), int(avg_h))

def calculate_crop_region(video_width, video_height, face_bbox=None):
    """
    Calculate the square crop region that includes the face and maximizes the use of video width.
    Returns (crop_x, crop_y, crop_size) or None if not possible.
    """
    # The crop size should be the minimum of width and height to make it square
    crop_size = min(video_width, video_height)
    
    if face_bbox is None:
        # Fallback to center crop if no face detected
        crop_x = (video_width - crop_size) // 2
        crop_y = (video_height - crop_size) // 2
        return crop_x, crop_y, crop_size
    
    face_x, face_y, face_w, face_h = face_bbox
    
    # Calculate face center
    face_center_x = face_x + face_w // 2
    face_center_y = face_y + face_h // 2
    
    # For portrait videos, we want to maximize width usage, so crop_size = video_width
    if video_height > video_width:
        crop_size = video_width
        crop_x = 0  # Use full width
        
        # Calculate Y position to include the face
        # Try to center the crop around the face, but ensure face is fully included
        ideal_crop_y = face_center_y - crop_size // 2
        
        # Make sure the entire face is included with some padding
        face_padding = max(face_w, face_h) // 4  # 25% padding around face
        min_crop_y = max(0, face_y + face_h + face_padding - crop_size)
        max_crop_y = min(video_height - crop_size, face_y - face_padding)
        
        # Clamp the ideal position to valid range
        crop_y = max(min_crop_y, min(max_crop_y, ideal_crop_y))
        
        # Final safety check
        crop_y = max(0, min(video_height - crop_size, crop_y))
        
    else:
        # For landscape or square videos, center crop
        crop_x = (video_width - crop_size) // 2
        crop_y = (video_height - crop_size) // 2
    
    return crop_x, crop_y, crop_size

def is_portrait(width, height):
    """Check if video is portrait (height > width)."""
    return height > width

def is_square_512(width, height):
    """Check if video is already 512x512."""
    return width == 512 and height == 512

def crop_and_resize_video(input_path, output_path, width, height, face_bbox=None):
    """Crop video to square (with face detection) and resize to 512x512."""
    # Calculate crop region based on face detection
    crop_region = calculate_crop_region(width, height, face_bbox)
    if crop_region is None:
        print(f"      Error: Could not calculate crop region")
        return False
    
    crop_x, crop_y, crop_size = crop_region
    
    # FFmpeg command to crop and resize to 512x512
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-vf', f'crop={crop_size}:{crop_size}:{crop_x}:{crop_y},scale=512:512:flags=lanczos',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'slow',
        '-c:a', 'copy',  # Copy audio without re-encoding
        '-y',  # Overwrite output file if it exists
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path}: {e}")
        return False

def copy_video(input_path, output_path):
    """Copy video without processing."""
    try:
        shutil.copy2(input_path, output_path)
        return True
    except Exception as e:
        print(f"Error copying {input_path}: {e}")
        return False

def process_videos():
    """Main function to process all videos."""
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'final_videos_raw'
    output_dir = base_dir / 'final_videos_cropped_512'
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Find all directories ending with '_rotated'
    rotated_dirs = [d for d in input_dir.iterdir() 
                   if d.is_dir() and d.name.endswith('_rotated')]
    
    print(f"Found {len(rotated_dirs)} method directories to process:")
    for d in rotated_dirs:
        print(f"  - {d.name}")
    
    total_processed = 0
    total_copied = 0
    total_errors = 0
    
    for method_dir in rotated_dirs:
        print(f"\nProcessing {method_dir.name}...")
        
        # Create corresponding output directory
        output_method_dir = output_dir / method_dir.name
        output_method_dir.mkdir(exist_ok=True)
        
        # Find all video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
        video_files = [f for f in method_dir.iterdir() 
                      if f.is_file() and f.suffix.lower() in video_extensions]
        
        print(f"  Found {len(video_files)} video files")
        
        for video_file in video_files:
            print(f"    Processing {video_file.name}...")
            
            # Get video dimensions
            width, height = get_video_info(video_file)
            if width is None or height is None:
                print(f"      Error: Could not get video info")
                total_errors += 1
                continue
            
            output_file = output_method_dir / video_file.name
            
            # Check if already 512x512
            if is_square_512(width, height):
                print(f"      Already 512x512, copying...")
                if copy_video(video_file, output_file):
                    total_copied += 1
                else:
                    total_errors += 1
            # Check if portrait
            elif is_portrait(width, height):
                print(f"      Portrait {width}x{height}, detecting face and cropping...")
                
                # Detect face in the video
                face_bbox = detect_face_in_video(video_file)
                if face_bbox:
                    face_x, face_y, face_w, face_h = face_bbox
                    print(f"      Face detected at ({face_x}, {face_y}) size {face_w}x{face_h}")
                else:
                    print(f"      No face detected, using center crop")
                
                if crop_and_resize_video(video_file, output_file, width, height, face_bbox):
                    total_processed += 1
                    print(f"      Successfully processed to 512x512")
                else:
                    total_errors += 1
            else:
                print(f"      Landscape/square {width}x{height}, using center crop...")
                # For non-portrait videos, still process them with center crop
                face_bbox = detect_face_in_video(video_file)
                if crop_and_resize_video(video_file, output_file, width, height, face_bbox):
                    total_processed += 1
                    print(f"      Successfully processed to 512x512")
                else:
                    total_errors += 1
    
    print(f"\n=== Processing Summary ===")
    print(f"Videos processed (cropped/resized with face detection): {total_processed}")
    print(f"Videos copied (already 512x512): {total_copied}")
    print(f"Errors: {total_errors}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    # Check if required tools are available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg and ffprobe are required but not found in PATH")
        print("Please install ffmpeg: sudo apt-get install ffmpeg")
        exit(1)
    
    process_videos()