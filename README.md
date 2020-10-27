# TEQST Backend Server

## Setup
### Create a new virtual environment
python3 -m venv TEQST_Backend/venv
### Activate the virtual environment
#### Linux/MacOS
source TEQST_Backend/venv/bin/activate
#### Windows
TEQST_Backend/venv/Scripts/activate.bat
### Install the dependencies
pip3 install -r TEQST_Backend/requirements.txt
### Prepare the database models
python3 manage.py makemigrations usermgmt\
python3 manage.py makemigrations textmgmt\
python3 manage.py makemigrations recordingmgmt\
python3 manage.py migrate
### create a superuser
creating a superuser via the createsuperuser utility is currently broken due to the additional required attribute of a birthyear in the user class
you have to create a user via the shell like so:
python3 manage.py shell
from usermgmt.models import CustomUser
CustomUser.objects.create_superuser('username', password='password')
### create a group called "Publisher" with no permissions
### Run the server
python3 manage.py runserver
## Testing
### Run all tests
python3 manage.py test
## Python setup
if the python3 name doesnt work on your machine try python instead but make sure (with python --version) that this calls a 3.x python
