import cv2
import os
import shutil

def parse_time_format(time_str):
    """Convert time format (mm:ss or hh:mm:ss) to seconds."""
    time_parts = time_str.split(":")
    time_parts = [int(part) for part in time_parts]

    if len(time_parts) == 2:  # mm:ss format
        minutes, seconds = time_parts
        return minutes * 60 + seconds
    elif len(time_parts) == 3:  # hh:mm:ss format
        hours, minutes, seconds = time_parts
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError("Invalid time format. Use mm:ss or hh:mm:ss.")

def format_timestamp(seconds):
    """Convert seconds into hh:mm:ss format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02}-{minutes:02}-{secs:02}"  # Use '-' instead of ':' for filenames

def get_opposite_color(color):
    """Get the opposite (inverted) RGB color."""
    return tuple(255 - c for c in color)

def add_timestamp_to_frame(frame, timestamp, font_scale=1.0, font_color=(255, 255, 255), thickness=2):
    """Add a timestamp to the bottom-right corner of the video frame with a contrasting shadow."""
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Get the size of the text
    text_size, _ = cv2.getTextSize(timestamp.replace("-", ":"), font, font_scale, thickness)

    # Calculate the position (bottom-right corner)
    frame_height, frame_width, _ = frame.shape
    text_x = frame_width - text_size[0] - 10  # 10 px padding from the right
    text_y = frame_height - 10  # 10 px padding from the bottom

    # Calculate the opposite color for the shadow
    shadow_color = get_opposite_color(font_color)

    # Add shadow for visibility using the opposite color
    cv2.putText(frame, timestamp.replace("-", ":"), (text_x, text_y), font, font_scale, shadow_color, thickness+1, cv2.LINE_AA)

    # Add timestamp text in the specified font_color
    cv2.putText(frame, timestamp.replace("-", ":"), (text_x, text_y), font, font_scale, font_color, thickness, cv2.LINE_AA)

    return frame

def extract_frames(video_path, output_folder, interval, start_time=None, end_time=None):
    # If the output folder exists, delete it and create a new one
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)  # Delete the folder and its contents
    os.makedirs(output_folder)  # Create a fresh output folder

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Get the frames per second (fps) of the video
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps  # Calculate total video duration in seconds

    # Convert start and end times to seconds
    if start_time is not None:
        start_time_seconds = parse_time_format(start_time)
        start_frame = int(start_time_seconds * fps)
    else:
        start_frame = 0  # Default to the beginning of the video

    if end_time is not None:
        end_time_seconds = parse_time_format(end_time)
        end_frame = int(end_time_seconds * fps)
    else:
        end_frame = total_frames  # Default to the end of the video

    # Ensure the end frame does not exceed the total number of frames in the video
    end_frame = min(end_frame, total_frames)

    # Calculate how many frames to skip based on the interval
    frame_interval = int(fps * interval)

    # Start reading the video from the start_frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_count = start_frame
    saved_count = 0

    while frame_count < end_frame:
        ret, frame = cap.read()

        if not ret:
            break

        # Calculate the current time in seconds based on the frame count
        current_time_seconds = frame_count / fps
        timestamp = format_timestamp(current_time_seconds)

        # Add timestamp to the frame
        frame_with_timestamp = add_timestamp_to_frame(frame, timestamp)

        # Save the frame every `frame_interval` frames
        if frame_count % frame_interval == 0:
            # Save the frame using the timestamp in the filename
            frame_filename = os.path.join(output_folder, f"frame_{timestamp}.jpg")
            cv2.imwrite(frame_filename, frame_with_timestamp)
            saved_count += 1

        frame_count += 1

    # Release the video capture object
    cap.release()
    print(f"Extracted {saved_count} frames to '{output_folder}' with timestamps in filenames")

if __name__ == "__main__":
    video_path = "input/video.mp4"  # Change this to your video file path
    output_folder = "frames_output"
    interval = 15.0  # seconds
    start_time = "43:00"  # optional, use format mm:ss or hh:mm:ss
    end_time = "44:00"  # optional, use format mm:ss or hh:mm:ss

    extract_frames(video_path, output_folder, interval, start_time, end_time)
