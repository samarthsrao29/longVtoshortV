import os
import math
import yt_dlp
from moviepy import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap

VIDEO_URL = ""
CLIP_DURATION = 180  # 1.5 minutes
OUTPUT_DIR = "divided_videos"

def main():
    # If ffmpeg is not available, we grab the best pre-merged mp4 to avoid needing it
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': 'original_video.%(ext)s',
        'noplaylist': True,
    }

    print("Downloading video...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(VIDEO_URL, download=True)
        video_title = info_dict.get('title', 'Video')
        original_filename = ydl.prepare_filename(info_dict)

    print(f"Video Title: {video_title}")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Loading video from {original_filename}...")
    video = VideoFileClip(original_filename)
    total_duration = video.duration
    num_parts = math.ceil(total_duration / CLIP_DURATION)

    def create_title_card(title_text, part_num, size):
        width, height = size
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try a standard macOS font
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(height*0.06))
            font_part = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(height*0.05))
        except:
            font_title = ImageFont.load_default()
            font_part = ImageFont.load_default()

        wrapped_title = textwrap.fill(title_text, width=40)
        text_part = f"Part {part_num}"
        
        try:
            draw.multiline_text((width/2, height/2 - 50), wrapped_title, font=font_title, fill=(255, 255, 255), anchor="md", align="center")
            draw.text((width/2, height/2 + 50), text_part, font=font_part, fill=(200, 200, 200), anchor="ma")
        except TypeError:
            # Fallback if anchor is not supported
            draw.text((50, height/2 - 100), wrapped_title, font=font_title, fill=(255, 255, 255))
            draw.text((50, height/2 + 50), text_part, font=font_part, fill=(200, 200, 200))
            
        temp_img_path = os.path.join(OUTPUT_DIR, f"temp_title_{part_num}.png")
        img.save(temp_img_path)
        return temp_img_path

    for i in range(num_parts):
        start_time = i * CLIP_DURATION
        end_time = min((i + 1) * CLIP_DURATION, total_duration)
        part_num = i + 1
        
        print(f"\n--- Processing Part {part_num}/{num_parts} ---")
        
        subclip = video.subclipped(start_time, end_time)
        title_img_path = create_title_card(video_title, part_num, subclip.size)
        title_clip = ImageClip(title_img_path).with_duration(3) # 3 seconds title card
        
        # Compose method to handle audio/video concatenation properly
        final_clip = concatenate_videoclips([title_clip, subclip], method="compose")
        
        output_filename = os.path.join(OUTPUT_DIR, f"Part_{part_num}.mp4")
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac", threads=4)
        
        os.remove(title_img_path)

    video.close()
    print("Done! All parts have been saved in the 'divided_videos' folder.")

if __name__ == "__main__":
    main()
