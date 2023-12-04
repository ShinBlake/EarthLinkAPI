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
from datetime import datetime, date, time



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

        data = {"UID" : user.uid, "email": email, "username": user.uid, "bio": "Say something about yourself...", "date_created": date.today().isoformat(), "profile_picture": "gs://earthlinks-7c491.appspot.com/person-24px.xml"}
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
                "token": token
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


@app.get("/getMessagesFromUser/{userID}/{sort_type}")
async def get_messages_from_user(userID: str, sort_type: int, search_term = None):
    try:
        messages = db.child("messages").order_by_child("user_uid").equal_to(userID).get().val()
        message_list = []

        if not messages:
            return JSONResponse(content={"message": "No messages found"}, status_code=200)

        for message_id, message_val in messages.items():
            message_val["message_id"] = message_id
            message_list.append(message_val)

        if search_term:
            message_list = [msg for msg in message_list if search_term.lower() in msg["message_content"].lower()]

        sorted_messages = sort_messages(message_list, 25, sort_type)

        return JSONResponse(content=sorted_messages, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    

@app.get("/getNumberMessages/{userID}")
async def get_number_messages(userID: str):
    try:
        messages = db.child("messages").order_by_child("user_uid").equal_to(userID).get().val()
        if not messages:
            return JSONResponse(content={"message": "No messages found"}, status_code=200)
        return JSONResponse(content={"number_messages": len(messages)}, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#get messags within 80 meter radius sorted by timestamp
#sort type 0 = by timestamp
#sort type 1 = by number of likes
@app.get("/getMessagesByRadius/{latitude}/{longitude}/{max_number}/{sort_type}")
async def get_messages_by_radius(latitude: float, longitude: float, max_number: int, sort_type: int):
    try:

        #CHANGE THIS TO CHANGE THE RADIUS
        cur_radius = 80


        geohash = geohash2.encode(latitude, longitude, precision=10)
        boundary = calculate_radius_boundary(geohash, radius_meters=cur_radius)
        min_lat, max_lat, min_lon, max_lon = get_bounding_box(boundary)

        # GeoHash range query
        min_geohash = geohash2.encode(min_lat, min_lon, precision=10)
        max_geohash = geohash2.encode(max_lat, max_lon, precision=10)
        messages = db.child("messages").order_by_child("geohash").start_at(min_geohash).end_at(max_geohash).get().val()

        if not messages:
            return JSONResponse(content = {"message": "No messages found around this area"}, status_code= 200)
        # Filter messages by actual distance
        center_point = (latitude, longitude)
        filtered_messages = []
        for message_id, message in messages.items():
            message_coords = (message['latitude'], message['longitude'])
            if is_within_radius(center_point, message_coords, cur_radius):
                message["message_id"] = message_id
                filtered_messages.append(message)

        
        #loop through 
        if not filtered_messages:
            return JSONResponse(content = {"message": "No messages found around this area"}, status_code= 200)
    
        #sort by timestamp
        sorted_messages = sort_messages(filtered_messages, max_number, sort_type)
        clusters = cluster_messages(sorted_messages, radius_meters=5)

        return JSONResponse(content=clusters, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def sort_messages(messages, max_number, sort_type):
    def parse_datetime(timestamp):
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            return datetime.min

    def sort_key(item):
        if sort_type == 0:
            return parse_datetime(item.get("timestamp", ""))
        elif sort_type == 1:
            return item.get('likes', 0)

    sorted_data = sorted(messages, key=sort_key, reverse=True)
    return sorted_data[:max_number]


#cluster the list of messages into list of messages within 5 meters of eachother
def cluster_messages(messages, radius_meters=5):
    # Convert messages to a list of (id, latitude, longitude)
    # message_list = [(mid, m['latitude'], m['longitude']) for mid, m in messages.items()]
    
    clusters = []
    while messages:
        # Start a new cluster
        cluster = []
        base_message = messages.pop(0)
        cluster.append(base_message)
        
        # Check for nearby messages
        i = 0
        while i < len(messages):
            if is_within_radius((base_message.get("latitude"), base_message.get("longitude")), (messages[i].get("latitude"), messages[i].get("longitude")), radius_meters):
                # Add to cluster and remove from list
                cluster.append(messages.pop(i))
            else:
                i += 1

        # Add cluster to list of clusters
        clusters.append(cluster)

    return clusters


def calculate_radius_boundary(geohash, radius_meters, num_points=32):
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
        return JSONResponse(content = {"message": "post {messageID} successfully deleted", "response" : response})
    except Exception as e:
        print(f"Error occured while deleting message: {e}")



#helper method to get the current reaction of user on the message, if any
def getCurrentReaction(reaction_key: str):
    try:
        res = db.child("reactions").order_by_child("reaction_id").equal_to(reaction_key).get().val()
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

        if 'likes' in message:
            cur_likes = message['likes']

        if 'dislikes' in message:
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
        reaction_key = message_id + ":" + user_uid
        print(reaction_key)


        #check if there is any existing reaction

        cur_reaction_key = None
        cur = getCurrentReaction(reaction_key)
        print(cur)
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
            print(reaction_key)
            store_data['reaction_id'] = reaction_key
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

#helper method to get all reactions by a specific user
def getAllReactionsByUser(user_uid:str):
    try:
        reactions = db.child("reactions").order_by_child("user_uid").equal_to(user_uid).get().val()
        return reactions
    except Exception as e:
        print("Error getting all reactions by user")


def getMessagesByID(message_ids:list):
    try:
        messages = {}
        for message_id in message_ids:
            message = db.child("messages").child(message_id).get().val()
            messages[message_id] = message
        return messages
    except Exception as e:
        print("Error getting all message from message ID's")

#get all posts that a user liked in form of dictionary,
# Returns: dictionary (key = message_id, value = message data content)
@app.get("/getLikedPostsByUser/{user_uid}")
async def getLikedPostsByUser(user_uid: str):
    try:
        reactions = getAllReactionsByUser(user_uid)
        message_ids= []
        for entry in reactions.values():
            if entry.get('reaction_type') == 1:
                message_ids.append(entry.get("message_id"))
        return JSONResponse(content = {"message": "reactions by user {user_uid}", 
                                       "reactions" : getMessagesByID(message_ids)},
                                       status_code = 200)
    
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )


#getting profile info
@app.get("/getUserInfo/{user_uid}")
async def getUserInfo(user_uid:str):
    try:
        user_info = db.child("users").order_by_child("UID").equal_to(user_uid).get().val()
        return JSONResponse(content = {"message": "User info for user {user_uid} successfully retrieved", "user info": user_info},
                            status_code = 200)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )


#deleting user account
@app.delete("/deleteUser/{user_uid}")
async def deleteUser(user_uid:str):
    try:
        response = db.child("users").order_by_child("UID").equal_to(user_uid).remove()
        return JSONResponse(content = {"message": "user {user_uid} successfully deleted", "response" : response},
                            status_code = 200)
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )

#change user info
@app.post("/changeUserInfo")
async def changeUserInfo(change_info: ChangeUserInfoSchema):
    try:
        user = db.child("users").order_by_child("UID").equal_to(change_info.user_uid).get().val()
        new_info = {}
        for cur in user.values():
            new_info = cur
            new_info["bio"] = change_info.bio
            new_info["username"] = change_info.username
            new_info["profile_picture"] = change_info.profile_pic

        
        
        result = db.child("users").order_by_child("UID").equal_to(change_info.user_uid).update(new_info)
        return result
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )

@app.get("/getNumberMessages/{userID}")
async def get_number_messages(userID: str):
    try:
        messages = db.child("messages").order_by_child("user_uid").equal_to(userID).get().val()
        if not messages:
            return JSONResponse(content={"message": "No messages found"}, status_code=200)
        return JSONResponse(content={"number_messages": len(messages)}, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    uvicorn.run("main:app",reload=True)


