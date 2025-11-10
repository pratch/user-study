#!/usr/bin/env python3
"""
Video processing script to crop videos to match face-area-to-box-area ratio from reference methods.
Processes videos in FINAL_BASELINES_V2_CRF/<method>/<method>_scale1.5/ directories.
Uses ar and gaga (front versions) as reference for target face ratio.
"""

import os
import subprocess
import cv2
from pathlib import Path
import json
import numpy as np
import mediapipe as mp
import argparse

def get_video_info(video_path):
    """Get video dimensions using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
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
    Detect face in the first frame of the video using MediaPipe.
    Returns the face bounding box (x, y, w, h) or None if no face found.
    MediaPipe provides more accurate face detection including full chin/jaw.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"      Error: Could not open video {video_path}")
        return None
    
    # Get first frame only
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"      Error: Could not read first frame from {video_path}")
        return None
    
    # Initialize MediaPipe Face Detection
    mp_face_detection = mp.solutions.face_detection
    
    with mp_face_detection.FaceDetection(
        model_selection=1,  # 1 for full-range model (better for close-up faces)
        min_detection_confidence=0.5
    ) as face_detection:
        
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(frame_rgb)
        
        if results.detections:
            # Take the first/most confident detection
            detection = results.detections[0]
            
            # Get bounding box in relative coordinates
            bbox = detection.location_data.relative_bounding_box
            
            # Convert to absolute pixel coordinates
            h, w, _ = frame.shape
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            box_w = int(bbox.width * w)
            box_h = int(bbox.height * h)
            
            # Ensure coordinates are within frame bounds
            x = max(0, x)
            y = max(0, y)
            box_w = min(box_w, w - x)
            box_h = min(box_h, h - y)
            
            return (x, y, box_w, box_h)
    
    print(f"      Warning: No faces detected in {video_path}")
    return None

def calculate_face_ratio_and_position(video_path):
    """
    Calculate the face-area-to-frame-area ratio and normalized chin position for a video.
    Returns (ratio, normalized_y_chin) or (None, None) if face not detected.
    """
    width, height = get_video_info(video_path)
    if width is None or height is None:
        return None, None
    
    face_bbox = detect_face_in_video(video_path)
    if face_bbox is None:
        return None, None
    
    face_x, face_y, face_w, face_h = face_bbox
    face_area = face_w * face_h
    frame_area = width * height
    
    ratio = face_area / frame_area
    
    # Calculate normalized y position of chin (bottom of face box)
    # (0 to 1, where 0 is top of frame, 1 is bottom of frame)
    face_chin_y = face_y + face_h
    normalized_y = face_chin_y / height
    
    return ratio, normalized_y

def get_reference_for_subject(base_dir, sentence, subject):
    """
    Get face ratio and chin position for a specific subject from reference methods (ar and gaga).
    Averages across ar and gaga for the same subject+sentence combination.
    Returns (avg_ratio, avg_normalized_chin_y) or (None, None) if failed.
    """
    reference_methods = [
        ('ar', 'ar'),
        ('gaga', 'gaga')
    ]
    
    ratios = []
    y_positions = []
    
    for method, subdir in reference_methods:
        method_dir = base_dir / method / subdir
        if not method_dir.exists():
            continue
        
        # Look for the specific subject video
        video_pattern = f"{method}_heygen_{sentence}_{subject}.mp4"
        video_file = method_dir / video_pattern
        
        if not video_file.exists():
            continue
        
        ratio, normalized_y = calculate_face_ratio_and_position(video_file)
        if ratio is not None and normalized_y is not None:
            ratios.append(ratio)
            y_positions.append(normalized_y)
    
    if not ratios or not y_positions:
        return None, None
    
    avg_ratio = sum(ratios) / len(ratios)
    avg_y = sum(y_positions) / len(y_positions)
    
    return avg_ratio, avg_y

def calculate_crop_box_for_target_ratio_and_position(video_width, video_height, face_bbox, target_ratio, target_normalized_chin_y):
    """
    Calculate a square crop box that contains the face and achieves both:
    1. The target face-to-box ratio
    2. The target normalized Y position for the chin (bottom of face)
    Returns (crop_x, crop_y, crop_size) or None if not possible.
    """
    if face_bbox is None:
        # Fallback to center crop
        crop_size = min(video_width, video_height)
        crop_x = (video_width - crop_size) // 2
        crop_y = (video_height - crop_size) // 2
        return crop_x, crop_y, crop_size
    
    face_x, face_y, face_w, face_h = face_bbox
    face_area = face_w * face_h
    
    # Calculate the box size needed to achieve target ratio
    # face_area / box_area = target_ratio
    # box_area = face_area / target_ratio
    target_box_area = face_area / target_ratio
    target_box_size = int(np.sqrt(target_box_area))
    
    # Ensure box size doesn't exceed video dimensions
    max_box_size = min(video_width, video_height)
    crop_size = min(target_box_size, max_box_size)
    
    # If calculated box is too small, use a minimum size
    min_box_size = max(face_w, face_h) * 1.5  # At least 1.5x the face size
    crop_size = max(crop_size, int(min_box_size))
    crop_size = min(crop_size, max_box_size)
    
    # Calculate face center (for horizontal positioning) and chin position
    face_center_x = face_x + face_w // 2
    face_chin_y = face_y + face_h  # Bottom of face box
    
    # Center the crop box horizontally around the face
    crop_x = face_center_x - crop_size // 2
    
    # Position the crop box vertically so that the chin is at target_normalized_chin_y
    # We want: (face_chin_y - crop_y) / crop_size = target_normalized_chin_y
    # So: crop_y = face_chin_y - (target_normalized_chin_y * crop_size)
    crop_y = int(face_chin_y - (target_normalized_chin_y * crop_size))
    
    # Adjust if crop box goes outside video bounds
    if crop_x < 0:
        crop_x = 0
    elif crop_x + crop_size > video_width:
        crop_x = video_width - crop_size
    
    if crop_y < 0:
        crop_y = 0
    elif crop_y + crop_size > video_height:
        crop_y = video_height - crop_size
    
    return crop_x, crop_y, crop_size

def crop_and_resize_video(input_path, output_path, crop_x, crop_y, crop_size):
    """Crop video to square and resize to 512x512."""
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-vf', f'crop={crop_size}:{crop_size}:{crop_x}:{crop_y},scale=512:512:flags=lanczos',
        '-c:v', 'libx264', '-crf', '10', '-preset', 'veryslow',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path}: {e}")
        return False

def reencode_video_no_crop(input_path, output_path):
    """Re-encode video without cropping (for videos already at 512x512 like gaga and ar)."""
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-c:v', 'libx264', '-crf', '10', '-preset', 'veryslow',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'copy',
        '-y',
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {input_path}: {e}")
        return False

def load_crop_cache(cache_file):
    """Load crop cache from JSON file."""
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load cache file {cache_file}: {e}")
    return {}

def save_crop_cache(cache_file, cache_data):
    """Save crop cache to JSON file."""
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache_data, indent=2, fp=f)
    except IOError as e:
        print(f"Warning: Could not save cache file {cache_file}: {e}")

def process_videos(methods_to_process=None):
    """Main function to process all videos.
    
    Args:
        methods_to_process: List of method names to process. If None, processes default methods.
    """
    base_dirs = [
        Path(__file__).parent / 'FINAL_BASELINES_V2_CRF',
        Path(__file__).parent / 'FINAL_BRIGHT'
    ]
    reference_base_dir = Path(__file__).parent / 'FINAL_BASELINES_V2_CRF'  # Always use this for reference
    output_front_dir = Path(__file__).parent / 'cropped_front'
    output_rotated_dir = Path(__file__).parent / 'cropped_rotated'
    cache_dir = Path(__file__).parent / 'crop_cache'
    
    if not reference_base_dir.exists():
        print(f"Error: Reference directory {reference_base_dir} not found")
        return
    
    # Create output and cache directories
    output_front_dir.mkdir(exist_ok=True)
    output_rotated_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)
    
    # Default methods to process if none specified
    if methods_to_process is None:
        methods_to_process = ['ga', '4dgs', 'hr', 'lam', 'gaga', 'ar']
    
    print(f"Methods to process: {', '.join(methods_to_process)}")
    
    total_processed = 0
    total_errors = 0
    
    for method in methods_to_process:
        print(f"\n{'='*60}")
        print(f"Processing method: {method}")
        print(f"{'='*60}")
        
        # Check if this is a reference method (gaga or ar) that needs re-encoding only
        is_reference_method = method in ['gaga', 'ar']
        
        # Load or initialize cache for this method (skip cache for reference methods)
        if not is_reference_method:
            cache_file = cache_dir / f"{method}_crop_cache.json"
            crop_cache = load_crop_cache(cache_file)
        else:
            print(f"  Note: {method} is a reference method - will re-encode without cropping")
        
        # Try to find method in any of the base directories
        method_found = False
        for base_dir in base_dirs:
            method_dir = base_dir / method
            if not method_dir.exists():
                continue
            
            method_found = True
            print(f"\n  Found method in: {base_dir.name}")
            
            # Process front videos (_scale1.5 or just method name for reference methods)
            print(f"  --- Processing FRONT videos from {base_dir.name} ---")
            
            # Reference methods (gaga, ar) use different directory structure
            if is_reference_method:
                input_method_dir = base_dir / method / method
            else:
                input_method_dir = base_dir / method / f"{method}_scale1.5"
            
            if not input_method_dir.exists():
                print(f"    Warning: Input directory {input_method_dir} not found, skipping front videos...")
            else:
                # Output directory: cropped_front/<method>/
                output_method_dir = output_front_dir / method
                output_method_dir.mkdir(parents=True, exist_ok=True)
                
                # Find all video files
                video_files = list(input_method_dir.glob('*.mp4'))
                print(f"    Found {len(video_files)} video files in front")
                
                for video_file in sorted(video_files):
                    print(f"\n    Processing {video_file.name}...")
                    
                    # For reference methods (gaga, ar), just re-encode without cropping
                    if is_reference_method:
                        # Output file (remove _scale1.5 suffix if present)
                        output_name = video_file.name.replace('_scale1.5', '')
                        output_file = output_method_dir / output_name
                        
                        print(f"      Re-encoding without crop (already 512x512)")
                        
                        # Re-encode without cropping
                        if reencode_video_no_crop(video_file, output_file):
                            total_processed += 1
                            print(f"      ✓ Successfully processed to {output_file}")
                        else:
                            total_errors += 1
                            print(f"      ✗ Failed to process")
                        continue
                    
                    # Extract subject info from filename (e.g., ga_heygen_A_104_scale1.5.mp4 -> A, 104)
                    filename = video_file.stem  # Remove .mp4
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        sentence = parts[2]  # A or B
                        subject = parts[3].replace('scale1.5', '').replace('scale15', '')  # Handle different formats
                    else:
                        print(f"      Warning: Could not parse filename {video_file.name}, skipping")
                        total_errors += 1
                        continue
                    
                    # Create cache key for this video
                    cache_key = f"{sentence}_{subject}"
                    
                    # Check if we have cached crop parameters
                    if cache_key in crop_cache:
                        print(f"      Using cached crop parameters for {cache_key}")
                        cached = crop_cache[cache_key]
                        target_ratio = cached['target_ratio']
                        target_y_position = cached['target_y_position']
                        face_bbox = tuple(cached['face_bbox']) if cached['face_bbox'] else None
                        crop_x = cached['crop_x']
                        crop_y = cached['crop_y']
                        crop_size = cached['crop_size']
                        width = cached['video_width']
                        height = cached['video_height']
                    else:
                        # Get reference values for this specific subject (always from FINAL_BASELINES_V2_CRF)
                        target_ratio, target_y_position = get_reference_for_subject(reference_base_dir, sentence, subject)
                        if target_ratio is None or target_y_position is None:
                            print(f"      Warning: Could not get reference for {sentence}_{subject}, skipping")
                            total_errors += 1
                            continue
                        
                        print(f"      Subject: {sentence}_{subject}")
                        print(f"      Target ratio: {target_ratio:.4f}, Target chin Y: {target_y_position:.4f}")
                        
                        # Get video dimensions
                        width, height = get_video_info(video_file)
                        if width is None or height is None:
                            print(f"      Error: Could not get video info")
                            total_errors += 1
                            continue
                        
                        print(f"      Video size: {width}x{height}")
                        
                        # Detect face
                        face_bbox = detect_face_in_video(video_file)
                        if face_bbox:
                            face_x, face_y, face_w, face_h = face_bbox
                            face_area = face_w * face_h
                            current_ratio = face_area / (width * height)
                            face_chin_y = face_y + face_h
                            current_chin_pos = face_chin_y / height
                            print(f"      Face detected at ({face_x}, {face_y}) size {face_w}x{face_h}")
                            print(f"      Current face ratio: {current_ratio:.4f}, Target: {target_ratio:.4f}")
                            print(f"      Current chin Y position: {current_chin_pos:.4f}, Target: {target_y_position:.4f}")
                        else:
                            print(f"      Warning: No face detected, using center crop")
                        
                        # Calculate crop box
                        crop_result = calculate_crop_box_for_target_ratio_and_position(width, height, face_bbox, target_ratio, target_y_position)
                        if crop_result is None:
                            print(f"      Error: Could not calculate crop region")
                            total_errors += 1
                            continue
                        
                        crop_x, crop_y, crop_size = crop_result
                        
                        # Cache the results
                        crop_cache[cache_key] = {
                            'target_ratio': target_ratio,
                            'target_y_position': target_y_position,
                            'face_bbox': list(face_bbox) if face_bbox else None,
                            'crop_x': crop_x,
                            'crop_y': crop_y,
                            'crop_size': crop_size,
                            'video_width': width,
                            'video_height': height
                        }
                    
                    # Calculate actual ratio and chin position after cropping
                    if face_bbox:
                        face_x, face_y, face_w, face_h = face_bbox
                        actual_face_area = face_w * face_h
                        actual_box_area = crop_size * crop_size
                        actual_ratio = actual_face_area / actual_box_area
                        # Calculate the normalized chin Y position within the crop box
                        face_chin_y = face_y + face_h
                        face_chin_y_in_crop = face_chin_y - crop_y
                        actual_chin_pos = face_chin_y_in_crop / crop_size
                        print(f"      Crop box: ({crop_x}, {crop_y}) size {crop_size}x{crop_size}")
                        print(f"      Resulting face ratio: {actual_ratio:.4f}, chin Y position: {actual_chin_pos:.4f}")
                    else:
                        print(f"      Crop box: ({crop_x}, {crop_y}) size {crop_size}x{crop_size}")
                    
                    # Output file (remove _scale1.5 suffix if present)
                    output_name = video_file.name.replace('_scale1.5', '')
                    output_file = output_method_dir / output_name
                    
                    # Crop and resize
                    if crop_and_resize_video(video_file, output_file, crop_x, crop_y, crop_size):
                        total_processed += 1
                        print(f"      ✓ Successfully processed to {output_file}")
                    else:
                        total_errors += 1
                        print(f"      ✗ Failed to process")
                
                # Save cache after processing front videos from this base directory
                if not is_reference_method:
                    save_crop_cache(cache_file, crop_cache)
                    print(f"\n    Saved crop cache to {cache_file}")
            
            # Process rotated videos (_rotated_scale1.5 or _rotated for reference methods)
            print(f"  --- Processing ROTATED videos from {base_dir.name} ---")
            
            # Reference methods (gaga, ar) might use different directory structure
            if is_reference_method:
                # Try both possible naming conventions
                input_rotated_dir = base_dir / method / f"{method}_rotated"
                if not input_rotated_dir.exists():
                    input_rotated_dir = base_dir / method / f"{method}_rotated_scale1.5"
            else:
                input_rotated_dir = base_dir / method / f"{method}_rotated_scale1.5"
            
            if not input_rotated_dir.exists():
                print(f"    Warning: Rotated input directory {input_rotated_dir} not found, skipping rotated videos...")
            else:
                # Output directory: cropped_rotated/<method>/
                output_method_rotated_dir = output_rotated_dir / method
                output_method_rotated_dir.mkdir(parents=True, exist_ok=True)
                
                # Find all rotated video files
                rotated_video_files = list(input_rotated_dir.glob('*.mp4'))
                print(f"    Found {len(rotated_video_files)} video files in rotated")
                
                for video_file in sorted(rotated_video_files):
                    print(f"\n    Processing {video_file.name}...")
                    
                    # For reference methods (gaga, ar), just re-encode without cropping
                    if is_reference_method:
                        # Output file (replace _rotated_scale1.5 with _rotated)
                        output_name = video_file.name.replace('_rotated_scale1.5', '_rotated')
                        output_file = output_method_rotated_dir / output_name
                        
                        print(f"      Re-encoding without crop (already 512x512)")
                        
                        # Re-encode without cropping
                        if reencode_video_no_crop(video_file, output_file):
                            total_processed += 1
                            print(f"      ✓ Successfully processed to {output_file}")
                        else:
                            total_errors += 1
                            print(f"      ✗ Failed to process")
                        continue
                    
                    # Extract subject info from filename (e.g., ga_heygen_A_104_rotated_scale1.5.mp4 -> A, 104)
                    filename = video_file.stem  # Remove .mp4
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        sentence = parts[2]  # A or B
                        subject = parts[3]  # Should be like "104"
                    else:
                        print(f"      Warning: Could not parse filename {video_file.name}, skipping")
                        total_errors += 1
                        continue
                    
                    # Create cache key
                    cache_key = f"{sentence}_{subject}"
                    
                    # Check if we have cached crop parameters from front video
                    if cache_key not in crop_cache:
                        print(f"      Warning: No cached crop parameters for {cache_key}, skipping")
                        total_errors += 1
                        continue
                    
                    print(f"      Using cached crop parameters from front video for {cache_key}")
                    cached = crop_cache[cache_key]
                    crop_x = cached['crop_x']
                    crop_y = cached['crop_y']
                    crop_size = cached['crop_size']
                    
                    print(f"      Applying crop: ({crop_x}, {crop_y}) size {crop_size}x{crop_size}")
                    
                    # Output file (replace _rotated_scale1.5 with _rotated)
                    output_name = video_file.name.replace('_rotated_scale1.5', '_rotated')
                    output_file = output_method_rotated_dir / output_name
                    
                    # Crop and resize using the same parameters from front video
                    if crop_and_resize_video(video_file, output_file, crop_x, crop_y, crop_size):
                        total_processed += 1
                        print(f"      ✓ Successfully processed to {output_file}")
                    else:
                        total_errors += 1
                        print(f"      ✗ Failed to process")
        
        if not method_found:
            print(f"  Warning: Method '{method}' not found in any base directory, skipping...")
    
    print(f"\n{'='*60}")
    print(f"=== Processing Summary ===")
    print(f"{'='*60}")
    print(f"Videos processed: {total_processed}")
    print(f"Errors: {total_errors}")
    print(f"Input directories searched:")
    for base_dir in base_dirs:
        print(f"  - {base_dir}")
    print(f"Output directories:")
    print(f"  Front videos: {output_front_dir}")
    print(f"  Rotated videos: {output_rotated_dir}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Crop and resize videos to match face framing from reference methods.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all default methods (ga, 4dgs, hr, lam, gaga, ar)
  python crop_face_matched.py
  
  # Process specific methods
  python crop_face_matched.py --methods ga hr
  
  # Process a single method
  python crop_face_matched.py --methods lam
  
  # Process reference methods only (gaga and ar will be re-encoded without cropping)
  python crop_face_matched.py --methods gaga ar
  
  # Process a new method
  python crop_face_matched.py --methods my_new_method
        """
    )
    parser.add_argument(
        '--methods', '-m',
        nargs='+',
        help='Specify which methods to process (e.g., ga 4dgs hr lam). If not specified, processes all default methods.',
        metavar='METHOD'
    )
    
    args = parser.parse_args()
    
    # Check if required tools are available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg and ffprobe are required but not found in PATH")
        print("Please install ffmpeg: sudo apt-get install ffmpeg")
        exit(1)
    
    # Process videos with specified methods
    process_videos(methods_to_process=args.methods)
