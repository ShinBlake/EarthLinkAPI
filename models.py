from pydantic import BaseModel, Field
from datetime import datetime

class SignUpSchema(BaseModel):
    email:str
    password:str

    class Config:
        schema_extra ={
            "example":{
                "email": "sample@gmail.com",
                "password": "samplepass123"
            }
        }

class LoginSchema(BaseModel):
    email:str
    password:str

    class Config:
        schema_extra ={
            "example":{
                "email": "sample@gmail.com",
                "password": "samplepass123"
            }
        }


class MessageSchema(BaseModel):
    user_uid: str = Field(..., title="User UID", description="The unique identifier for the user")
    message_content: str = Field(..., title="Message Content", description="The content of the message")
    latitude: float = Field(..., title="Latitude", description="The latitude where the message was posted")
    longitude: float = Field(..., title="Longitude", description="The longitude where the message was posted")
    timestamp: datetime = Field(default_factory=datetime.now, title="Timestamp", description="The date and time when the message was posted")
    likes: int
    dislikes: int

    class Config:
        schema_extra = {
            "example": {
                "user_uid": "user_12345",
                "message_content": "This is a sample message.",
                "latitude": 34.052235,
                "longitude": -118.243683,
                "timestamp": datetime.now().isoformat(),
                "likes": 0,
                "dislikes": 0
            }
        }


class ReactionsSchema(BaseModel):
    user_uid: str = Field(..., title="User UID", description="The unique identifier for the user")
    message_id: str
    reaction_type: int
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        schema_extra = {
            "example": {
                "user_uid": "example_user",
                "message_id": "example_message",
                "reaction_type": "like",
                "timestamp": datetime.now().isoformat()
            }
        }


class ChangeUserInfoSchema(BaseModel):
    user_uid: str
    bio : str
    profile_pic: str
    username : str

    class Config:
        schema_extra = {
            "example": {
                "user_uid": "example_user",
                "bio": "string",
                "profile_pic": "link to picture",
                "username": "string"
            }
        }

