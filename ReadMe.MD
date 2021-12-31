# Installation

Requires Python 3.9+ and pip

### Install spaCy
More information on: https://spacy.io/usage

It is recommended to use a virtual environment
1. `python -m venv .env`
2. `source .env/bin/activate`

Install spaCy v3.1.3. We are using the large english model (`en_core_web_lg`)
4. `pip install -U pip setuptools wheel`
5. `pip install -U spacy==3.1.3`
6. `python -m spacy download en_core_web_lg`

### Install dependencies

1. `pip install pyinflect`
2. `python -m pip install coreferee`
3. `python -m coreferee install en`

# Run the application
There are three ways to run the application:

### 1. Running multiple files at once (Shell)
To process multiples files at once, simply move them to the `Texts` folder and run the `evaluation.sh` Shell script.
Due to the nature of Python and spaCy, we need to run the python files separately and cannot simply call the function multiple times.

The results will appear in the `ProcssedTexts` directory

### 2. Running a single file manually (Python)
To process a single file, simply run 

`python evaluation.py <Path-To-File>`

The path is relative to this repository

### 3. Running multiple files at once (Python)
To process multiple file, do the following:
1. Move all files to the `Texts` folder
2. Uncomment line 52 in `evaluation.py`
3. Comment lines 55-58 in `evaluation.py`
4. Run `python evaluation.py`