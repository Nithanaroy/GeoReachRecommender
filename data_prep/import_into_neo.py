"""
Creates the social and spatial graph in neo4j

For creating social graph we use user.json
For creating spatial graph we use business.json
For linking both these graphs we use review.json
"""

import json, time, gc
from py2neo import Graph
from py2neo.packages.httpstream import http


def insert(graph, f, insert_query, unwind_key):
    entities = map(lambda x: json.loads(x), f.read().splitlines())
    print '\tCompleted JSON Loads at %s' % (time.time(),)
    x = 0
    while x < len(entities):
        graph.cypher.execute(insert_query, {unwind_key: entities[x:x + 200]})
        x = min(x + 200, len(entities))
        print '\tSaved %d entities at %s' % (x, time.time())

    count = len(entities)
    entities = None  # for GC
    gc.collect(0)
    return count


def main(user, business, review, graph):
    """
    creates the graph as explained in the header of the file
    :param user: user JSON file path as string
    :param business: business JSON file path as string
    :param review: review JSON file path as string
    :param graph: open connection to graph DB
    :return: None
    """
    print 'Started at %s' % (time.time())

    # Create User Nodes
    with open(user, 'r') as u:
        insert_query = """
            UNWIND {users} as u
            CREATE (:Person {id: u['user_id'], name: u['name']});
            """
        num_users = insert(graph, u, insert_query, 'users')
        index_query = """
        CREATE INDEX ON :Person(id)
        """
        graph.cypher.execute(index_query)
        print 'Created %d Users Nodes by %s' % (num_users, time.time())

    # Create Business Nodes
    with open(business, 'r') as b:
        insert_query = """
            UNWIND {biz} as b
            CREATE (:Business {id: b['business_id'], name: b['name']});
            """
        num_biz = insert(graph, b, insert_query, 'biz')
        index_query = """
        CREATE INDEX ON :Business(id)
        """
        graph.cypher.execute(index_query)
        print 'Created %d Business Nodes by %s' % (num_biz, time.time())

    # Create relationships between businesses and users
    with open(review, 'r') as r:
        insert_query = """
        UNWIND {rvw} as r
        CREATE (:Person {id: r['user_id']})-[:REVIEWED {stars: r['stars']}]->(:Business {id: r['business_id']});
        """
        num_rel = insert(graph, r, insert_query, 'rvw')
        print 'Created %d Business-User relations by %s' % (num_rel, time.time())

    # Create relationships among users
    with open(user, 'r') as users:
        # TODO: A better way to create user-user relations. There are thousands of users and looping over each
        # can be very time consuming. Solution: A way to club more user-user relationships
        for u in users:
            u = json.loads(u)
            insert_query = """
            UNWIND {friends} as f
            MERGE (:Person {id: '%s'})-[:FRIEND]-(:Person {id: f});
            """ % (u['user_id'],)
            graph.cypher.execute(insert_query, {"friends": u['friends']})
            print 'Created %d relations for %s at %s' % (len(u['friends']), u['user_id'], time.time())

    print 'Created User-User relations by %s' % (time.time(),)


if __name__ == '__main__':
    http.socket_timeout = 9999

    graph = Graph("http://neo4j:1234@localhost:7474/db/data/")  # TODO: Get from environment
    main('../dataset/user.json', '../dataset/business.json', '../dataset/review_train.json', graph)
