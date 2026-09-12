from datetime import date

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from movies.models import Movie


class Command(BaseCommand):
    help = "Imports currently playing movies from TMDB"

    def handle(self, *args, **options):
        token = settings.TMDB_API_TOKEN

        if not token:
            raise CommandError("TMDB_API_TOKEN was not found.")

        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json",
            "User-Agent": "CineBookAI/1.0",
        }

        retry_strategy = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
        )

        session = requests.Session()
        session.headers.update(headers)
        session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

        try:
            response = session.get(
                "https://api.themoviedb.org/3/movie/now_playing",
                params={"language": "en-US", "page": 1},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise CommandError(f"Could not contact TMDB: {error}")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for item in response.json().get("results", []):
            release_date_text = item.get("release_date")

            if not release_date_text:
                skipped_count += 1
                continue

            try:
                release_date = date.fromisoformat(release_date_text)
            except ValueError:
                skipped_count += 1
                continue

            tmdb_id = item["id"]
            poster_path = item.get("poster_path")
            poster_url = ""

            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"

            try:
                details_response = session.get(
                    f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                    params={"language": "en-US"},
                    timeout=20,
                )
                details_response.raise_for_status()
            except requests.RequestException:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    f"Skipped {item.get('title', 'a movie')} because TMDB temporarily disconnected."
                ))
                continue

            details = details_response.json()

            genre = ", ".join(
                movie_genre["name"] for movie_genre in details.get("genres", [])
            )[:100] or "Other"

            _, created = Movie.objects.update_or_create(
                tmdb_id=tmdb_id,
                defaults={
                    "title": item.get("title", "Untitled"),
                    "genre": genre,
                    "language": details.get("original_language", "en").upper(),
                    "duration_minutes": details.get("runtime") or 120,
                    "release_date": release_date,
                    "rating": item.get("vote_average") or 0,
                    "description": item.get("overview") or "Description not available.",
                    "poster_url": poster_url,
                    "is_now_showing": True,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"TMDB sync complete: {created_count} added, "
            f"{updated_count} updated, {skipped_count} skipped."
        ))