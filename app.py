from flask import Flask, jsonify, send_from_directory
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import pandas as pd
from descriptive_statistics import analyze_file  

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required to use flash messages

# Set the path for the uploads folder
# Uploads folder is used to collect scraped data
# Uploads folder is used to receive cleaned data
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit

# Set the path for the json folder
JSON_FOLDER = 'json_objects'
JSON_EXTENSIONS = {'json'}
app.config['JSON_FOLDER'] = JSON_FOLDER
os.makedirs(JSON_FOLDER, exist_ok=True)


# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# NAVIGATION ROUTES
# go to home page
@app.route('/')
def home():
    breadcrumbs = [("Home", "/")]
    return render_template('index.html', breadcrumbs=breadcrumbs)

# New route for the Selector demo page - will be removed later
@app.route('/selector')
def selector():
    breadcrumbs = [("Home", "/"), ("Selector Demo", "/selector")]
    files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    return render_template('selector.html', breadcrumbs=breadcrumbs, files=files)

@app.route('/data-scraper')
def data_scraper():
    breadcrumbs = [("Home", "/"), ("Data Scraper", "/data-scraper")]
    return render_template('data_scraper.html', breadcrumbs=breadcrumbs)

@app.route('/data-cleaner')
def data_cleaner():
    breadcrumbs = [("Home", "/"), ("Data Cleaner", "/data-cleaner")]
    return render_template('data_cleaner.html', breadcrumbs=breadcrumbs)

# Function to convert statistical results to JSON format
def create_json_graph(file_path):
    try:
        stats = analyze_file(file_path)

        if stats is None:
            return {'error': 'Failed to generate statistics'}, None

        if 'error' in stats:
            return {'error': stats['error']}, None

        def convert(obj):
            if isinstance(obj, (int, float)):
                return obj
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert(value) for key, value in obj.items()}
            return str(obj)

        stats = convert(stats)

        # Create JSON file with statistics
        json_file_name = os.path.basename(file_path).replace('.', '_') + '.json'
        json_file_path = os.path.join(app.config['JSON_FOLDER'], json_file_name)


        with open(json_file_path, 'w') as json_file:
            json.dump(stats, json_file, indent=4)

        return stats, os.path.basename(json_file_path)


    except Exception as e:
        return {'error': str(e)}, None
    
# Function to check if file has allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# NETWORK STATISTICS NAVIGATION ROUTE
@app.route('/network-statistics')
def network_statistics():
    breadcrumbs = [("Home", "/"), ("Select Dataset for Network Statistics", "/network-statistics")]
    
    # Retrieve and Filter files
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files = [f for f in files if allowed_file(f)]  # Assuming you have 'allowed_file'

    print("Files in Uploads Folder:", files)  # Debugging line

    return render_template('network_statistics.html', breadcrumbs=breadcrumbs, files=files)


# ROUTE FOR FILTERING DATASETS BY SHEET
@app.route('/select-dataset')
def select_dataset():
    files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    return render_template('selector.html', files=files)

@app.route('/get-sheets', methods=['POST'])
def get_sheets():
    filename = request.form['filename']
    try:
        xls = pd.ExcelFile(os.path.join('uploads', filename))
        sheets = xls.sheet_names
        return jsonify({'sheets': sheets})
    except Exception as e:
        return jsonify({'error': str(e)})

# Route for uploading data files
@app.route('/data-upload', methods=['GET', 'POST'])
def data_upload():
    breadcrumbs = [("Home", "/"), ("Data Upload", "/data-upload")]

    if request.method == 'POST':
        file = request.files['dataFile']
        if file and allowed_file(file.filename):  # Make sure you have an 'allowed_file' function
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            flash('File uploaded successfully!', 'success')

            # Update files info immediately
            files = os.listdir(app.config['UPLOAD_FOLDER'])
            files_info = [{
                'name': file,
                'size': f"{os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file)).st_size / 1024:.2f} KB",
                'upload_time': datetime.fromtimestamp(os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file)).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            } for file in files]

            return redirect(url_for('data_upload'))  # Redirect to refresh the page
        else:
            flash('Invalid file type. Please upload .csv, .xlsx, or .xls files only.', 'danger')

    # Retrieve file information for displaying existing uploads
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files_info = [{
        'name': file,
        'size': f"{os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file)).st_size / 1024:.2f} KB",
        'upload_time': datetime.fromtimestamp(os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file)).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    } for file in files]

    return render_template('data_upload.html', breadcrumbs=breadcrumbs, files=files_info)



@app.route('/datasets')
def datasets():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        stats = os.stat(filepath)
        files.append({
            'name': filename,
            'size': f"{stats.st_size / 1024:.2f} KB",
            'upload_time': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    return render_template('datasets.html', files=files)

@app.route('/explore-data')
def explore_data():
    breadcrumbs = [("Home", "/"), ("Choose Dataset to Explore", "/explore-data")]
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    if not files:
        flash("No uploaded files found. Please upload a file first.", 'danger')
        return render_template('explore_data.html', files=files, breadcrumbs=breadcrumbs, error_message="No uploaded files found.")
    return render_template('explore_data.html', files=files, breadcrumbs=breadcrumbs)

# Route for analyzing data
@app.route('/analyze-data', methods=['POST'])
def analyze_data():
    selected_file = request.form.get('selectedFile')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)
    if not os.path.exists(file_path):
        flash("File does not exist.", 'danger')
        return redirect(url_for('explore_data'))

    breadcrumbs = [("Home", "/"), ("Choose Dataset to Explore", "/explore-data"), ("Explore Data", "/analyze-data")]

    try:
        # Check the file extension and read accordingly
        if selected_file.endswith(('.xlsx', '.xls')):
            # Read all sheets; each sheet's DataFrame is stored in a dictionary
            xls = pd.ExcelFile(file_path)
            sheets = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
        elif selected_file.endswith('.csv'):
            df = pd.read_csv(file_path)
            sheets = {'CSV': df}
        else:
            flash("Unsupported file format.", 'danger')
            return redirect(url_for('explore_data'))

        # Convert each DataFrame to HTML table
        tables_html = {sheet_name: df.to_html(classes='table table-striped', index=False) for sheet_name, df in sheets.items()}

        # Call create_json_graph to print JSON data to console
        for sheet_name, df in sheets.items():
            json_data = create_json_graph(file_path)  # Assuming you want to print JSON for each sheet
            print(f"JSON data for {sheet_name}:")
            print(json_data)

    except Exception as e:
        flash(f"Failed to read the file: {str(e)}", 'danger')
        return redirect(url_for('explore_data'))

    return render_template('analysis_results.html', tables_html=tables_html, filename=selected_file, sheet_names=list(tables_html.keys()), json_data=json_data, breadcrumbs=breadcrumbs)

# Route for listing JSON files
@app.route('/list_files', methods=['GET'])
def list_files():
    files = [f for f in os.listdir(app.config['JSON_FOLDER']) if f.endswith('.json')]
    return jsonify(files)

# Route for getting JSON data
@app.route('/get_json_data/<filename>', methods=['GET'])
def get_json_data(filename):
    json_file_path = os.path.join(app.config['JSON_FOLDER'], filename)
    
    if not os.path.exists(json_file_path):
        return jsonify({'error': 'File not found'}), 404
    
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        
    return jsonify(data)

# Route for descriptive statistics
@app.route('/descriptive-statistics')
def descriptive_statistics():
    breadcrumbs = [("Home", "/"), ("Descriptive Statistics", "/descriptive-statistics")]
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    stats = {}
    json_files = {}
    
    for file in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
        stats[file], json_files[file] = create_json_graph(file_path)

        # Call create_json_graph to print JSON data to console
        print(f"JSON data for {file}:")
        print(stats[file])
    
    return render_template('descriptive_statistics.html', files=files, stats=stats, json_files=json_files, breadcrumbs=breadcrumbs)

@app.route('/descriptive-statistics-viewer')
def descriptive_statistics_viewer():
    breadcrumbs = [("Home", "/"), ("Descriptive Statistics Viewer", "/descriptive-statistics-viewer")]
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.xlsx', '.xls', '.csv'))]  # Filter to include only relevant file types
    return render_template('descriptive_statistics_viewer.html', files=files, breadcrumbs=breadcrumbs)

@app.route('/analyze/<filename>')
def analyze(filename):
    breadcrumbs = [("Home", "/"), ("Descriptive Statistics", "/descriptive-statistics"), ("View Statistics", "/")]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash("File does not exist.", 'danger')
        return redirect(url_for('descriptive_statistics'))
    results = analyze_file(file_path)
    return render_template('view_statistics.html', filename=filename, results=results, breadcrumbs=breadcrumbs)

@app.route('/network-visualiser')
def network_visualiser():
    breadcrumbs = [("Home", "/"), ("Network Visualiser", "/network-visualiser")]
    return render_template('network_visualiser.html', breadcrumbs=breadcrumbs)

@app.route('/report-generator')
def report_generator():
    breadcrumbs = [("Home", "/"), ("Report Generator", "/report-generator")]
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        stats = os.stat(filepath)
        files.append({
            'name': filename,
        })
    return render_template('report_generator.html', breadcrumbs=breadcrumbs)

@app.route('/login')
def user_profile():
    breadcrumbs = [("Home", "/"), ("Login", "/login")]
    return render_template('login.html', breadcrumbs=breadcrumbs)

@app.route('/settings')
def settings():
    breadcrumbs = [("Home", "/"), ("Settings", "/settings")]
    return render_template('settings.html', breadcrumbs=breadcrumbs)

@app.route('/support')
def support():
    breadcrumbs = [("Home", "/"), ("Support", "/support")]
    return render_template('support.html', breadcrumbs=breadcrumbs)

@app.route('/feedback')
def feedback():
    breadcrumbs = [("Home", "/"), ("Feedback", "/feedback")]
    return render_template('feedback.html', breadcrumbs=breadcrumbs)

if __name__ == '__main__':
    app.run(debug=True)
