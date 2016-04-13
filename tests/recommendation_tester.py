import urllib2 as u
import json, time, math, os
from py2neo.packages.httpstream import http
from py2neo import Graph

global paths_values  # values for each path
paths_values = {}


def save_all_paths(inp, out):
    """
    Saves all paths from a user to region to a file
    Assumes that the /recommend service returns all paths and not just the top K
    a region is a latitude and longitude combination for northeast and southwest points
    E.g: 33.4198365601,-111.82434082,33.4089467182,-111.843910217
    :param inp: input CSV file path as string containing all user and region pairs
    :param out: output file path where to save all paths
    :return: None
    """
    with open(inp) as f:
        with open(out, 'w') as o:
            begin = time.time()
            for tuple in f:
                print 'At %s after %s, started %s ' % (time.time(), time.time() - begin, tuple)
                user, nelat, nelong, swlat, swlong = [None] * 5
                try:
                    user, nelat, nelong, swlat, swlong = tuple.split(',')[:5]
                    start = time.time()
                    url = 'http://127.0.0.1:5000/{0}/recommend?nelat={1}&nelong={2}&swlat={3}&swlong={4}'
                    c = u.urlopen(url.format(user, nelat, nelong, swlat, swlong)).read()
                    took = time.time() - start
                    paths = json.loads(c)['paths']
                    region = [nelat, nelong, swlat, swlong]
                    o.write(json.dumps(
                        {'user': user, 'region': region, 'paths': paths, 'start': start, 'took': took}) + '\n')
                except Exception as e:
                    o.write(json.dumps(
                        {'error': str(e.reason), 'user': user, 'region': [nelat, nelong, swlat, swlong]}) + '\n')


def save_ranked_paths(inp, out):
    """
    Takes the randomly ordered paths from save_all_paths() and ranks them based on a ranking function
    :param inp: input file path as string containing the output of save_all_paths()
    :param out: output file path where to save the ranked paths
    :return: None
    """
    with open(inp) as f:
        with open(out, 'w') as o:
            for i, line in enumerate(f):
                print 'Line number: {} ({})'.format(i, time.time())
                paths = json.loads(line)['paths']
                for p in paths:
                    paths_values[key_for_path(p)] = value_of_path(p)
                o.write(json.dumps(sorted(paths, rank, reverse=True)) + '\n')


def key_for_path(p):
    """
    Representation of the path, ID for a path
    :param p: a JSON path dictionary
    :return: a unique string for the path
    """
    # key for a path is made of starting user id and ending business id in the path
    return '%s_%s' % (p[0]['props']['id'], p[-1]['props']['id'])


def value_of_path(p):
    """
    Computes the value or the importance of a path
    Three things are considered:
    1) Rating of the end (recommended) business
    2) Popularity of the people in the path
    3) Social closeness of the people in the path with the user
    :param p: a JSON path dictionary
    :return: a float value indicating the value of the path, [0, 3]
    """
    business_rating = p[-2]['props']['stars']  # get number of stars given by the reviewer
    popularity_of_path = get_popularity(p)
    friendship_strength = get_social_strength(p)
    return business_rating / 5 + popularity_of_path + friendship_strength


def get_social_strength(p):
    """
    Computes the social (normalized) strength of a path
    For each friend, the number of businesses commonly reviewed is computed
    Then a linear weighted average of these counts is returned
    The farther the node from starting node, lesser the weight it gets
    :param p: a JSON path dictionary
    :return: normalized weighted indicating the social strength of the path [0, 1]
    """
    me = p[0]['props']['id']
    friends = friends_in_path(p)
    query = """UNWIND {friends} as f
    MATCH (p:Person {id: {me}})-[:REVIEWED]-(b)-[:REVIEWED]-(q:Person {id: f['props']['id']})
    RETURN q['id'], COUNT(b);"""
    graph = Graph('http://neo4j:1234@localhost:7474/db/data/')
    common_reviews = {}
    # initialize common reviews count to 0 for each friend
    for friend in friends:
        common_reviews[friend['props']['id']] = 0
    total_common_reviews = 0
    for fid, count in graph.cypher.execute(query, {'me': me, 'friends': friends}):
        total_common_reviews += count
        common_reviews[fid] = count
    weighted_sum = 0
    for index, friend in enumerate(friends):
        # line equation => social_strength(y) = # friends(m) - distance_in_the_path_from_me(x)
        weighted_sum += common_reviews[friend['props']['id']] * (len(friends) - index)
    d = total_common_reviews * len(friends)
    return weighted_sum / (d if d > 0 else 1)


def get_popularity(p):
    """
    For each :Person node in the path except the starting node, get linear weighted average
    of number of fans in the path
    A path is of the form:
    [{"labels":["Person"],"props":{"elite":[2015],"fans":6,"id":"2AGGIi5EiVLM1XhBXaaAVw","name":"Art"}},
    {"props":{},"type":"FRIEND"},{"labels":["Person"],"props":{"elite":[2010,2011,2012,2013,2014],"fans":404,"id":"4ozupHULqGyO42s3zNUzOQ","name":"Lindsey"}},
    {"props":{"stars":5},"type":"REVIEWED"},{"labels":["Business"],"props":{"categories":["Food","Bakeries","Coffee & Tea","Salad","Restaurants"],"id":"A-M-ebgWSjHTXi9S6tvchw","name":"Arcadia Farms Cafe"}}]
    :param p: Path
    :return: normalized weighted sum, [0, 1]
    """
    weighted_sum = 0
    total_fans = 0
    # path includes both relations and nodes. exclude the 1st (viz. user of interest) and the last node (viz. business)
    friends = friends_in_path(p)
    for index, friend in enumerate(friends):
        fans = friend['props']['fans'] if 'props' in friend and 'fans' in friend['props'] else 0
        total_fans += fans
        # line equation => weight_of_friend(y) = # friends(m) - distance_in_the_path_from_me(x)
        weighted_sum += fans * (len(friends) - index)
    d = total_fans * len(friends)
    return weighted_sum / (d if d > 0 else 1)


def friends_in_path(p):
    """
    Finds all friend nodes in the path
    :param p: a path as JSON dictionary
    :return: list of friend JSON dictionaries
    """
    friends = []
    friends_count = int(math.ceil(len(p) / 2.0) - 2)
    for index in range(2, (friends_count * 2) + 1, 2):
        friends.append(p[index])
    return friends


def rank(p1, p2):
    """
    Ranks two paths
    :param p1: First path object
    :param p2: Second path object
    :return: if p1 is ranked more than p2, then 1; if equal, then 0; else -1
    """
    if paths_values[key_for_path(p1)] > paths_values[key_for_path(p2)]:
        return 1
    elif paths_values[key_for_path(p1)] == paths_values[key_for_path(p2)]:
        return 0
    else:
        return -1


if __name__ == '__main__':
    http.socket_timeout = 9999
    inp1 = './user_region_inp.csv'
    out1 = './all_paths_out.json'
    out2 = './ranked_paths_out.json'
    save_all_paths(inp1, out1)
    save_ranked_paths(out1, out2)
