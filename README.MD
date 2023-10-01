Backend server for EarthLinks

Uses: FastAPI, firebase, pyrebase

How to use:
1. Install pipenv : pip install pipenv
2. Type: pipenv shell
3. Install requirements from requiements.txt 
4. Run: python main.py
5. Swagger.UI will open up in browser, can test there. Linked to firebase project that stores all user authentication

How it works:
Signup: Create a new user in firebase with email/password authentication
Login: Take email and password to generate a access token
validate_token: Take a request containing the access token, and returns the UID of user (See test.py for example of testing this endpoint)