base_path="final_videos_raw"
out_path="final_videos_concat"

subjects=("074" "104" "218" "253" "264" "302" "304" "306" "460")

for subject in "${subjects[@]}"; do
    for sen in "A" "B"; do

        ours_path=$base_path"/data_brightfinal_viewdep_superres"
        instag_path=$base_path"/data_instag"

        ours_name="${sen}_synctalk_222200037_nersemble_${subject}_2_200000"
        instag_name="livemaytrain${subject}_audio${sen}"

        out_name="pair_${subject}_${sen}_ours_vs_instag"

        video_left=$ours_path/$ours_name
        video_right=$instag_path/$instag_name

        out_video_left=$ours_path/labeledA_$ours_name
        out_video_right=$instag_path/labeledB_$instag_name

        out=$out_path"/"$out_name

        font_file="font/BAHNSCHRIFT.TTF"
        text_fontsize=70
        text_height=100  # height of white label area
        video_width=550  # assumed width of input videos
        crop_size=170    # crop bottom white space
        height=802       # final output height including any pads/spacers

        # ------------------ Create label bars ------------------

        # # Label bar for Method A (left)
        # ffmpeg -f lavfi -y -i color=c=white:s=${video_width}x${text_height} \
        # -vf "drawtext=fontfile='${font_file}':fontsize=${text_fontsize}:fontcolor=black:x=(w-text_w)/2:y=(h-text_h)/2:text='Method A'" \
        # -t 1 -c:v libx264 label_A.mp4

        # # Label bar for Method B (right)
        # ffmpeg -f lavfi -y -i color=c=white:s=${video_width}x${text_height} \
        # -vf "drawtext=fontfile='${font_file}':fontsize=${text_fontsize}:fontcolor=black:x=(w-text_w)/2:y=(h-text_h)/2:text='Method B'" \
        # -t 1 -c:v libx264 label_B.mp4

        # ------------------ Crop videos and stack with labels ------------------

        # # Left video (Method A)
        ffmpeg -i label_A.mp4 -i $video_left.mp4 -y -filter_complex \
        "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
        -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_left.mp4

        # # Right video (Method B)
        ffmpeg -i label_B.mp4 -i $video_right.mp4 -y -filter_complex \
        "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
        -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_right.mp4

        # ------------------ Spacer for visual separation ------------------

        # ffmpeg -f lavfi -y -i color=c=black:s=20x$(($height - $crop_size + $text_height)) -t 10 spacer.mp4

        # ------------------ Final horizontal concat ------------------

        ffmpeg -i $out_video_left.mp4 -i spacer.mp4 -i $out_video_right.mp4 -y \
        -filter_complex "[0:v][1:v][2:v]hstack=inputs=3" \
        -c:v libx264 -crf 18 -preset slow $out.mp4

        # ------------------ Swapped: Instag left, Ours right ------------------

        out_name_swapped="pair_${subject}_${sen}_instag_vs_ours"

        video_left_swapped=$instag_path/$instag_name
        video_right_swapped=$ours_path/$ours_name

        out_video_left_swapped=$instag_path/labeledA_$instag_name
        out_video_right_swapped=$ours_path/labeledB_$ours_name

        out_swapped=$out_path"/"$out_name_swapped

        # # Left video (Method A, now Instag)
        ffmpeg -i label_A.mp4 -i $video_left_swapped.mp4 -y -filter_complex \
        "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
        -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_left_swapped.mp4

        # # Right video (Method B, now Ours)
        ffmpeg -i label_B.mp4 -i $video_right_swapped.mp4 -y -filter_complex \
        "[1:v]crop=in_w:in_h-${crop_size}:0:0[cropped]; [0:v][cropped]vstack=inputs=2" \
        -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_right_swapped.mp4

        # ------------------ Final horizontal concat (swapped) ------------------

        ffmpeg -i $out_video_left_swapped.mp4 -i spacer.mp4 -i $out_video_right_swapped.mp4 -y \
        -filter_complex "[0:v][1:v][2:v]hstack=inputs=3" \
        -c:v libx264 -crf 18 -preset slow $out_swapped.mp4

    done
done
