<img src="https://developer-blogs.nvidia.com/wp-content/uploads/2018/12/catboost_hero.png" width="100%">

# Recommender System API

This repository contains the code for a personalized recommendation system API. The system is designed to provide personalized text post recommendations based on user data. The goal was to create an API that would return JSONs with text posts on request.

## Repository Structure

The repository consists of the following main files:

1. `features_uploader.ipynb`: This Jupyter notebook is used for gathering and transforming data, which is then uploaded to an SQL server for model training. It includes methods for data extraction, transformation, and loading (ETL).

2. `training.ipynb`: This Jupyter notebook contains the code for training the recommendation model. It includes data preprocessing, model training, and model evaluation steps. Various machine learning algorithms and techniques are used in this process.

3. `service.py`: This is the main service file for the API. It handles API requests and responses, and uses the trained model to generate recommendations. It includes methods for handling HTTP requests, processing data, and returning responses.

## Data

The data used in this project consists of three tables:

1. `user_data`: Contains information about users such as age, city, country, experience group, gender, operating system, and user ID. This table has 163,205 entries.

2. `post_text_df`: Contains information about text posts such as post ID, text content, and topic. This table has 7,023 entries.

3. `feed_data`: Contains information about user-to-post interactions such as timestamp, user ID, post ID, action, and target. This table has 76,892,800 entries.

## Feature Engineering

A combined approach was used to create features from both users and posts. Techniques such as accumulative likes on posts, time decomposition, Truncated Singular Value Decomposition (Truncated SVD), and category encoding were used. The Catboost model was pre-trained and its integrated importance features were used to select the best features. Features with potential information leakage were deleted.

## Model Training

The Catboost model was trained using custom metrics 'AUC' and 'NDCG' to align more with the Hitrate@5 metric used for evaluation. The Hitrate@5 is not a part of the Catboost library, so a custom implementation was used.

## Model Performance

The Hitrate@5, which shows the likelihood of at least one of the 5 recommended posts being liked by the user, was 0.63 on the test set.

## API Usage

The FastAPI takes the following parameters using the GET method:

- `id`: The user's ID for whom the posts are requested.
- `time`: A datetime object, e.g., `datetime.datetime(year=2021, month=1, day=3, hour=14)`.
- `limit`: The number of posts for the user.

The API returns 5 posts in the following format:

```json
[
  {
    "id": 345,
    "text": "COVID-19 runs wild....",
    "topic": "news"
  }, 
  {
    "id": 134,
    "text": "Chelsea FC wins UEFA..",
    "topic": "news"
  }, 
  ...
]
```

## Setup and Usage

### Prerequisites

- Python 3.x
- Jupyter Notebook
- Required Python libraries: (list any libraries that are not included in the standard library)

### Installation

1. Clone this repository to your local machine.
2. Install the required Python libraries.
3. Run the `features_uploader.ipynb` notebook to gather and transform data.
4. Run the `training.ipynb` notebook to train the model.
5. Run `service.py` to start the API

Here is a diagram that illustrates the workflow of the recommendation system:

![Workflow Diagram](https://showme.redstarplugin.com/s/HhAbRWIt)

You can [edit this diagram online](https://showme.redstarplugin.com/s/BbOjZHXl) if you want to make any changes.

In this workflow:

1. User data is extracted, transformed, and loaded (ETL) in the `features_uploader.ipynb` notebook.
2. The transformed data is uploaded to an SQL server.
3. The `training.ipynb` notebook trains the recommendation model using the uploaded data.
4. The `service.py` file handles API requests and uses the trained model to generate recommendations.
5. The recommendations are returned to the user.

## Contributing

Contributions are welcome! Please read the [contributing guidelines](link-to-guidelines) before getting started.

## License

This project is licensed under the terms of the (your license) - see the [LICENSE](LICENSE) file for details.

