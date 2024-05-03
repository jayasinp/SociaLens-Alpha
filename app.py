from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask import session
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
import pandas as pd
from descriptive_statistics import analyze_file
from calculate_network_statistics import calculate_network_statistics
from ergm import process_file
from chatbot import talktogpt



# FLASK APP MANDATORY CODE
app = Flask(__name__, static_folder='templates/static')
app.secret_key = 'supersecretkey'  # Required to use flash messages

# FILE PATHS
# Set the path for the uploads folder
UPLOAD_FOLDER = 'uploads'
# define the allowed file types
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# define the max file size allowed
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set the path for the json folder
JSON_FOLDER = 'json_objects'
JSON_EXTENSIONS = {'json'}
app.config['JSON_FOLDER'] = JSON_FOLDER
# Ensure the JSON directory exists
os.makedirs(JSON_FOLDER, exist_ok=True)

# Set the path for the raw_data_objects folder
RAW_DATA_FOLDER = 'raw_data_objects'
app.config['RAW_DATA_FOLDER'] = RAW_DATA_FOLDER
# Ensure the raw_data_objects directory exists
os.makedirs(RAW_DATA_FOLDER, exist_ok=True)

# Set the path for the prompt_files folder
PROMPT_FILES_FOLDER = 'descriptive'
app.config['PROMPT_FILES_FOLDER'] = 'descriptive'  # Path for the output text files
os.makedirs(app.config['PROMPT_FILES_FOLDER'], exist_ok=True)

# Set the path for the network_prompt_files folder where network statistics are saved for gpt3.5
NETWORK_PROMPT_FILES_FOLDER = 'network_prompt_files'
app.config['NETWORK_PROMPT_FILES_FOLDER'] = 'network_prompt_files'  # Path for the output text files
os.makedirs(app.config['NETWORK_PROMPT_FILES_FOLDER'], exist_ok=True)

# INDEX ROUTE
# go to home page
@app.route('/')
def home():
    breadcrumbs = [("Home", "/")]
    return render_template('index.html', breadcrumbs=breadcrumbs)

# SELECTOR ROUTE
# New route for the Selector demo page - will be removed later
@app.route('/selector')
def selector():
    breadcrumbs = [("Home", "/"), ("Selector Demo", "/selector")]
    files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    return render_template('selector.html', breadcrumbs=breadcrumbs, files=files)

# DATA SCRAPER ROUTE
@app.route('/data-scraper', methods=['GET', 'POST'])
def data_scraper():
    if request.method == 'POST':
        url = request.form['url']
        return redirect(url_for('results', url=url))   
    breadcrumbs = [("Home", "/"), ("Data Scraper", "/data-scraper")]
    return render_template('data_scraper.html', breadcrumbs=breadcrumbs)

# DATA SCRAPER VISUALISATION ROUTE
@app.route('/results')
def results():
    url = request.args.get('url', '')
    return render_template('data_scraper_vis.html', url=url)

# DATA CLEANER ROUTE
@app.route('/data-cleaner')
def data_cleaner():
    breadcrumbs = [("Home", "/"), ("Data Cleaner", "/data-cleaner")]
    return render_template('data_cleaner.html', breadcrumbs=breadcrumbs)

# DATA SCRAPER LOGIC
@app.route('/network.json')
def network_json():
    url = request.args.get('url', '')
    links, graph_json = scrape_wikipedia(url)
    save_data(url, graph_json)  # Save the scraped data to a file
    return jsonify(graph_json)

def scrape_wikipedia(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/wiki/') and not ':' in href:
                full_link = 'https://en.wikipedia.org' + href
                links.append(full_link)
        return links, create_network_json(url, links)
    except requests.RequestException:
        return [], {}

def create_network_json(url, links):
    nodes = [{'data': {'id': url, 'label': url.split('/')[-1]}}]
    nodes.extend({'data': {'id': link, 'label': link.split('/')[-1]}} for link in links)
    edges = [{'data': {'source': url, 'target': link}} for link in links]
    return {'nodes': nodes, 'edges': edges}

def save_data(url, data):
    directory = 'scraped_data'
    if not os.path.exists(directory):
        os.makedirs(directory)  # Create directory if it does not exist

    # Create a valid filename from the URL
    filename = url.replace('https://', '').replace('http://', '').replace('/', '_') + '.json'
    file_path = os.path.join(directory, filename)

    # Save the data to a JSON file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# DATA UPLOAD ROUTE
# BIG CHANGES HERE -> Automatically creates separate excel, csv and JSON files after file upload from raw data
# Route for uploading data files
@app.route('/data-upload', methods=['GET', 'POST'])
def data_upload():
    # Define navigation breadcrumbs for the user interface
    breadcrumbs = [("Home", "/"), ("Data Upload", "/data-upload")]

    # Handle POST requests, which are sent when a user uploads a file
    if request.method == 'POST':
        # Retrieve the file from the form input named 'dataFile'
        file = request.files['dataFile']
        # Validate the file using the allowed_file function to check its extension
        if file and allowed_file(file.filename):
            # Secure the filename to avoid file system injection attacks
            filename = secure_filename(file.filename)
            # Construct the file path where the file will be saved
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Save the file to the specified path
            file.save(file_path)
            # Notify the user of successful upload
            flash('File uploaded successfully!', 'success')

            # Additional processing for Excel files
            if filename.endswith(('.xlsx', '.xls')):
                # Process the Excel file to extract each sheet and save in different formats
                process_excel(file_path, filename)

            # Update file list and details immediately after upload
            files = os.listdir(app.config['UPLOAD_FOLDER'])
            files_info = [{
                'name': file_name,
                'size': f"{os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file_name)).st_size / 1024:.2f} KB",
                'upload_time': datetime.fromtimestamp(os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file_name)).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            } for file_name in files]

            # Redirect to the upload page to show the update and clean form
            return redirect(url_for('data_upload'))
        else:
            # Notify the user if the uploaded file type is not allowed
            flash('Invalid file type. Please upload .csv, .xlsx, or .xls files only.', 'danger')

    # For GET requests or after file upload, list all files in the upload directory
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files_info = format_files_info(files)
    # Render the upload page with breadcrumbs and file information
    return render_template('data_upload.html', breadcrumbs=breadcrumbs, files=files_info)

# PART OF DATA UPLOAD ROUTE -> Opens excel, then creates separate file types from individual sheets.
def process_excel(file_path, original_filename):
    # Open the Excel file for reading
    xls = pd.ExcelFile(file_path)
    # Strip the extension from the filename to use as a base for new files
    base_filename = original_filename.rsplit('.', 1)[0]

    # Create a directory for this specific file's processed outputs
    data_directory = os.path.join(app.config['RAW_DATA_FOLDER'], base_filename)
    os.makedirs(data_directory, exist_ok=True)

    # Process each sheet in the Excel file and save them in the newly created directory
    for sheet_name in xls.sheet_names:
        # Read the sheet into a DataFrame
        df = pd.read_excel(xls, sheet_name)
        # Create a filename for each format based on the original filename and sheet name
        sheet_base_filename = f"{base_filename}_{sheet_name}"
        
        # Save the DataFrame to an Excel file
        df.to_excel(os.path.join(data_directory, f"{sheet_base_filename}.xlsx"), index=False)  # Corrected path
        
        # Save the DataFrame to a CSV file
        df.to_csv(os.path.join(data_directory, f"{sheet_base_filename}.csv"), index=False)  # Corrected path
        
        # Convert the DataFrame to JSON and save to a file, using a traditional array format
        df.to_json(os.path.join(data_directory, f"{sheet_base_filename}.json"), orient='records')  # Corrected path


def format_files_info(files):
    # Generate file information for the user interface
    return [{
        'name': file,
        'size': f"{os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file)).st_size / 1024:.2f} KB",
        'upload_time': datetime.fromtimestamp(os.stat(os.path.join(app.config['UPLOAD_FOLDER'], file)).st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    } for file in files]


# DATASETS ROUTE 
# ! DEPRECATED !
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

# EXPLORE DATA ROUTE
# Nav route with some error or success messages
@app.route('/explore-data') 
def explore_data():

    # Create breadcrumbs for navigation
    breadcrumbs = [("Home", "/"), ("Choose Dataset to Explore", "/explore-data")]

    # Retrieve uploaded files, applying file extension filtering
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]

    # Handle the case where no files are found
    if not files:
        flash("No uploaded files found. Please upload a file first.", 'danger')
        return render_template('explore_data.html', files=files, breadcrumbs=breadcrumbs, error_message="No uploaded files found.")

    # If files exist, render the template with the list of files
    return render_template('explore_data.html', files=files, breadcrumbs=breadcrumbs) 

# EXPLORE DATA RESULTS ROUTE
# Route for viewing all sheets and their rows and columns in the browser
@app.route('/analyze-data', methods=['POST'])
def analyze_data():

    # Get the selected filename from the form submission
    selected_file = request.form.get('selectedFile')

    # Construct the full filepath by joining the uploads folder path and filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)

    # Check if the file exists. If not, display an error and redirect.
    if not os.path.exists(file_path):
        flash("File does not exist.", 'danger')
        return redirect(url_for('explore_data'))

    # Create a breadcrumbs list for navigation
    breadcrumbs = [("Home", "/"), ("Choose Dataset to Explore", "/explore-data"), ("Explore Data", "/analyze-data")]

    # Error handling block using a 'try...except'
    try:
        # Check file extension and read data accordingly
        if selected_file.endswith(('.xlsx', '.xls')):  
            # Read Excel file, storing each sheet in a dictionary
            xls = pd.ExcelFile(file_path)
            sheets = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
        elif selected_file.endswith('.csv'):
            # Read CSV file into a DataFrame  
            df = pd.read_csv(file_path)
            sheets = {'CSV': df}  # Store DataFrame in a dictionary  
        else:
            # Handle unsupported file formats
            flash("Unsupported file format.", 'danger')
            return redirect(url_for('explore_data'))

        # Convert DataFrames in the dictionary to HTML tables 
        tables_html = {sheet_name: df.to_html(classes='table table-striped', index=False) for sheet_name, df in sheets.items()}

        # Call a function to create JSON data (assuming it exists)
        for sheet_name, df in sheets.items():
            json_data = create_json_graph(file_path) 
            print(f"JSON data for {sheet_name}:")
            print(json_data)

    # Catch any potential exceptions during file reading
    except Exception as e:
        flash(f"Failed to read the file: {str(e)}", 'danger')
        return redirect(url_for('explore_data'))

    # Render the template and pass necessary data
    return render_template('analysis_results.html', tables_html=tables_html, filename=selected_file, sheet_names=list(tables_html.keys()), json_data=json_data, breadcrumbs=breadcrumbs) 

# NETWORK STATISTICS NAVIGATION ROUTE
@app.route('/network-statistics', methods=['GET', 'POST'])
def network_statistics():
    if request.method == 'POST':
        selected_folder = request.form.get('selectedFolder')
        selected_file = request.form.get('selectedFile')
        file_path = os.path.join(app.config['RAW_DATA_FOLDER'], selected_folder, selected_file)
        
        if not os.path.exists(file_path):
            flash("Selected file does not exist.", 'danger')
            return redirect(url_for('network_statistics'))

        if not selected_folder or not selected_file:
            flash("Please select both a folder and a file.", 'warning')
            return redirect(url_for('network_statistics'))

        file_path = os.path.join(app.config['RAW_DATA_FOLDER'], selected_folder, selected_file)
        if not os.path.exists(file_path):
            flash("Selected file does not exist.", 'danger')
            return redirect(url_for('network_statistics'))

        try:
            network_stats = calculate_network_statistics(file_path)
            return render_template('network_statistics_results.html', network_stats=network_stats, filename=selected_file)
        except Exception as e:
            flash(f"Failed to calculate network statistics: {str(e)}", 'danger')
            return redirect(url_for('network_statistics'))

    else:  # GET Request
        # This might be redundant now since we are using dynamic JavaScript loading
        return render_template('network_statistics.html')
    
# ERGM ROUTE
@app.route('/ergm', methods=['GET', 'POST'])
def ergm():
    if request.method == 'POST':
        selected_folder = request.form.get('selectedFolder')
        selected_file = request.form.get('selectedFile')
        if not selected_folder or not selected_file:
            flash("Please select both a folder and a file.", 'warning')
            return redirect(url_for('ergm'))
        
        file_path = os.path.join(app.config['RAW_DATA_FOLDER'], selected_folder, selected_file)
        if not os.path.exists(file_path):
            flash(f"Selected file {file_path} does not exist.", 'danger')
            return redirect(url_for('ergm'))

        try:
            ergm_results = process_file(file_path)
            return render_template('ergm_results.html', ergm_results=ergm_results, filename=selected_file)
        except Exception as e:
            flash(f"Failed to calculate ERGM: {str(e)}", 'danger')
            return redirect(url_for('ergm'))

    else:
        folders = [f for f in os.listdir(app.config['RAW_DATA_FOLDER']) if os.path.isdir(os.path.join(app.config['RAW_DATA_FOLDER'], f))]
        return render_template('ergm.html', folders=folders)

# Helper to populate files based on selected folder
@app.route('/api/files/<folder>')
def files_for_folder(folder):
    directory = os.path.join(app.config['RAW_DATA_FOLDER'], folder)
    try:
        files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 404

#
#App route for selecting the dataset for the chatbot
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    # Load available files for the selection dropdown
    files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    return render_template('chatbot.html', files=files)


#actual interface
@app.route('/chat-interface', methods=['GET', 'POST'])
def chat_interface():
    # Accessing the selected file and sheet from the URL query parameters
    file = request.args.get('file')
    file = file.replace('.xlsx', '')
    sheet = request.args.get('sheet')
    file_path = request.args.get('filePath')  # filepath variable assignment
    selector = file + "_" + sheet + '.txt'
    
        

    # Initialize file_contents variable outside the conditional blocks
    file_contents = ""
    stored_message=""
    response =""
    if not file or not sheet:
        # Redirect back to selection if no file or sheet is provided
        return redirect(url_for('chatbot'))

    # Construct the full path to the file
    full_file_path = os.path.join(file_path, file, selector)
    if os.path.exists(full_file_path):
        # Read the specified file
        try:
            with open(full_file_path, 'r') as file:  # Corrected to use full_file_path
                file_contents = file.read()
                
        except Exception as e:
            file_contents = f"Failed to read the file: {str(e)}"
    else:
        file_contents = "File does not exist."
    # save file contents to session
    session['file_contents']=file_contents
    return render_template('chat-interface.html', filePath=file_path, selector=selector, file_contents=file_contents, stored_message=stored_message, response=response)

@app.route('/send-message', methods=['POST'])
def send_message():
    # Extract the message from the form data
    user_message = request.form.get('message')
    #retrieve file contents froms ession
    file_contents = session.get('file_contents')
    prompt = "i will provide some statistical summaries and a question, please respond in a simple yet descriptive manner " + file_contents+" " +user_message
    response=talktogpt(prompt)
    return response

@app.route('/api/get-files')
def get_files():
    folder = request.args.get('folder')
    if folder:
        directory = os.path.join(app.config['RAW_DATA_FOLDER'], folder)
        try:
            files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
            return jsonify({'files': files})
        except FileNotFoundError:
            return jsonify({'error': 'Folder not found'}), 404
    else:
        # Fetch all folders in the base directory if no specific folder is requested
        try:
            folders = [f for f in os.listdir(app.config['RAW_DATA_FOLDER']) if os.path.isdir(os.path.join(app.config['RAW_DATA_FOLDER'], f))]
            return jsonify({'folders': folders})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No folder specified'}), 400



# DESCRIPTIVE STATISTICS ROUTE
# Prepares the page to show data
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

# Route to present descriptive statistics to user
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

# NETWORK VISUALISER ROUTES
# creates a blank page work-in-progress
@app.route('/network-visualiser')
def network_visualiser():
    breadcrumbs = [("Home", "/"), ("Network Visualiser", "/network-visualiser")]
    return render_template('network_visualiser.html', breadcrumbs=breadcrumbs)

# REPORT GENERATOR ROUTE
# Creates a blank UI work-in-progress
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

# ANCILLIARY ROUTES LOW PRIORITY
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

# SOCIALENS UTILITIES
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

# ROUTE FOR FILTERING DATASETS BY SHEET
# Used by selector demo
@app.route('/select-dataset')
def select_dataset():
    files = [f for f in os.listdir('uploads') if f.endswith('.xlsx')]
    return render_template('selector.html', files=files)

# ROUTE TO GET SHEET NAMES FROM EXCEL FILE 
# ! Could be broken !
@app.route('/get-sheets', methods=['POST'])
def get_sheets():
    filename = request.form['filename']
    try:
        xls = pd.ExcelFile(os.path.join('uploads', filename))
        sheets = xls.sheet_names
        return jsonify({'sheets': sheets})
    except Exception as e:
        return jsonify({'error': str(e)})
    
# ROUTES FOR JSON UTILITIES
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


if __name__ == '__main__':
    app.run(debug=True)
