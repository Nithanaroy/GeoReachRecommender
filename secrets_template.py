import os


def dev():
    os.environ['maps_api_key'] = '<YOUR_GOOGLE_MAPS_API_KEY>'
    os.environ['neo_db_password'] = '<YOUR_NEO4J_DATABASE_PASSWORD>'
