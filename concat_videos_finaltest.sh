base_path="final_videos_raw"
out_path="final_videos_concat"

subject="218"
sen="A"

ours_path=$base_path"/data_brightfinal_viewdep_superres"
ga_path=$base_path"/data_GA_final_amp12_front"

ours_name="${sen}_synctalk_222200037_nersemble_${subject}_2_200000"
ga_name="${subject}_liveport_amp12_${sen}"

out_name="out_${subject}_${sen}_ours_vs_ga"

video_left=$ours_path/$ours_name
video_right=$ga_path/$ga_name

out_video_left=$ours_path/labeled_$ours_name
out_video_right=$ga_path/labeled_$ga_name

out=$out_path"/"$out_name

# for voodoo
# ffmpeg -i $video4.mp4 -y -vf "pad=550:802:(550-512)/2:(802-512)/2:black" ${out_video4}_padded.mp4

font_style="fontfile='font/BAHNSCHRIFT.TTF':fontsize=62:x=(w-text_w)/2:y=10:fontcolor=white:borderw=3:bordercolor=black"

echo $out_video_left

# crop bottom (white space for GA)
crop_size=170
crop_filter="crop=in_w:in_h-$crop_size:0:0"

# fixed: preserve quality with libx264 (need ffmpeg 7 via conda -c conda-forge)
ffmpeg -i $video_left.mp4 -y -vf "$crop_filter,drawtext=text='Method A':$font_style" -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_left.mp4
ffmpeg -i $video_right.mp4 -y -vf "$crop_filter,drawtext=text='Method B':$font_style" -c:v libx264 -crf 18 -preset veryslow -c:a copy $out_video_right.mp4

height=802
ffmpeg -f lavfi -y -i color=c=black:s=20x$(($height - $crop_size)) -t 10 spacer.mp4

ffmpeg -i $out_video_left.mp4 -y -i spacer.mp4 -i $out_video_right.mp4 \
-filter_complex "[0:v][1:v][2:v]hstack=inputs=3" \
-c:v libx264 -crf 18 -preset slow $out.mp4
