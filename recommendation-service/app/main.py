"""Recommendation Service — external API integrations for events, concerts, etc."""

from __future__ import annotations

import json
import logging
from typing import Optional
from datetime import date

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import RecommendationSettings
from shared.auth import AuthHandler

logger = logging.getLogger("recommendation-service")
settings = RecommendationSettings()
auth = AuthHandler(settings)  # type: ignore[arg-type]

app = FastAPI(title="MeetSync - Recommendation Service", version="0.1.0", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
CACHE_TTL = 3600  # 1 hour


class Recommendation(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    url: str | None = None
    image_url: str | None = None
    price: str | None = None
    date: str | None = None
    location: str | None = None
    source: str | None = None


@app.get("/health")
async def health():
    return {"service": "recommendation-service", "status": "ok"}


async def _get_cache(key: str) -> list | None:
    data = await redis_client.get(f"recommendation:{key}")
    if data:
        return json.loads(data)
    return None


async def _set_cache(key: str, value: list, ttl: int = CACHE_TTL) -> None:
    await redis_client.setex(f"recommendation:{key}", ttl, json.dumps([r.model_dump() if isinstance(r, Recommendation) else r for r in value], default=str))


# ─── OpenTripMap ────────────────────────────────────────────────


async def _fetch_opentripmap(city: str, category: Optional[str] = None) -> list[Recommendation]:
    """Fetch attractions from OpenTripMap."""
    if not settings.opentripmap_api_key:
        return []

    cache_key = f"opentripmap:{city}:{category or 'all'}"
    cached = await _get_cache(cache_key)
    if cached:
        return [Recommendation(**r) for r in cached]

    # Geocode city first
    try:
        async with httpx.AsyncClient() as client:
            geo_resp = await client.get(
                "https://api.opentripmap.com/0.1/en/places/geoname",
                params={"name": city, "apikey": settings.opentripmap_api_key},
            )
            if geo_resp.status_code != 200:
                return []
            geo_data = geo_resp.json()
            lat, lon = geo_data.get("lat"), geo_data.get("lon")
            if not lat or not lon:
                return []

            # Get places
            radius = 5000
            kinds = category or "cultural"
            places_resp = await client.get(
                "https://api.opentripmap.com/0.1/en/places/radius",
                params={
                    "radius": radius, "lon": lon, "lat": lat,
                    "kinds": kinds, "limit": 20,
                    "apikey": settings.opentripmap_api_key,
                },
            )
            if places_resp.status_code != 200:
                return []
            places = places_resp.json().get("features", [])

            results = []
            for p in places[:10]:
                props = p.get("properties", {})
                results.append(Recommendation(
                    title=props.get("name", "Unknown"),
                    description=props.get("description", ""),
                    category=kinds,
                    source="OpenTripMap",
                ))
            await _set_cache(cache_key, results)
            return results
    except Exception as e:
        logger.error("OpenTripMap error: %s", e)
        return []


# ─── OpenWeather ────────────────────────────────────────────────


async def _fetch_weather(city: str, forecast_date: Optional[date] = None) -> list[Recommendation]:
    if not settings.openweather_api_key:
        return []

    cache_key = f"weather:{city}:{forecast_date or 'today'}"
    cached = await _get_cache(cache_key)
    if cached:
        return [Recommendation(**r) for r in cached]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": settings.openweather_api_key, "units": "metric", "lang": "en"},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            temp = data.get("main", {}).get("temp")
            desc = data.get("weather", [{}])[0].get("description", "")
            results = [Recommendation(
                title=f"Weather in {city}",
                description=f"{desc.capitalize()}, {temp:.0f}°C",
                category="weather",
                source="OpenWeather",
            )]
            await _set_cache(cache_key, results, ttl=1800)  # 30 min
            return results
    except Exception as e:
        logger.error("OpenWeather error: %s", e)
        return []


# ─── Ticketmaster ──────────────────────────────────────────────


async def _fetch_ticketmaster(city: str, category: Optional[str] = None) -> list[Recommendation]:
    if not settings.ticketmaster_api_key:
        return []

    cache_key = f"ticketmaster:{city}:{category or 'all'}"
    cached = await _get_cache(cache_key)
    if cached:
        return [Recommendation(**r) for r in cached]

    try:
        async with httpx.AsyncClient() as client:
            params = {
                "apikey": settings.ticketmaster_api_key,
                "city": city,
                "size": 10,
                "locale": "*",
            }
            if category:
                params["classificationName"] = category

            resp = await client.get(
                "https://app.ticketmaster.com/discovery/v2/events.json",
                params=params,
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            events = data.get("_embedded", {}).get("events", [])

            results = []
            for ev in events[:10]:
                results.append(Recommendation(
                    title=ev.get("name", "Unknown Event"),
                    description=ev.get("description", ""),
                    category=category or ev.get("classifications", [{}])[0].get("segment", {}).get("name"),
                    url=ev.get("url"),
                    image_url=ev.get("images", [{}])[0].get("url") if ev.get("images") else None,
                    date=ev.get("dates", {}).get("start", {}).get("localDate"),
                    location=ev.get("_embedded", {}).get("venues", [{}])[0].get("name"),
                    source="Ticketmaster",
                ))
            await _set_cache(cache_key, results)
            return results
    except Exception as e:
        logger.error("Ticketmaster error: %s", e)
        return []


# ─── API Endpoints ─────────────────────────────────────────────


@app.get("/api/v1/recommendations", response_model=list[Recommendation])
async def get_recommendations(
    city: str = Query(default="Moscow"),
    category: str | None = Query(default=None),
    user_id: int = Depends(auth.get_current_user_id),
):
    """Get recommendations from all available sources."""
    results: list[Recommendation] = []

    # Try each source in parallel
    import asyncio
    tasks = []
    tasks.append(_fetch_opentripmap(city, category))
    tasks.append(_fetch_weather(city))
    tasks.append(_fetch_ticketmaster(city, category))

    try:
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in task_results:
            if isinstance(r, list):
                results.extend(r)
            elif isinstance(r, Exception):
                logger.warning("Recommendation source error: %s", r)
    except Exception as e:
        logger.error("Gather error: %s", e)

    # De-duplicate by title
    seen = set()
    unique = []
    for r in results:
        if r.title and r.title not in seen:
            seen.add(r.title)
            unique.append(r)

    return unique


@app.get("/api/v1/recommendations/opentripmap", response_model=list[Recommendation])
async def get_opentripmap(
    city: str = Query(default="Moscow"),
    kinds: str | None = Query(default=None),
    user_id: int = Depends(auth.get_current_user_id),
):
    return await _fetch_opentripmap(city, kinds)


@app.get("/api/v1/recommendations/ticketmaster", response_model=list[Recommendation])
async def get_ticketmaster(
    city: str = Query(default="Moscow"),
    category: str | None = Query(default=None),
    user_id: int = Depends(auth.get_current_user_id),
):
    return await _fetch_ticketmaster(city, category)


@app.get("/api/v1/recommendations/weather", response_model=list[Recommendation])
async def get_weather(
    city: str = Query(default="Moscow"),
    user_id: int = Depends(auth.get_current_user_id),
):
    return await _fetch_weather(city)
