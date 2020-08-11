# TEQST Backend Server

## Setup
\
**Create a new virtual environment**:\
python3 -m venv TEQST_Backend/venv\
\
**Activate the virtual environment**:\
**Linux/MacOS**:\
source TEQST_Backend/venv/bin/activate\
**Windows**:\
TEQST_Backend/venv/Scripts/activate.bat\
\
**Install the dependencies**:\
pip3 install -r TEQST_Backend/requirements.txt\
\
**Prepare the database models**:\
python3 manage.py makemigrations usermgmt\
python3 manage.py makemigrations textmgmt\
python3 manage.py makemigrations recordingmgmt\
python3 manage.py migrate\
\
**create a superuser**\
python3 manage.py createsuperuser\
\
**create a group called "Publisher" with no permissions**\
\
**Run the server**:\
python3 manage.py runserver

## Testing
**Run all tests**:\
python3 manage.py test
