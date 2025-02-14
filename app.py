import os
import uuid
import logging
from flask import Flask, request, render_template, send_file, url_for, redirect, flash
from werkzeug.utils import secure_filename
from video_processing import process_videos

# Configure logging for debugging and error reporting.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

# Initialize Flask application.
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for flash messages.

# Define the folder for uploaded and processed files.
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions for video uploads.
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    """
    Render the index page with the video processing form.
    """
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """
    Handle the video processing request:
      - Validate and save uploaded video files.
      - Parse both basic and advanced processing parameters from the form.
      - Invoke the video processing pipeline.
      - Render the page with a preview and download option for the output video.
    """
    try:
        # Basic options
        remove_spspps = request.form.get('remove_spspps', 'yes')
        # I-frame removal mode: 'none', 'first', or 'all'
        removal_mode = request.form.get('remove_iframes', 'first')
        try:
            offset = float(request.form.get('offset', '0.0'))
        except ValueError:
            offset = 0.0

        # Advanced datamoshing parameters
        try:
            duplicate_pframes = int(request.form.get('duplicate_pframes', 1))
        except ValueError:
            duplicate_pframes = 1
        try:
            duplicate_probability = int(request.form.get('duplicate_probability', 100))
        except ValueError:
            duplicate_probability = 100
        try:
            reorder_intensity = int(request.form.get('reorder_intensity', 0))
        except ValueError:
            reorder_intensity = 0
        try:
            reorder_window_size = int(request.form.get('reorder_window_size', 10))
        except ValueError:
            reorder_window_size = 10
        try:
            corrupt_pframes_chance = int(request.form.get('corrupt_pframes', 0))
        except ValueError:
            corrupt_pframes_chance = 0
        try:
            corruption_intensity = int(request.form.get('corruption_intensity', 50))
        except ValueError:
            corruption_intensity = 50
        try:
            drop_frame_percentage = int(request.form.get('drop_frame_percentage', 0))
        except ValueError:
            drop_frame_percentage = 0

        # Ensure both video files are provided.
        if 'video1' not in request.files or 'video2' not in request.files:
            flash('Both video files are required.')
            return redirect(request.url)

        video1_file = request.files['video1']
        video2_file = request.files['video2']

        # Check that files have been selected.
        if video1_file.filename == '' or video2_file.filename == '':
            flash('No selected file for one or both videos.')
            return redirect(request.url)

        # Validate file extensions.
        if not (allowed_file(video1_file.filename) and allowed_file(video2_file.filename)):
            flash('One or both files have an invalid file type.')
            return redirect(request.url)

        # Create unique filenames using a UUID and sanitize them.
        uid = str(uuid.uuid4())
        video1_filename = secure_filename(f"video1_{uid}_" + video1_file.filename)
        video2_filename = secure_filename(f"video2_{uid}_" + video2_file.filename)
        video1_path = os.path.join(app.config['UPLOAD_FOLDER'], video1_filename)
        video2_path = os.path.join(app.config['UPLOAD_FOLDER'], video2_filename)
        
        # Save the uploaded files to disk.
        video1_file.save(video1_path)
        video2_file.save(video2_path)
        logging.info("Uploaded files saved successfully.")

        # Process the videos using the advanced pipeline.
        output_video_path = process_videos(
            video1_path, video2_path, uid, remove_spspps, removal_mode,
            offset, app.config['UPLOAD_FOLDER'],
            duplicate_pframes, duplicate_probability, reorder_intensity, reorder_window_size,
            corrupt_pframes_chance, corruption_intensity, drop_frame_percentage
        )

        # Generate the URL for previewing and downloading the output video.
        video_url = url_for('uploaded_file', filename=os.path.basename(output_video_path))
        return render_template('index.html', video_url=video_url)

    except Exception as e:
        # Log the error and notify the user with a flash message.
        logging.error("An error occurred during processing: %s", e, exc_info=True)
        flash("An error occurred during video processing. Please try again.")
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Serve the processed video file so users can preview or download it.
    """
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    # Run the Flask application in debug mode.
    app.run(debug=True)
