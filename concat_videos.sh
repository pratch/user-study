base_path="test_videos"
out_path="processed"

video1_name="ours-218A"
video2_name="GA-218A"
video3_name="talkg-218A"
video4_name="voo-218A"
concat_name="concat-218A"

video1=$base_path"/"$video1_name
video2=$base_path"/"$video2_name
video3=$base_path"/"$video3_name
video4=$base_path"/"$video4_name

out_video1=$out_path"/"$video1_name
out_video2=$out_path"/"$video2_name
out_video3=$out_path"/"$video3_name
out_video4=$out_path"/"$video4_name
out_concat=$out_path"/"$concat_name

ffmpeg -i $video4.mp4 -y -vf "pad=550:802:(550-512)/2:(802-512)/2:black" ${out_video4}_padded.mp4

font_style="fontfile='font/BAHNSCHRIFT.TTF':fontsize=62:x=(w-text_w)/2:y=10:fontcolor=white:borderw=3:bordercolor=black"

ffmpeg -i $video1.mp4 -y -vf "drawtext=text='Method A':$font_style" $out_video1.mp4
ffmpeg -i $video2.mp4 -y -vf "drawtext=text='Method B':$font_style" $out_video2.mp4
ffmpeg -i $video3.mp4 -y -vf "drawtext=text='Method C':$font_style" $out_video3.mp4
ffmpeg -i ${out_video4}_padded.mp4 -y -vf "drawtext=text='Method D':$font_style" $out_video4.mp4

ffmpeg -f lavfi -y -i color=c=black:s=20x802 -t 10 spacer.mp4

ffmpeg -i $out_video1.mp4 -y -i spacer.mp4 -i $out_video2.mp4 -i spacer.mp4 -i $out_video3.mp4 -i spacer.mp4 -i $out_video4.mp4 \
-filter_complex "[0:v][1:v][2:v][3:v][4:v][5:v][6:v]hstack=inputs=7" \
-c:v libx264 -crf 18 -preset slow $out_concat.mp4
