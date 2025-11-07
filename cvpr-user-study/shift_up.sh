#/bin/bash

# This script shifts the video up and stacks the top and bottom parts vertically.

mv A_synctalk_222200037_nersemble_460_2_200000.mp4 A_synctalk_222200037_nersemble_460_2_200000_orig.mp4
shift=76
ffmpeg -i A_synctalk_222200037_nersemble_460_2_200000_orig.mp4 -filter_complex \
"[0:v]crop=in_w:$shift:0:0[top]; \
 [0:v]crop=in_w:in_h-$shift:0:$shift[rest]; \
 [rest][top]vstack=inputs=2" \
-c:a copy A_synctalk_222200037_nersemble_460_2_200000.mp4

shift=90
mv A_synctalk_222200037_nersemble_304_2_200000.mp4 A_synctalk_222200037_nersemble_304_2_200000_orig.mp4
ffmpeg -i A_synctalk_222200037_nersemble_304_2_200000_orig.mp4 -filter_complex \
"[0:v]crop=in_w:$shift:0:0[top]; \
 [0:v]crop=in_w:in_h-$shift:0:$shift[rest]; \
 [rest][top]vstack=inputs=2" \
-c:a copy A_synctalk_222200037_nersemble_304_2_200000.mp4

shift=30
mv A_synctalk_222200037_nersemble_264_2_200000.mp4 A_synctalk_222200037_nersemble_264_2_200000_orig.mp4
ffmpeg -i A_synctalk_222200037_nersemble_264_2_200000_orig.mp4 -filter_complex \
"[0:v]crop=in_w:$shift:0:0[top]; \
 [0:v]crop=in_w:in_h-$shift:0:$shift[rest]; \
 [rest][top]vstack=inputs=2" \
-c:a copy A_synctalk_222200037_nersemble_264_2_200000.mp4

mv B_synctalk_222200037_nersemble_460_2_200000.mp4 B_synctalk_222200037_nersemble_460_2_200000_orig.mp4
shift=76
ffmpeg -i B_synctalk_222200037_nersemble_460_2_200000_orig.mp4 -filter_complex \
"[0:v]crop=in_w:$shift:0:0[top]; \
 [0:v]crop=in_w:in_h-$shift:0:$shift[rest]; \
 [rest][top]vstack=inputs=2" \
-c:a copy B_synctalk_222200037_nersemble_460_2_200000.mp4

shift=90
mv B_synctalk_222200037_nersemble_304_2_200000.mp4 B_synctalk_222200037_nersemble_304_2_200000_orig.mp4
ffmpeg -i B_synctalk_222200037_nersemble_304_2_200000_orig.mp4 -filter_complex \
"[0:v]crop=in_w:$shift:0:0[top]; \
 [0:v]crop=in_w:in_h-$shift:0:$shift[rest]; \
 [rest][top]vstack=inputs=2" \
-c:a copy B_synctalk_222200037_nersemble_304_2_200000.mp4

shift=30
mv B_synctalk_222200037_nersemble_264_2_200000.mp4 B_synctalk_222200037_nersemble_264_2_200000_orig.mp4
ffmpeg -i B_synctalk_222200037_nersemble_264_2_200000_orig.mp4 -filter_complex \
"[0:v]crop=in_w:$shift:0:0[top]; \
 [0:v]crop=in_w:in_h-$shift:0:$shift[rest]; \
 [rest][top]vstack=inputs=2" \
-c:a copy B_synctalk_222200037_nersemble_264_2_200000.mp4
