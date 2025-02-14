# H.264 Datamosh Web Tool

A web-based tool for performing H.264 datamoshing by processing and concatenating two video clips. This project uses Python, Flask, and ffmpeg to extract and manipulate raw video streams, providing a modern and user-friendly interface with advanced controls for creative effects.

## Features

- **Video Uploads:** Upload two video clips for processing.
- **Basic Datamoshing Options:** 
  - Remove SPS/PPS (NAL types 7 & 8) 
  - I-frame removal modes: remove the first I-frame, remove all I-frames, or keep all.
  - Time offset for Clip 2.
- **Advanced Datamoshing Effects:**
  - **P-frame Duplication:** Duplicate P-frames by a specified factor with a set probability.
  - **Localized Reordering:** Shuffle frames within a local window to create controlled glitch effects. Control the intensity and window size.
  - **P-frame Corruption:** Apply corruption to P-frames with adjustable probability and intensity.
  - **Frame Dropping:** Randomly drop frames based on a user-defined percentage.
- **Real-Time Preview:** Preview and download the processed video in the browser.
- **Responsive Design:** A modern, minimalistic UI built with Bootstrap 5.

## Installation

### Prerequisites

- Python 3.7 or later.
- [ffmpeg](https://ffmpeg.org/) installed and accessible in your system's PATH.

### Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your_username/h264-datamosh-web-tool.git
   cd h264-datamosh-web-tool
   ```
2. **Create a Virtual Environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. **Install the Required Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Application:**
   ```bash
   python app.py
   ```
5. **Access the Tool:**
   Open your web browser and navigate to `http://127.0.0.1:5000`.
   
## Project Structure
   ```graphql
   .
   ├── app.py                   # Main Flask application
   ├── video_processing.py      # Video processing logic and helper functions
   ├── requirements.txt         # Python dependencies
   ├── README.md                # Project documentation
   ├── .gitignore               # Git ignore file
   ├── uploads/                 # Directory for uploaded and processed videos
   ├── templates/
   │   └── index.html           # Jinja2 template for the web interface
   └── static/
       └── css/
           └── style.css        # Custom CSS for styling
   ```

## Usage

1. **Upload Videos:**
   - Use the form to upload two video clips. The first clip serves as the base, and the second clip will be processed and appended.

2. **Adjust Settings:**
   - **Basic Options:** Configure whether to remove SPS/PPS and choose the I-frame removal mode (`Remove first I-frame`, `Remove all I-frames`, or `Keep all I-frames`).
   - **Advanced Datamoshing Options:**
   - - **Duplicate P-frames:** Specify how many times each P-frame should be duplicated and set a probability for duplication.
   - - **Localized Reordering:** Set the intensity (chance to shuffle a local window) and window size for frame reordering.
   - - **P-frame Corruption:** Define the percentage chance to corrupt P-frames and the intensity of the corruption.
   - - **Frame Dropping:** Set the percentage chance to randomly drop any frame.
   - **Offset:** Specify the number of seconds to skip at the start of Clip 2.

3. **Process and Preview:**
   - Click "Process and Preview" to generate the datamoshed video.
   - The processed video will be displayed for preview, and you can download it if you like the result.
   
## Logging and Error Handling
- The application uses Python's `logging` module to record debug, info, and error messages.
- Errors during processing are handled gracefully with user-friendly notifications.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.