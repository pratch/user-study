base_path="test_videos"
video4=$base_path"/voo-218A"
ffmpeg -i $video4.mp4 -vf "pad=550:802:(550-512)/2:(802-512)/2:black" ${video4}_padded.mp4
