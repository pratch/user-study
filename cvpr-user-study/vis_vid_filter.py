from flask import Flask, request, send_file, send_from_directory
import glob, os
import numpy as np
import json
import sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--path', required=True)
parser.add_argument('--port', default=5000, type=int, help='Port to run the server on (default: 5000)')
args = parser.parse_args()

def create_app():
    app = Flask(__name__)
    
    @app.route('/files/<path:path>')
    def servefile(path):
        #NOTE: Serve the file to html    
        return send_from_directory(os.getcwd(), path)
    
    @app.route('/')
    def root():
        # Query string
        idx_str = request.args.get('idx', None)
        selected_subject = request.args.get('subject', 'FIRST')  # Default to showing first subject

        # Get all subdirectories
        subdirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
        subdirs = sorted(subdirs)
        
        if not subdirs:
            return f"<h3>No subdirectories found in {args.path}</h3>"
        
        def parse_video_info(video_name):
            """Parse video filename to extract subject_id and sentence_type"""
            if video_name.startswith('nersemble_'):
                # Pattern: nersemble_{subject_id}_{checkpoint}.mp4
                parts = video_name.split('_')
                if len(parts) >= 3:
                    subject_id = parts[1]
                    return subject_id, 'A'  # Default to A for viewdep methods
            else:
                # Pattern: {method}_heygen_{sentence_type}_{subject_id}_{epoch}.mp4 or {method}_heygen_{sentence_type}_{subject_id}.mp4
                parts = video_name.split('_')
                if len(parts) >= 4:
                    sentence_type = parts[2]  # A or B
                    subject_id = parts[3].split('.')[0]  # Remove .mp4 and any epoch info
                    return subject_id, sentence_type
            return None, None

        # Extract all unique subject+sentence combinations from all subdirs
        subject_combinations = set()
        all_videos_by_subdir = {}
        
        for subdir in subdirs:
            subdir_path = os.path.join(args.path, subdir)
            videos = sorted(glob.glob(os.path.join(subdir_path, '*.mp4')))
            all_videos_by_subdir[subdir] = videos
            
            for video in videos:
                video_name = os.path.basename(video)
                subject_id, sentence_type = parse_video_info(video_name)
                if subject_id and sentence_type:
                    subject_combinations.add(f"{subject_id} {sentence_type}")
        
        subject_combinations = sorted(list(subject_combinations))
        
        # Calculate video width based on number of subdirs to fit standard screen
        num_subdirs = len(subdirs)
        video_width = max(200, min(400, 1200 // num_subdirs))
        
        out = f"""
        <style>
            body {{ margin: 20px; }}
            .controls {{ 
                margin-bottom: 20px; 
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }}
            .controls select {{
                padding: 8px 12px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                margin-left: 10px;
            }}
            .controls label {{
                font-weight: bold;
                font-size: 14px;
            }}
            .container {{ display: flex; flex-wrap: wrap; gap: 10px; }}
            .method-column {{ 
                flex: 1; 
                min-width: {video_width}px; 
                text-align: center; 
                border: 1px solid #ddd;
                padding: 10px;
                border-radius: 8px;
            }}
            .method-title {{ 
                font-weight: bold; 
                font-size: 16px; 
                margin-bottom: 10px;
                background-color: #f0f0f0;
                padding: 8px;
                border-radius: 4px;
            }}
            video {{ 
                width: 100%; 
                max-width: {video_width}px; 
                height: auto;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-bottom: 8px;
            }}
            .video-name {{
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }}
            .loading-indicator {{
                color: #666;
                font-style: italic;
                margin-top: 10px;
            }}
        </style>
        <script>
            let allVideosLoaded = false;
            let videosToLoad = 0;
            let videosLoaded = 0;

            function onVideoLoaded() {{
                videosLoaded++;
                updateLoadingStatus();
                if (videosLoaded === videosToLoad && !allVideosLoaded) {{
                    allVideosLoaded = true;
                    startAllVideos();
                }}
            }}

            function updateLoadingStatus() {{
                const indicator = document.getElementById('loading-indicator');
                if (indicator) {{
                    if (videosLoaded < videosToLoad) {{
                        indicator.textContent = `Loading videos... ({{videosLoaded}}/{{videosToLoad}})`;
                    }} else {{
                        indicator.textContent = 'All videos loaded! Playing in sync...';
                        setTimeout(() => {{
                            indicator.style.display = 'none';
                        }}, 2000);
                    }}
                }}
            }}

            function startAllVideos() {{
                const videos = document.querySelectorAll('video');
                videos.forEach(video => {{
                    video.currentTime = 0;
                    video.play().catch(e => console.log('Autoplay prevented:', e));
                }});
            }}

            function initializeVideos() {{
                const videos = document.querySelectorAll('video');
                videosToLoad = videos.length;
                
                if (videosToLoad === 0) {{
                    return;
                }}

                updateLoadingStatus();

                videos.forEach(video => {{
                    video.addEventListener('canplaythrough', onVideoLoaded);
                    video.addEventListener('error', () => {{
                        console.log('Video load error:', video.src);
                        onVideoLoaded(); // Count as loaded to not block others
                    }});
                    video.load(); // Force loading
                }});
            }}

            function onSubjectChange() {{
                const select = document.getElementById('subject-select');
                const currentUrl = new URL(window.location.href);
                currentUrl.searchParams.set('subject', select.value);
                window.location.href = currentUrl.toString();
            }}

            document.addEventListener('DOMContentLoaded', initializeVideos);
        </script>
        """
        out += f"<h2>Video Comparison: {os.path.basename(args.path)}</h2>"
        
        # Add dropdown controls
        out += "<div class='controls'>"
        out += "<label for='subject-select'>Show subject:</label>"
        out += f"<select id='subject-select' onchange='onSubjectChange()'>"
        out += f"<option value='FIRST'{'selected' if selected_subject == 'FIRST' else ''}>First subject only (default)</option>"
        out += f"<option value='ALL'{'selected' if selected_subject == 'ALL' else ''}>All subjects</option>"
        for subject_combo in subject_combinations:
            selected = 'selected' if selected_subject == subject_combo else ''
            out += f"<option value='{subject_combo}' {selected}>Subject {subject_combo}</option>"
        out += "</select>"
        out += "</div>"
        
        # Display info based on selection
        if selected_subject == 'FIRST':
            first_subject = subject_combinations[0] if subject_combinations else "none"
            out += f"<p>Showing first subject ({first_subject}) across {num_subdirs} methods</p>"
        elif selected_subject == 'ALL':
            out += f"<p>Showing all subjects across {num_subdirs} methods</p>"
        else:
            out += f"<p>Showing subject {selected_subject} across {num_subdirs} methods</p>"
            
        out += "<div id='loading-indicator' class='loading-indicator'>Preparing videos...</div>"
        out += "<div class='container'>"
        
        for subdir in subdirs:
            videos = all_videos_by_subdir[subdir]
            
            # Filter videos based on selected subject
            filtered_videos = []
            
            if selected_subject == 'ALL':
                filtered_videos = videos  # Show all videos
            elif selected_subject == 'FIRST':
                # Show only the first subject (alphabetically)
                if subject_combinations:
                    target_subject = subject_combinations[0]
                    target_subject_id, target_sentence_type = target_subject.split(' ')
                    for video in videos:
                        video_name = os.path.basename(video)
                        v_subject_id, v_sentence_type = parse_video_info(video_name)
                        if v_subject_id == target_subject_id and v_sentence_type == target_sentence_type:
                            filtered_videos.append(video)
            else:
                # Show videos matching the selected subject combination
                target_subject_id, target_sentence_type = selected_subject.split(' ')
                for video in videos:
                    video_name = os.path.basename(video)
                    v_subject_id, v_sentence_type = parse_video_info(video_name)
                    if v_subject_id == target_subject_id and v_sentence_type == target_sentence_type:
                        filtered_videos.append(video)
            
            # Show column for each method
            out += "<div class='method-column'>"
            out += f"<div class='method-title'>{subdir}</div>"
            
            if filtered_videos:
                for video in filtered_videos:
                    video_name = os.path.basename(video)
                    out += f"<div class='video-name'>{video_name}</div>"
                    out += f"""<video controls muted loop preload="auto">
                        <source src="/files/{video}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>"""
            else:
                out += "<p>No matching videos found</p>"
            
            out += "</div>"
        
        out += "</div>"
        return out
    return app
        
if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=args.port, debug=True, threaded=False)
