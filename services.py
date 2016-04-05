import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from py2neo import Graph
from bson.json_util import dumps
from html_services import html_api
from flask.ext.triangle import Triangle
import secrets

app = Flask(__name__)
Triangle(app)
app.register_blueprint(html_api)


@app.route('/business')
def business():
    """
    Finds businesses in a given region
    Query Params:   swlong - Southwest point longitude
                    swlat - Southwest point latitude
                    nelong - Northeast point longitude
                    nelat - Northeast point latitude
    :return: JSON array of business objects containing at least {_id, location, name}
    """
    nelat, nelong, swlat, swlong = get_coords_from_request()
    return cursor_tojson(business_in_loc(nelat, nelong, swlat, swlong), 'bids')


@app.route('/<bid>/reviewers')
def reviewers(bid):
    """
    Fetches the reviewers of a business
    :param bid: business ID as URL parameter
    :return: {uids: [users ids...]}
    """
    query = "MATCH (n:Person)-[:REVIEWED]->(b:Business {id: '%s'}) RETURN COLLECT(n.id);" % (bid,)
    return jsonify({'uids': graph.cypher.execute_one(query)})


@app.route('/<uid>/reviews')
def reviews(uid):
    """
    Fetches the list of businesses the user has reviewed
    Each `biz_obj` below has at least _id, name, location [longitude, latitude], stars
    :param uid: id of the user as a string
    :return: {reviewed: [{biz_obj}, {biz_obj}...]}
    """
    query = "MATCH (:Person {id: {uid}})-->(b:Business) RETURN COLLECT(DISTINCT b.id)"
    bids = graph.cypher.execute_one(query, uid=uid)
    businesses = db.business.find({"_id": {"$in": bids}})
    return cursor_tojson(businesses, 'reviewed')


@app.route('/<uid>/recommend')
def recommend(uid):
    """
    Recommend businesses to a user in a given region
    Region should be passed as a Query String
    Query Params:   swlong - Southwest point longitude
                    swlat - Southwest point latitude
                    nelong - Northeast point longitude
                    nelat - Northeast point latitude
    Algorithm:
    (1) Find all businesses in the given region which user didn't review
    (2) For each of those businesses find the shortest path from user node
    (3) Rank these paths and return the top 10
    :param uid: user id as a string
    :return: top 10 business recommendations
    """
    nelat, nelong, swlat, swlong = get_coords_from_request()
    unvisited_biz = biz_not_visited(nelat, nelong, swlat, swlong, uid)
    ranked_paths = sorted(paths_to_biz(uid, unvisited_biz), rank)[:11]  # return best 10
    return jsonify({"try": map(lambda b: b.end_node.properties['id'], ranked_paths)})


def rank(p1, p2):
    """
    Ranks two paths
    :param p1: First path object
    :param p2: Second path object
    :return: if p1 is ranked more than p2, then 1; if equal, then 0; else -1
    """
    if len(p1.relationships) > len(p2.relationships):
        return 1
    elif len(p1.relationships) == len(p2.relationships):
        return 0
    else:
        return -1


def paths_to_biz(uid, biz):
    """
    Finds paths from a person node to a list of business nodes
    :param uid: user id of the person, the starting node
    :param biz: list of business ids to which shortest paths have to be found
    :return: a list of Path objects
    """
    query = """
    UNWIND {businesses} as biz
    MATCH pa=shortestPath((n:Person {id: {uid}})-[*]->(b:Business {id: biz}))
    RETURN pa
    """
    paths = []
    x = 0
    while x < len(biz):
        paths += [p['pa'] for p in graph.cypher.execute(query, uid=uid, businesses=biz[x:x + 10])]
        x = min(x + 10, len(biz))
    return paths


def biz_not_visited(nelat, nelong, swlat, swlong, uid):
    """
    Fetches all the IDs of the business' which user did not visit in the region
    :param uid: id of the user
    :param nelat: Latitude of the northeast coordinate
    :param nelong: Longitude of the northeast coordinate
    :param swlat: Latitude of the southwest coordinate
    :param swlong: Longitude of the southwest coordinate
    :return: a list of business IDs
    """
    all_biz = set([b['_id'] for b in business_in_loc(nelat, nelong, swlat, swlong)])
    visited_query = "MATCH (:Person {id: {uid}})-[:REVIEWED]->(b:Business) WHERE b.id IN {biz} RETURN COLLECT(b.id);"
    visited_biz = set([i for i in graph.cypher.execute_one(visited_query, uid=uid, biz=all_biz)])
    return list(all_biz - visited_biz)


def business_in_loc(nelat, nelong, swlat, swlong):
    """
    Finds businesses in a given region
    :param nelat: Latitude of the northeast coordinate
    :param nelong: Longitude of the northeast coordinate
    :param swlat: Latitude of the southwest coordinate
    :param swlong: Longitude of the southwest coordinate
    :return: iterable cursor where each entity is a business
    """
    query = {"loc": {"$geoWithin": {"$box": [[swlong, swlat], [nelong, nelat]]}}}
    return db.business.find(query)


def get_coords_from_request():
    swlong = float(request.args.get('swlong').strip())
    swlat = float(request.args.get('swlat').strip())
    nelong = float(request.args.get('nelong').strip())
    nelat = float(request.args.get('nelat').strip())
    return nelat, nelong, swlat, swlong


def cursor_tojson(cursor, key):
    """
    Converts a cursor to a JSON object
    :param cursor: Mongo cursor
    :param key: string to use as a key in the result JSON object
    :return: {key: [values from cursor]}
    """
    bs = []
    for b in cursor:
        bs.append(b)
    return jsonify({key: bs});


if __name__ == '__main__':
    secrets.dev()  # set dev environment settings
    db = MongoClient().yelpdata
    graph = Graph("http://neo4j:%s@localhost:7474/db/data/" % (os.environ['neo_db_password']))
    app.run(debug=True)
