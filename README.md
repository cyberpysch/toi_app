# TOI App

## Project Setup

### 1. Create a Virtual Environment
To set up the project, create a virtual environment:
```bash
python -m venv venv
```

Activate the virtual environment:
- **Windows**:
  ```bash
  venv\Scripts\activate
  ```
- **Linux/Mac**:
  ```bash
  source venv/bin/activate
  ```

### 2. Install Dependencies
Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Directory Structure
```
TOI App
├── app
│   ├── __init__.py
│   ├── api.py
│   ├── routes.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   ├── js
│   │   │   └── main.js
│   └── templates
│       └── index.html
├── prompts
│   ├── facts_prompt.json
│   ├── mcq_prompt.json
│   └── summary_prompt.json
├── crud.py
├── database.py
├── main.py
├── run.py
├── models.py
├── requirements.txt
└── README.md
```

## Flows

### 1. Scraping Flow (`main.py`)
The `main.py` file is responsible for scraping data. To run the scraping flow:
```bash
python main.py
```
This script will fetch and process data as per the defined logic.

### 2. Live Server Flow (`run.py`)
The `run.py` file is used to start the live server. To run the server:
```bash
python run.py
```
This will start the Flask application, making it accessible on your local machine.

## Running the Project

### Step-by-Step Guide
1. **Activate the virtual environment**:
   ```bash
   venv\Scripts\activate
   ```
2. **Run the scraping flow**:
   ```bash
   python main.py
   ```
3. **Start the live server**:
   ```bash
   python run.py
   ```

Access the application in your browser at `http://127.0.0.1:5000/`.