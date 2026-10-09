"""FastAPI service for the movie recommendation system.

Start locally with:
    fastapi dev api.py

The service expects a ``movie_recommender.joblib`` artifact next to this file.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "movie_recommender.joblib"
STATIC_DIR = BASE_DIR / "static"


class MovieSearchResult(BaseModel):
    movie_id: int
    title: str
    vote_average: float | None = None
    popularity: float | None = None


class Recommendation(BaseModel):
    movie_id: int
    title: str
    similarity: float
    overview: str | None = None
    vote_average: float | None = None
    popularity: float | None = None


def optional_float(value: Any) -> float | None:
    """Convert pandas/numpy numeric values to JSON-safe floats."""
    if value is None or pd.isna(value):
        return None
    return float(value)


def optional_text(value: Any) -> str | None:
    """Convert empty or missing dataframe text values to JSON null."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def load_artifacts() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {MODEL_PATH}. "
            "Create it by running your training notebook's joblib.dump cell."
        )

    artifacts = joblib.load(MODEL_PATH)
    required_keys = {"knn", "feature_matrix", "movie_matrix", "movies"}
    missing = required_keys - artifacts.keys()
    if missing:
        raise ValueError(f"Model artifact is missing required keys: {sorted(missing)}")

    artifacts["movies"] = artifacts["movies"].reset_index(drop=True)
    return artifacts


def resolve_movie_id(
    movie_matrix: pd.Series, movies: pd.DataFrame, normalized_title: str
) -> int:
    """Return one movie ID, choosing the most popular film when titles repeat."""
    matched_ids = movie_matrix.loc[normalized_title]

    # A unique title produces a scalar; duplicate titles produce a Series.
    if not isinstance(matched_ids, pd.Series):
        return int(matched_ids)

    candidate_ids = [int(movie_id) for movie_id in matched_ids.tolist()]
    candidates = movies.iloc[candidate_ids].copy()
    candidates["_movie_id"] = candidate_ids
    candidates["_popularity"] = pd.to_numeric(
        candidates.get("popularity"), errors="coerce"
    ).fillna(0)
    return int(candidates.sort_values("_popularity", ascending=False).iloc[0]["_movie_id"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loading once at startup keeps recommendation requests fast.
    app.state.artifacts = load_artifacts()
    yield


app = FastAPI(
    title="Movie Recommendation API",
    version="1.0.0",
    description="Content-based movie recommendations using text and genre similarity.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/movies/search", response_model=list[MovieSearchResult])
def search_movies(
    q: str = Query(..., min_length=1, description="Part of a movie title"),
    limit: int = Query(10, ge=1, le=50),
) -> list[MovieSearchResult]:
    movies: pd.DataFrame = app.state.artifacts["movies"]
    query = q.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Search query cannot be blank.")

    matches = movies[movies["title"].str.contains(query, case=False, na=False, regex=False)]
    return [
        MovieSearchResult(
            movie_id=int(index),
            title=str(row["title"]),
            vote_average=optional_float(row.get("vote_average")),
            popularity=optional_float(row.get("popularity")),
        )
        for index, row in matches.head(limit).iterrows()
    ]


@app.get("/recommendations", response_model=list[Recommendation])
def get_recommendations(
    title: str = Query(..., min_length=1, description="Exact movie title"),
    limit: int = Query(5, ge=1, le=20),
) -> list[Recommendation]:
    artifacts = app.state.artifacts
    movie_matrix: pd.Series = artifacts["movie_matrix"]
    movies: pd.DataFrame = artifacts["movies"]
    normalized_title = title.strip().lower()

    if not normalized_title or normalized_title not in movie_matrix.index:
        raise HTTPException(
            status_code=404,
            detail="Movie not found. Use /movies/search?q=... to find the exact title.",
        )

    movie_id = resolve_movie_id(movie_matrix, movies, normalized_title)
    max_neighbors = min(limit + 1, len(movies))
    distances, movie_ids = artifacts["knn"].kneighbors(
        artifacts["feature_matrix"][movie_id], n_neighbors=max_neighbors
    )

    recommendations = []
    for distance, recommended_id in zip(distances[0], movie_ids[0]):
        if int(recommended_id) == movie_id:
            continue

        row = movies.iloc[int(recommended_id)]
        recommendations.append(
            Recommendation(
                movie_id=int(recommended_id),
                title=str(row["title"]),
                similarity=round(float(1 - distance), 4),
                overview=optional_text(row.get("overview")),
                vote_average=optional_float(row.get("vote_average")),
                popularity=optional_float(row.get("popularity")),
            )
        )
        if len(recommendations) == limit:
            break

    return recommendations
