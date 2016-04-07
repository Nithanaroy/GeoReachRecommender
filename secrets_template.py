import os


def env():
    # Common Environment Settings
    os.environ['maps_api_key'] = '<YOUR_GOOGLE_MAPS_API_KEY>'
    # Return the function handler for the type of environment you want to set
    return dev


def prod():
    os.environ['debug_server'] = "False"
    os.environ['neo_db_url'] = '<YOUR_PROD_NEO4J_CONNECTION_URL>'
    os.environ['mongo_connection_url'] = "<YOUR_PROD_MONGODB_CONNECTION_URL>"


def dev():
    os.environ['debug_server'] = "True"
    os.environ['neo_db_url'] = '<YOUR_DEV_NEO4J_CONNECTION_URL>'
    os.environ['mongo_connection_url'] = "mongodb://localhost:27017"
