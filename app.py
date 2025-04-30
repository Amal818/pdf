from flask import Flask, request, jsonify, render_template
import os
import zipfile
import pdfplumber

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variable to store extracted data
extracted_data = []

def extract_data_from_pdf(pdf_path, filename):
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            print(f"Extracted text from {pdf_path}: {text}")  # Debugging line
            lines = text.split("\n")
            for line in lines:
                if line.strip():
                    parts = line.split()
                    matricule = parts[0]
                    name = " ".join(parts[1:-2])
                    days = parts[-2]
                    salary = parts[-1]
                    # Add file name to the data
                    data.append({'matricule': matricule, 'name': name, 'days': days, 'salary': salary, 'file': filename})
    return data

def process_zip(file_path):
    global extracted_data  # Use global variable
    data = []
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(UPLOAD_FOLDER)
        for filename in zip_ref.namelist():
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(UPLOAD_FOLDER, filename)
                # Pass the filename to extract data from pdf
                data.extend(extract_data_from_pdf(pdf_path, filename))
    extracted_data = data  # Store data in global variable
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    data = process_zip(file_path)
    print(f"Extracted Data: {data}")  # Debugging line
    os.remove(file_path)
    return jsonify({'message': 'File uploaded successfully', 'data': data})

@app.route('/search', methods=['GET'])
def search_name():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'Name parameter is required'}), 400
    
    result = [entry for entry in extracted_data if name.lower() in entry['name'].lower()]
    print(f"Search Results for '{name}':", result)  # Debugging line
    return jsonify({'results': result})

if __name__ == '__main__':
    app.run(debug=True)
