"""
Entrée serverless Vercel — seule fonction Python du projet.

Vercel transforme chaque .py de api/ en fonction ; le code applicatif vit
dans backend/app.py et les rewrites de vercel.json routent tout /api/* ici.
La variable `app` (ASGI) est détectée automatiquement par le runtime Python.
"""
from backend.app import app  # noqa: F401
