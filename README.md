# Frame — Movie Recommendation System

Frame is a content-based movie recommendation application. Select a film from the catalogue and the application returns similar movies based on their plot descriptions, taglines, original language, and genres.

The project began as an exploratory data-analysis and machine-learning notebook, and was then turned into a working web application with a FastAPI backend and a browser interface.

## What I built

- Cleaned and prepared a movie metadata dataset.
- Explored missing values, duplicate records, popularity, ratings, and genre coverage in `EDA.ipynb`.
- Converted genre lists into machine-readable binary features.
- Combined overview, tagline, and original language into a text feature.
- Used TF-IDF to turn text into numeric features.
- Combined the text features with the genre features.
- Trained a nearest-neighbours model using cosine similarity.
- Created a `recommend_movie()` function that returns a chosen number of similar films.
- Saved the trained model, feature matrix, movie-title index, and movie information as `movie_recommender.joblib`.
- Built a FastAPI service for health checks, title search, and recommendations.
- Built a responsive frontend with title search, a recommendation-count selector, and recommendation cards.
- Added graceful handling for unknown and duplicate movie titles.

## How recommendations work

Each movie is represented by two kinds of features:

1. **Text features**: TF-IDF vectors created from its overview, tagline, and original language.
2. **Genre features**: binary values representing genres such as Action, Drama, Comedy, and Science Fiction.

The application combines these features and uses cosine distance with `NearestNeighbors` to find the closest films. A higher similarity score means the films have more closely related content and genres according to this model.

## Project structure

```text
.
├── EDA.ipynb                  # Data cleaning, exploration, and feature preparation
├── model.ipynb                # Model training and notebook experiments
├── api.py                     # FastAPI application and recommendation endpoints
├── movie_recommender.joblib   # Saved model artifact required by the web app
├── requirements.txt           # Python dependencies
├── frontend/
│   ├── index.html             # Frontend markup
│   ├── styles.css             # Frontend styling
│   └── app.js                 # Search and recommendation interactions
└── README.md
```

The CSV data files are used during exploration and training. The deployed application uses `movie_recommender.joblib` at runtime.

## Run locally

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
```

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the application:

```bash
fastapi dev api.py
```

Open the app at [Movie Recommendation System](https://movie-recommendation-system-75z0.onrender.com/). Interactive API documentation is available at [the deployed API documentation](https://movie-recommendation-system-75z0.onrender.com/docs).

## API endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Serves the movie recommendation interface. |
| `GET /health` | Reports whether the service is running. |
| `GET /movies/search?q=heat` | Searches the catalogue by partial title. |
| `GET /recommendations?title=Heat&limit=5` | Returns similar movies for an exact title. |

## Creating the model artifact

Run the training cells in `model.ipynb`, then save the required artifacts with Joblib. The API expects a file named `movie_recommender.joblib` in the project root containing:

- `knn`
- `feature_matrix`
- `movie_matrix`
- `movies`

## Future improvements

- Add release years so users can distinguish movies with the same title.
- Use posters and richer movie metadata.
- Add a favourites/watchlist feature and collect user feedback.
- Add collaborative filtering to create personalized hybrid recommendations.
- Write endpoint and model tests, then add continuous deployment.
