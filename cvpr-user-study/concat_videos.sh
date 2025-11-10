#!/bin/bash

# Trap SIGINT (Ctrl+C) and SIGTERM to kill all background jobs
trap 'echo "Stopping all jobs..."; kill $(jobs -p) 2>/dev/null; wait; exit' SIGINT SIGTERM

base_path="final_cropped_rotated"
labelled_path="labeled_videos"
out_path="final_videos_concat"

# crop = 0 to not crop bottom part
# Set max parallel jobs (adjust based on your CPU cores and memory)
MAX_JOBS=8

mkdir -p $out_path
mkdir -p $labelled_path

subjects=("074" "104" "218" "253" "264" "302" "304" "306" "460")
competing_methods=("ga" "4dgs" "hr" "ar" "gaga" "lam")

# First, create all labeled videos (non-parallel to avoid conflicts)
echo "Creating labeled videos..."
font_file="font/BAHNSCHRIFT.TTF"
text_fontsize=60
text_height=100
video_width=512
crop_size=0
height=612

# Create label bars once (shared across all jobs)
ffmpeg -f lavfi -y -i color=c=black:s=${video_width}x${text_height} \
-vf "drawtext=fontfile='${font_file}':fontsize=${text_fontsize}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:text='Method A'" \
-t 1 -c:v libx264 label_A.mp4 2>/dev/null

ffmpeg -f lavfi -y -i color=c=black:s=${video_width}x${text_height} \
-vf "drawtext=fontfile='${font_file}':fontsize=${text_fontsize}:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:text='Method B'" \
-t 1 -c:v libx264 label_B.mp4 2>/dev/null

# Create spacer once (shared across all jobs)
ffmpeg -f lavfi -y -i color=c=black:s=20x${height} -t 10 spacer.mp4 2>/dev/null

# Create labeled videos for all subjects/sentences/methods
for subject in "${subjects[@]}"; do
    for sen in "A" "B"; do
        ours_method="finetune15"
        ours_path=$base_path/$ours_method
        ours_name="${ours_method}_heygen_${sen}_${subject}"
        video_ours=$ours_path/$ours_name
        
        mkdir -p $labelled_path/${ours_method}
        
        # Create labeled "ours" video once (reused across all competing methods)
        out_video_ours_A=$labelled_path/${ours_method}/labeledA_${ours_name}
        out_video_ours_B=$labelled_path/${ours_method}/labeledB_${ours_name}
        
        if [ ! -f "$out_video_ours_A.mp4" ]; then
            ffmpeg -i label_A.mp4 -i $video_ours.mp4 -y -filter_complex \
            "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
            -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_ours_A.mp4 2>/dev/null
        fi
        
        if [ ! -f "$out_video_ours_B.mp4" ]; then
            ffmpeg -i label_B.mp4 -i $video_ours.mp4 -y -filter_complex \
            "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
            -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_ours_B.mp4 2>/dev/null
        fi
        
        # Create labeled competing method videos
        for competing_method in "${competing_methods[@]}"; do
            competing_path=$base_path/$competing_method
            competing_name="${competing_method}_heygen_${sen}_${subject}_rotated"
            video_competing=$competing_path/$competing_name
            
            mkdir -p $labelled_path/${competing_method}
            
            out_video_competing_A=$labelled_path/${competing_method}/labeledA_${competing_name}
            out_video_competing_B=$labelled_path/${competing_method}/labeledB_${competing_name}
            
            if [ ! -f "$out_video_competing_A.mp4" ]; then
                ffmpeg -i label_A.mp4 -i $video_competing.mp4 -y -filter_complex \
                "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
                -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_competing_A.mp4 2>/dev/null
            fi
            
            if [ ! -f "$out_video_competing_B.mp4" ]; then
                ffmpeg -i label_B.mp4 -i $video_competing.mp4 -y -filter_complex \
                "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
                -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_competing_B.mp4 2>/dev/null
            fi
        done
        
        echo "Labeled videos created for ${subject}_${sen}"
    done
done

echo "All labeled videos created. Starting concatenation..."

# Now do the concatenations in parallel
for subject in "${subjects[@]}"; do
    for sen in "A" "B"; do
        for competing_method in "${competing_methods[@]}"; do
            
            # Limit concurrent jobs
            while [ $(jobs -r | wc -l) -ge $MAX_JOBS ]; do
                sleep 1
            done
            
            # Run each comparison in background
            (
            ours_method="finetune15"

            ours_name="${ours_method}_heygen_${sen}_${subject}"
            competing_name="${competing_method}_heygen_${sen}_${subject}_rotated"

            out_name="pair_${subject}_${sen}_ours_vs_${competing_method}"
            out_name_swapped="pair_${subject}_${sen}_${competing_method}_vs_ours"

            # Use pre-created labeled videos
            out_video_left=$labelled_path/${ours_method}/labeledA_${ours_name}
            out_video_right=$labelled_path/${competing_method}/labeledB_${competing_name}
            
            out_video_left_swapped=$labelled_path/${competing_method}/labeledA_${competing_name}
            out_video_right_swapped=$labelled_path/${ours_method}/labeledB_${ours_name}

            out=$out_path"/"$out_name
            out_swapped=$out_path"/"$out_name_swapped

            # ------------------ Final horizontal concat (ours vs competing) ------------------

            ffmpeg -i $out_video_left.mp4 -i spacer.mp4 -i $out_video_right.mp4 -y \
            -filter_complex "[0:v][1:v][2:v]hstack=inputs=3" \
            -c:v libx264 -crf 18 -preset slow $out.mp4 2>/dev/null

            # ------------------ Final horizontal concat (competing vs ours) ------------------

            ffmpeg -i $out_video_left_swapped.mp4 -i spacer.mp4 -i $out_video_right_swapped.mp4 -y \
            -filter_complex "[0:v][1:v][2:v]hstack=inputs=3" \
            -c:v libx264 -crf 18 -preset slow $out_swapped.mp4 2>/dev/null
            
            echo "Completed: ${subject}_${sen}_${competing_method}"
            
            ) &  # Run in background

        done
    done
done

# Wait for all background jobs to finish
wait
echo "All video processing completed!"