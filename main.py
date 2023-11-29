import uvicorn
import pyrebase
from fastapi import FastAPI
from models import *
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
import firebase_admin
from firebase_admin import credentials,auth
import geohash2
from geopy.distance import distance
import numpy as np
from geopy.distance import great_circle
import ast


app = FastAPI(
    description="Test app",
    title="EarthLink",
    docs_url="/"
)

@app.get("/")
def home():
    return {"Hello": "World"}


if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

firebaseConfig = {
  "apiKey": "AIzaSyBFV0RkPrt5jJmIhvVdRl_oCdVWXLtlGsg",
  "authDomain": "earthlinks-7c491.firebaseapp.com",
  "projectId": "earthlinks-7c491",
  "storageBucket": "earthlinks-7c491.appspot.com",
  "messagingSenderId": "699164993677",
  "appId": "1:699164993677:web:2b01a53426ec0386c09ac4",
  "measurementId": "G-V17GM0DBC0",
  "databaseURL": "https://earthlinks-7c491-default-rtdb.firebaseio.com/"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()



# post method for creating new account
@app.post('/signup')
async def create_account(user_data:SignUpSchema):
    email = user_data.email
    password = user_data.password

    try:
        user = auth.create_user(
            email = email,
            password = password
        )


        data = {"UID" : user.uid, "username": user.uid, "bio": "", "profile_picture": "gs://earthlinks-7c491.appspot.com/person-24px.xml"}
        db_result = db.child("users").push(data)


        return JSONResponse(content={"message": f"User account created succesfully for user {user.uid}"},
                            status_code= 201)

    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=400,
            detail=f"Account already created for the email {email}"
        )
    except ValueError as e:
        raise(
            HTTPException(
                status_code = 422,
                detail=str(e)
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



#post for creating access token for user login
@app.post('/login')
async def create_access_token(user_data:LoginSchema):
    email = user_data.email
    password = user_data.password

    try:
        user = firebase.auth().sign_in_with_email_and_password(
            email=email,
            password = password
        )

        token = user['idToken']

        return JSONResponse(
            content={
                "token":token
            }, status_code=200
        )
    except:
        raise HTTPException(
            status_code=400,
            detail="Invalid email/password"
        )

#post for validdting the token before logging in
#request: the 
@app.post('/ping')
async def validate_token(request:Request):
    headers = request.headers
    jwt = headers.get('authorization')

    user = auth.verify_id_token(jwt)

    return JSONResponse(content = {"userID": user["user_id"]}
                        ,status_code = 200)



@app.post('/message')
async def post_message(message_data:MessageSchema):

    data = message_data.dict()
    data['timestamp'] = data['timestamp'].isoformat()  # Convert datetime to string for Firebase
    geohash = geohash2.encode(message_data.latitude, message_data.longitude, precision=10)
    data['geohash'] = geohash

    try:
        result = db.child("messages").push(data)


        return JSONResponse(content ={"message": "Message posted successfully", 
                                      "message_id": result["name"]},
                            status_code = 200)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

#request to get all users
@app.get("/getUsers")
async def get_users():
    try:
        data = db.child("users").get().val()
        return JSONResponse(content = data,
                            status_code = 200)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )



#retrieve user information by their UID
@app.get("/getUser/{user_uid}")
async def get_user_by_uid(user_uid: str):
    try:
        user = db.child("users").order_by_child("UID").equal_to(user_uid).get()
        return JSONResponse(content=user.pyres[0].item[1], status_code = 200)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )



#testing getting data from database
@app.get("/getAllMessages")
async def get_all_messages():
    try:

        data = db.child("messages").get().val()
        return JSONResponse(content=data, status_code = 200)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"error occured while retrieving messages: {e}"
        )


@app.get("/getMessagesFromUser/{userID}")
async def get_messages_from_user(userID: str):
    try:
        messages = db.child("messages").order_by_child("user_uid").equal_to(userID).get().val()
        return JSONResponse(content = messages, status_code = 200)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    

#get messags within 10 meter radius
@app.get("/getMessagesByRadius/{latitude}/{longitude}")
async def get_messages_by_radius(latitude: float, longitude: float):
    try:
        geohash = geohash2.encode(latitude, longitude, precision=10)
        boundary = calculate_radius_boundary(geohash)
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(boundary)

        # GeoHash range query
        min_geohash = geohash2.encode(min_lat, min_lon, precision=10)
        max_geohash = geohash2.encode(max_lat, max_lon, precision=10)
        messages = db.child("messages").order_by_child("geohash").start_at(min_geohash).end_at(max_geohash).get().val()

        # Filter messages by actual distance
        center_point = (latitude, longitude)
        filtered_messages = []
        for message_id, message in messages.items():
            message_coords = (message['latitude'], message['longitude'])
            if is_within_radius(center_point, message_coords, 10):
                filtered_messages.append(message)

        return JSONResponse(content=filtered_messages, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_radius_boundary(geohash, radius_meters=10, num_points=32):
    # Decode geohash to get center latitude and longitude
    lat, lon, _, _ = geohash2.decode_exactly(geohash)

    # Calculate points on the circle boundary
    circle_points = []
    for bearing in np.linspace(0, 360, num_points):
        boundary_point = distance(meters=radius_meters).destination((lat, lon), bearing)
        circle_points.append((boundary_point.latitude, boundary_point.longitude))

    return circle_points

def get_bounding_box(boundary_points):
    """
    Calculate the bounding box for a set of geographical points.

    Parameters:
    boundary_points (list of tuples): A list of (latitude, longitude) tuples.

    Returns:
    tuple: A tuple containing the min and max latitude, and the min and max longitude.
    """
    min_lat = min(point[0] for point in boundary_points)
    max_lat = max(point[0] for point in boundary_points)
    min_lon = min(point[1] for point in boundary_points)
    max_lon = max(point[1] for point in boundary_points)

    return min_lat, max_lat, min_lon, max_lon


def is_within_radius(center, point, radius_meters):
    """
    Check if a point is within a specified radius of a center point.

    Parameters:
    center (tuple): A tuple (latitude, longitude) for the center point.
    point (tuple): A tuple (latitude, longitude) for the point to check.
    radius_meters (float): The radius in meters.

    Returns:
    bool: True if the point is within the radius of the center point, False otherwise.
    """
    return great_circle(center, point).meters <= radius_meters


@app.delete("/deleteMessage/{messageID}")
async def deleteMessage(messageID: str):
    try:
        response = db.child("messages").child(messageID).remove()
        return response
    except Exception as e:
        print(f"Error occured while deleting message: {e}")


#delete user account


#helper method to get the current reaction of user on the message, if any
def getCurrentReaction(key: str):
    try:
        res = db.child("reactions").order_by_child("reaction_id").equal_to(key).get().val()
        return res
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    

#helper method to update the reactions in message database accordingly
def updateReactions(message_id: str, reaction_type: int, prev_reaction: int):
    try:        
        message = db.child("messages").child(message_id).get().val()
        cur_likes = 0
        cur_dislikes = 0
        if message['likes']:
            cur_likes = message['likes']

        if message['dislikes']:
            cur_dislikes = message['dislikes']


        #if prev reaction was like/dislike, then remove it
        if prev_reaction == 1:
            cur_likes -= 1
        elif prev_reaction == -1:
            cur_dislikes -= 1
        
        if reaction_type == 1:
            cur_likes += 1
        elif reaction_type == -1:
            cur_dislikes += 1

        message['likes'] = cur_likes
        message['dislikes'] = cur_dislikes

        response = db.child('messages').child(message_id).update(message)

        return JSONResponse(content ={"message": response},
                            status_code = 200)


    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = "error with update Reactions"
        )



#change likes/dislikes
#accepts: userid, messageid, and reaction type.
#if reaction type is like/dislike, it updates accordingly. If it is none, then it removes any reaction
#update the message accordingly
@app.post("/changeReactions")
async def changeReactions(reaction_data:ReactionsSchema):

    try:
        #extract the correct information from input
        data = reaction_data.dict()
        user_uid = data['user_uid']
        message_id = data['message_id']
        reaction_type = data['reaction_type']
        key = message_id + ":" + user_uid


        #check if there is any existing reaction

        cur_reaction_key = None
        cur = getCurrentReaction(key)
        prev_reaction = 0

        #if there is existing one
        if cur:
            for key in cur:
                cur_reaction_key = key
                prev_reaction = cur[key]['reaction_type']

        if prev_reaction != reaction_type:
            #update the message accordingly
            response = updateReactions(message_id, reaction_type, prev_reaction)
            if response.status_code != 200:
                raise HTTPException(
                    status_code = 500,
                    detail = "Error updating message data"
                )

            
            #store the data into reaction database

            store_data = {}
            store_data['reaction_id'] = key
            store_data['user_uid'] = user_uid
            store_data['message_id'] = message_id
            store_data['reaction_type'] = reaction_type
            store_data['timestamp'] = data["timestamp"].isoformat()
            #if reaction already existed

            if cur_reaction_key:
                result = db.child("reactions").child(cur_reaction_key).update(store_data)
            else:
                result = db.child("reactions").push(store_data)


            return JSONResponse(content ={"message": "Message updated successfully", 
                                          "result": result},
                                status_code = 200)
        else:
            return JSONResponse(content={"message": "Already liked/disliked"})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


#get all posts that a user liked

if __name__ == "__main__":
    uvicorn.run("main:app",reload=True)


