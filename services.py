import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
from py2neo import Graph
from bson.json_util import dumps
from html_services import html_api
import secrets
from py2neo.packages.httpstream import http

app = Flask(__name__)
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


@app.route('/<bids>/info')
def bizinfo(bids):
    """
    Fetches the info about businesses
    :param bids: comma separated list of business IDs
    :return: JSON list of business objects
    """
    query = {'_id': {'$in': map(lambda x: x.strip(), bids.split(','))}}
    return cursor_tojson(db.business.find(query), 'about')


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


@app.route('/<uid>/reviews_test')
def reviews_test(uid):
    """
    Fetches the list of businesses the user has reviewed from the test dataset
    Each `biz_obj` below has at least _id, name, location [longitude, latitude], stars
    :param uid: id of the user as a string
    :return: {reviewed: [{biz_obj}, {biz_obj}...]}
    """
    bids = [b['business_id'] for b in db.reviews_test.find({'user_id': uid}, {'business_id': 1, '_id': 0})]
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
    :return: top 10 business recommendations. Complete business object is sent
    """
    nelat, nelong, swlat, swlong = get_coords_from_request()
    unvisited_biz = biz_not_visited(nelat, nelong, swlat, swlong, uid)
    print 'Not Visited Biz %d' % (len(unvisited_biz),)
    ranked_paths = sorted(paths_to_biz(uid, unvisited_biz), rank)[:10]  # return best 10
    return jsonify({"paths": [path_info(p) for p in ranked_paths]})
    # ranked_paths = sorted(paths_to_biz(uid, ['15LrCqlaxoKSzwL7dD0bnA']), rank)[:10]  # test call
    # test return statement below
    # return jsonify({"paths":[[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2013,2014,2015],"fans":6,"id":"hGvHc3YnSvAgUhSGEum5cA","name":"Mo"}},{"props":{"stars":4},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Food","Donuts","Coffee & Tea"],"id":"FuykdWajbSDj0hBY5DIuZQ","name":"Dunkin' Donuts"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2013,2014,2015],"fans":48,"id":"RsUNADZTrJ5xFXVMXJC1MQ","name":"Doug"}},{"props":{"stars":2},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Burgers","Fast Food","Restaurants"],"id":"LYLGCIqNQQrpMwOxJ1hlrg","name":"Smashburger"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2014,2015],"fans":7,"id":"1CGI66n0zKnK_mpMkdYkQQ","name":"Megan"}},{"props":{"stars":4},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Bars","Food","Breweries","Pubs","Nightlife","American (New)","Restaurants"],"id":"JokKtdXU7zXHcr20Lrk29A","name":"Four Peaks Brewing Co"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2013,2014,2015],"fans":48,"id":"RsUNADZTrJ5xFXVMXJC1MQ","name":"Doug"}},{"props":{"stars":4},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Pizza","Restaurants"],"id":"X1iWMwX_f9FJkyd-xcHVgA","name":"My Pie"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2009,2010,2011,2012,2013,2014,2015],"fans":63,"id":"hFtlFksrcLaWHGPNa6SmeA","name":"Samantha"}},{"props":{"stars":5},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Food","Coffee & Tea"],"id":"XIXxWu5FJaiDc7tdmePoVg","name":"Dutch Bros Coffee"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2010,2011,2012,2013,2014,2015],"fans":29,"id":"aTi0NVrcPJWbN6jAsJVcAw","name":"Donna"}},{"props":{"stars":4},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Sporting Goods","Fashion","Shopping","Sports Wear"],"id":"c7WYnjVpI7Qr87G6RvFQkA","name":"Campus Corner - Closed"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2013,2015],"fans":8,"id":"Xz1w0h7wDI22IZKi-CnrHA","name":"Karina"}},{"props":{"stars":3},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Bars","Mexican","Nightlife","Lounges","Restaurants"],"id":"ZtJRkaNF6OnSyQJLa5W1cQ","name":"Tapacubo"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2014,2015],"fans":7,"id":"1CGI66n0zKnK_mpMkdYkQQ","name":"Megan"}},{"props":{"stars":5},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Food","Breakfast & Brunch","American (New)","Coffee & Tea","Restaurants"],"id":"EXtCgZoxHNjXrqPCFOgQmQ","name":"D'lish"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2010,2011,2012,2013,2014,2015],"fans":21,"id":"XTFE2ERq7YvaqGUgQYzVNA","name":"Kate"}},{"props":{"stars":1},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Gluten-Free","Asian Fusion","Chinese","Restaurants"],"id":"xcOncADGPr9eki8OU5Ln7g","name":"P.F. Chang's"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2014,2015],"fans":7,"id":"1CGI66n0zKnK_mpMkdYkQQ","name":"Megan"}},{"props":{"stars":4},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Breakfast & Brunch","Mexican","Sandwiches","Restaurants"],"id":"1zDCfNgtfyh-Uw8j3JxhHA","name":"Los Favoritos Tacos Shop"}}],[{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},{"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2014,2015],"fans":22,"id":"Wh5pL_iTBOj3R4W7cJWEkw","name":"Kazi"}},{"props":{"stars":2},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Food","Coffee & Tea"],"id":"lktu5JPDlQUG-7cV7gOzDQ","name":"Cartel Coffee Lab"}}]]})


def path_info(path):
    nodes = [{"props": n.properties, 'labels': [l for l in n.labels]} for n in path.nodes]
    relations = [{"props": n.properties, 'type': n.type} for n in path.rels]
    return merge_lists(nodes, relations)


def merge_lists(list1, list2):
    """
    Merges two lists in an alternate way
    [1, 2, 3] + [4, 5] => [1, 4, 2, 5, 3]
    Borrowed from : http://stackoverflow.com/a/3678938/1585523
    :param list1: a list of objects which the result starts from, occupies in the odd spots
    :param list2: a list of objects, occupies even spots
    :return: alternating combined list of list1 and list2
    """
    result = [None] * (len(list1) + len(list2))
    result[::2] = list1
    result[1::2] = list2
    return result


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
    http.socket_timeout = 9999
    secrets.env()()  # set environment settings
    with MongoClient(os.environ['mongo_connection_url']) as connection:
        db = connection.yelpdata
        graph = Graph(os.environ['neo_db_url'])
        app.run(debug=os.environ['debug_server'] is "True")
