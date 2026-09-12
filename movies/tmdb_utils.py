
import os

import requests
from dotenv import load_dotenv


load_dotenv("tmdb.env")


def fetch_tmdb_movie(tmdb_id):
    api_key = os.getenv("TMDB_API_KEY")

    if not api_key:
        raise ValueError("TMDB_API_KEY is missing from .env")

    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"

    params = {
        "api_key": api_key,
        "language": "en-US",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        raise ValueError(
            f"TMDB request failed: {response.status_code}"
        )

    data = response.json()

    poster_path = data.get("poster_path")

    poster_url = ""

    if poster_path:
        poster_url = (
            f"https://image.tmdb.org/t/p/w500{poster_path}"
        )

    return {
        "title": data.get("title", ""),
        "poster_url": poster_url,
        "description": data.get("overview", ""),
        "duration_minutes": data.get("runtime") or 0,
        "rating": data.get("vote_average") or 0,
        "release_date": data.get("release_date") or None,
        "genres": ", ".join(
            genre["name"]
            for genre in data.get("genres", [])
        ),
    }
