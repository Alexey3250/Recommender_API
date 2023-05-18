# Import necessary modules and libraries
import os
from catboost import CatBoostClassifier, Pool, CatBoost
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query 
from datetime import datetime
from pydantic import BaseModel, Field
import logging
import pydantic

'''
MODEL LOADING FUNCTIONS
'''
# Check if the code is running in LMS or locally
def get_model_path(path: str) -> str:
    """Please do not change this code"""
    if os.environ.get("IS_LMS") == "1":  # check where the code is running in LMS or locally. A bit of magic
        MODEL_PATH = '/workdir/user_input/model'
    else:
        MODEL_PATH = path
    return MODEL_PATH

class CatBoostWrapper(CatBoost):
    def predict_proba(self, X):
        return self.predict(X, prediction_type='Probability')

# Load model
def load_models():
    model_path = get_model_path("catboost_model_1.cbm")
    model = CatBoostWrapper()
    model.load_model(model_path)
    return model


'''
FETCHING DATA FROM DATABASE
'''

# Define function to fetch data from PostgreSQL database
def batch_load_sql(query: str) -> pd.DataFrame:
    CHUNKSIZE = 200000
    engine = create_engine(
        "postgresql://robot-startml-ro:pheiph0hahj1Vaif@"
        "postgres.lab.karpov.courses:6432/startml"
    )
    conn = engine.connect().execution_options(stream_results=True)
    chunks = []
    for chunk_dataframe in pd.read_sql(query, conn, chunksize=CHUNKSIZE):
        chunks.append(chunk_dataframe)
    conn.close()
    return pd.concat(chunks, ignore_index=True)

def load_features() -> pd.DataFrame:
    query = "a-efimik_features_lesson_22_4"
    return batch_load_sql(query)

def caching_predictions(feed_data, model):
    # Get a list of unique users from the feed data
    unique_users = feed_data['user_id'].unique()

    # Create a dictionary mapping each unique user to a group ID
    group_id_dict = {user_id: idx for idx, user_id in enumerate(unique_users)}
    
    # Add a new column to the feed data, mapping each user to their group ID
    feed_data['group_id'] = feed_data['user_id'].map(group_id_dict)

    # Sort the feed data by group ID
    feed_data_sorted = feed_data.sort_values(by='group_id')
    
    # Create a Pool object for CatBoost, dropping the 'user_id' column and using 'group_id' for grouping
    data_pool = Pool(feed_data_sorted.drop(columns=['user_id']), group_id=feed_data_sorted['group_id'])
    
    # Use the model to predict probabilities for each group, and take the probability of the positive class
    y_pred_proba = model.predict_proba(data_pool)[:, 1]
    
    # Add the predicted probabilities to the feed data as a new column
    feed_data['pred_proba'] = y_pred_proba
    
    # For each user, find the top 5 posts with the highest predicted probabilities
    top_5_posts = feed_data.groupby('user_id').apply(lambda x: x.nlargest(5, 'pred_proba')['post_id'])
    
    # Convert the top 5 posts for each user to a dictionary
    top_5_posts_dict = top_5_posts.reset_index().groupby('user_id')['post_id'].apply(list).to_dict()
    
    # Return the dictionary of top 5 posts for each user
    return top_5_posts_dict

        
class Post(BaseModel):
    id: int
    text: str
    topic: str

class PostList(BaseModel):
    posts: List[Post]

# Define function to get database session
def get_db():
    with SessionLocal() as db:
        return db

# Define variables for database connection
SQLALCHEMY_DATABASE_URL = "postgresql://robot-startml-ro:pheiph0hahj1Vaif@postgres.lab.karpov.courses:6432/startml"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
print("Connected to PostgreSQL database")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("Database session established")

Base = declarative_base()
print("Base class for defining database table established")


model = load_models()
print("Model loaded")

features = load_features()
print("Data loaded")

top_posts_dict = caching_predictions(features, model)
print("Predictions made")

'''
FAST API CODE
'''

class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    class Config:
        orm_mode = True # ORM stands for Object-Relational Mapping, a programming technology that links databases with object-oriented programming concepts, creating a "virtual object database".

app = FastAPI()

@app.get("/post/recommendations/", response_model=List[PostGet])
def recommended_posts(
        id: int, 
        time: datetime, 
        limit: int = 5) -> List[PostGet]:
    
    # Retrieve the top posts
    post_ids = top_posts_dict.get(id)
    
    if not post_ids:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve the posts from the database
    # You may need to implement this part according to your database setup
    query = "SELECT * FROM post_text_df WHERE post_id IN ({})".format(", ".join(map(str, post_ids[:limit])))
    df = pd.read_sql(query, engine)

    # Add a print statement to inspect the DataFrame
    print(df)
    print("Posts retrieved")
    # Add another print statement to inspect the list of records
    records = df.to_dict('records')
    print(records)
    print("Posts converted to dictionary")

    posts = []
    for rec in records:
        rec["id"] = rec.pop("post_id")  # change "post_id" to "id"
        try:
            posts.append(PostGet(**rec))
        except pydantic.error_wrappers.ValidationError as e:
            print(f"Validation error for record {rec}: {e}")

    return posts
