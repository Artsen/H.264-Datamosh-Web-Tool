import os
import subprocess
import logging
import random

def extract_raw_stream(input_path, output_path):
    """
    Extract a raw H.264 bitstream (Annex B format) from an input video file using ffmpeg.
    
    Parameters:
      input_path (str): Path to the source video file.
      output_path (str): Destination file path for the raw stream.
    """
    try:
        logging.debug("Extracting raw H.264 stream from %s to %s", input_path, output_path)
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-c:v', 'copy', '-bsf:v', 'h264_mp4toannexb', output_path
        ], check=True)
        logging.info("Extraction completed for %s", input_path)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to extract raw stream from %s: %s", input_path, e)
        raise

def corrupt_nal(nal, corruption_intensity):
    """
    Introduce artificial corruption to a NAL unit by modifying one random byte in its payload.
    
    Parameters:
      nal (bytes): The original NAL unit.
      corruption_intensity (int): A value from 0 to 100 indicating the intensity of corruption.
      
    Returns:
      bytes: The corrupted NAL unit.
    """
    ba = bytearray(nal)
    if len(ba) > 5:
        # Choose a random index beyond the header to corrupt.
        index_to_corrupt = random.randint(5, len(ba) - 1)
        # Determine the maximum change based on the corruption intensity.
        max_change = max(1, int(255 * corruption_intensity / 100))
        change = random.randint(1, max_change)
        ba[index_to_corrupt] = (ba[index_to_corrupt] + change) % 256
    return bytes(ba)

def process_video2_raw(input_path, output_path, remove_spspps='yes', removal_mode='first',
                       duplicate_pframes=1, duplicate_probability=100,
                       reorder_intensity=0, reorder_window_size=10,
                       corrupt_pframes_chance=0, corruption_intensity=50, drop_frame_percentage=0):
    """
    Process the raw H.264 stream of the second video with advanced datamoshing options.
    
    Parameters:
      input_path (str): Path to the raw video file to process.
      output_path (str): Destination file path for the processed stream.
      remove_spspps (str): 'yes' to remove SPS/PPS (NAL types 7 & 8).
      removal_mode (str): I-frame removal mode: 'none', 'first', or 'all'.
                          'first' removes the first I-frame (IDR, NAL type 5).
                          'all' removes all I-frames.
                          'none' keeps all I-frames.
      duplicate_pframes (int): Number of times to duplicate each P-frame.
      duplicate_probability (int): Percentage chance (0-100) to duplicate a P-frame.
      reorder_intensity (int): Percentage chance (0-100) that a local window will be shuffled.
      reorder_window_size (int): Number of frames in each window for localized reordering.
      corrupt_pframes_chance (int): Percentage chance (0-100) to corrupt a P-frame.
      corruption_intensity (int): Intensity (0-100) of the corruption applied.
      drop_frame_percentage (int): Percentage chance (0-100) to drop any frame.
    """
    try:
        logging.debug("Processing raw video stream %s with advanced datamoshing options", input_path)
        # Read the entire raw video file.
        with open(input_path, "rb") as f:
            data = f.read()

        # Define the start code used in H.264 streams.
        start_code = b'\x00\x00\x00\x01'
        nals = []
        offsets = []
        start = 0

        # Identify the start of each NAL unit.
        while True:
            idx = data.find(start_code, start)
            if idx == -1:
                break
            offsets.append(idx)
            start = idx + 4
        offsets.append(len(data))
        for i in range(len(offsets) - 1):
            nal = data[offsets[i]:offsets[i+1]]
            nals.append(nal)

        processed_nals = []
        removed_first_idr = False

        # Iterate through each NAL unit applying the chosen datamoshing effects.
        for nal in nals:
            if len(nal) < 5:
                continue  # Skip invalid NAL units.
            nal_type = nal[4] & 0x1F

            # Remove SPS (7) and PPS (8) if requested.
            if remove_spspps == 'yes' and nal_type in [7, 8]:
                continue

            # I-frame removal logic based on removal_mode.
            if removal_mode == 'first' and not removed_first_idr and nal_type == 5:
                removed_first_idr = True
                continue
            elif removal_mode == 'all' and nal_type == 5:
                continue

            # Randomly drop frames based on drop_frame_percentage.
            if drop_frame_percentage > 0:
                if random.uniform(0, 100) < drop_frame_percentage:
                    continue

            # Process P-frames (NAL type 1) with duplication and potential corruption.
            if nal_type == 1:
                if random.uniform(0, 100) < duplicate_probability:
                    # Duplicate the P-frame the specified number of times.
                    for _ in range(duplicate_pframes):
                        temp_nal = nal
                        if corrupt_pframes_chance > 0 and random.uniform(0, 100) < corrupt_pframes_chance:
                            temp_nal = corrupt_nal(nal, corruption_intensity)
                        processed_nals.append(temp_nal)
                else:
                    processed_nals.append(nal)
                continue  # Skip normal append since P-frame handled.

            # For all other frames, append as is.
            processed_nals.append(nal)

        # Apply localized reordering if requested.
        if reorder_intensity > 0 and reorder_window_size > 1:
            new_nals = []
            for i in range(0, len(processed_nals), reorder_window_size):
                window = processed_nals[i:i + reorder_window_size]
                # With a probability based on reorder_intensity, shuffle this window.
                if random.uniform(0, 100) < reorder_intensity:
                    random.shuffle(window)
                    logging.debug("Shuffled a window of %d frames", len(window))
                new_nals.extend(window)
            processed_nals = new_nals

        # Write the processed NAL units to the output file.
        with open(output_path, "wb") as f:
            for nal in processed_nals:
                f.write(nal)
        logging.info("Advanced processing of video2 raw stream completed. Output saved to %s", output_path)
    except Exception as e:
        logging.error("Error processing video2 raw stream: %s", e, exc_info=True)
        raise

def apply_offset(input_path, output_path, offset):
    """
    Apply a time offset to a video file using ffmpeg to skip a specified duration.
    
    Parameters:
      input_path (str): Path to the input file.
      output_path (str): Destination file path after applying the offset.
      offset (float): Time in seconds to skip from the beginning of the video.
    """
    try:
        logging.debug("Applying offset of %s seconds to %s", offset, input_path)
        subprocess.run([
            'ffmpeg', '-y', '-ss', str(offset), '-i', input_path,
            '-c', 'copy', output_path
        ], check=True)
        logging.info("Offset applied successfully. Output saved to %s", output_path)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to apply offset to %s: %s", input_path, e)
        raise

def concatenate_streams(video1_raw, video2_processed, output_path):
    """
    Concatenate two raw H.264 streams into one file.
    
    Parameters:
      video1_raw (str): Path to the first raw video stream.
      video2_processed (str): Path to the processed second video stream.
      output_path (str): Destination file path for the concatenated output.
    """
    try:
        logging.debug("Concatenating streams: %s and %s into %s", video1_raw, video2_processed, output_path)
        with open(output_path, "wb") as outfile:
            with open(video1_raw, "rb") as infile:
                outfile.write(infile.read())
            with open(video2_processed, "rb") as infile:
                outfile.write(infile.read())
        logging.info("Concatenation completed. Combined file saved to %s", output_path)
    except Exception as e:
        logging.error("Error during concatenation: %s", e, exc_info=True)
        raise

def remux_to_mp4(input_path, output_path):
    """
    Remux and re-encode a concatenated raw H.264 stream into an MP4 container using ffmpeg.
    This version re-encodes the video using libx264 with settings that preserve quality 
    while generating a smooth output. It also includes the '-movflags faststart' flag to
    ensure that the moov atom is placed at the beginning of the file for better streaming.
    Additionally, '-err_detect ignore_err' is used to skip over non-critical errors.
    
    Parameters:
      input_path (str): Path to the concatenated raw video file.
      output_path (str): Destination file path for the MP4 output.
    """
    try:
        logging.debug("Re-encoding raw stream %s to MP4 format at %s with faststart", input_path, output_path)
        subprocess.run([
            'ffmpeg', '-y', '-fflags', '+genpts', '-err_detect', 'ignore_err', '-i', input_path,
            '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', 
            '-movflags', 'faststart', output_path
        ], check=True)
        logging.info("Re-encoding and remuxing completed. Output MP4 saved to %s", output_path)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to re-encode to MP4: %s", e)
        raise

def process_videos(video1_path, video2_path, uid, remove_spspps, removal_mode,
                   offset, upload_folder, duplicate_pframes=1, duplicate_probability=100,
                   reorder_intensity=0, reorder_window_size=10,
                   corrupt_pframes_chance=0, corruption_intensity=50, drop_frame_percentage=0):
    """
    Execute the complete video processing pipeline:
      1. Extract raw H.264 streams from both input videos.
      2. Process the second video's raw stream with advanced datamoshing options.
      3. Apply an offset to the processed second video if required.
      4. Concatenate the raw streams.
      5. Remux the concatenated stream into an MP4 container.
    
    Parameters:
      video1_path (str): Path to the first video file.
      video2_path (str): Path to the second video file.
      uid (str): Unique identifier for this processing session.
      remove_spspps (str): Option to remove SPS/PPS.
      removal_mode (str): I-frame removal mode ('none', 'first', or 'all').
      offset (float): Time offset (in seconds) for the second video.
      upload_folder (str): Directory to save all intermediate and final files.
      duplicate_pframes (int): Number of times to duplicate each P-frame.
      duplicate_probability (int): Chance (0-100) to duplicate a P-frame.
      reorder_intensity (int): Chance (0-100) that a local window will be shuffled.
      reorder_window_size (int): Number of frames in each local reordering window.
      corrupt_pframes_chance (int): Chance (0-100) to corrupt a P-frame.
      corruption_intensity (int): Intensity (0-100) of the corruption applied.
      drop_frame_percentage (int): Chance (0-100) to drop a frame.
      
    Returns:
      str: Path to the final processed MP4 video.
    """
    try:
        # Define intermediate file paths.
        video1_raw = os.path.join(upload_folder, f"video1_{uid}.264")
        video2_raw = os.path.join(upload_folder, f"video2_{uid}.264")
        video2_processed = os.path.join(upload_folder, f"video2_processed_{uid}.264")
        video2_final = os.path.join(upload_folder, f"video2_final_{uid}.264")
        concatenated_raw = os.path.join(upload_folder, f"final_{uid}.264")
        final_output = os.path.join(upload_folder, f"output_{uid}.mp4")

        # Step 1: Extract raw H.264 streams from both videos.
        extract_raw_stream(video1_path, video1_raw)
        extract_raw_stream(video2_path, video2_raw)

        # Step 2: Process the raw stream of the second video with advanced effects.
        process_video2_raw(video2_raw, video2_processed, remove_spspps, removal_mode,
                           duplicate_pframes, duplicate_probability, reorder_intensity, reorder_window_size,
                           corrupt_pframes_chance, corruption_intensity, drop_frame_percentage)

        # Step 3: Apply offset if specified.
        if offset > 0:
            apply_offset(video2_processed, video2_final, offset)
        else:
            video2_final = video2_processed

        # Step 4: Concatenate the two raw video streams.
        concatenate_streams(video1_raw, video2_final, concatenated_raw)

        # Step 5: Remux the concatenated raw stream into an MP4 container.
        remux_to_mp4(concatenated_raw, final_output)

        logging.info("Video processing pipeline completed successfully.")
        return final_output

    except Exception as e:
        logging.error("Video processing pipeline failed: %s", e, exc_info=True)
        raise
