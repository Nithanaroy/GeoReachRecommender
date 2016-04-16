"""
Creates the social and spatial graph in neo4j

For creating social graph we use edges.txt
For linking both these graphs we use checkins-train.txt
"""

import json, time, gc
from py2neo import Graph
from py2neo.packages.httpstream import http
import os, secrets


def insert(graph, entities, insert_query, unwind_key):
    x = 0
    step = 1000
    while x < len(entities):
        graph.cypher.execute(insert_query, {unwind_key: entities[x:x + step]})
        x = min(x + step, len(entities))
        # print '\tSaved %d entities at %s' % (x, time.time())

    count = len(entities)
    entities = None  # for GC
    gc.collect(0)
    return count


def main(edges, checkins, graph):
    # Create user nodes
    nodes = set()
    with open(edges, 'r') as f:
        for l in f:
            u, v = map(lambda x: x.strip(), l.split("\t"))
            nodes.add(u)
            nodes.add(v)
    print 'Person Nodes: ', len(nodes)
    insert_query = """
        UNWIND {users} as user
        CREATE (n:Person {id: user});
        """
    insert(graph, list(nodes), insert_query, 'users')
    graph.cypher.execute('CREATE CONSTRAINT ON (p:Person) ASSERT p.id IS UNIQUE')
    # graph.cypher.execute('CREATE INDEX ON :Person(id)')
    print 'Created user nodes at %s' % (time.time(),)

    # Create business nodes
    businesses = set()
    lines = 0
    with open(checkins, 'r') as f:
        for l in f:
            lines += 1
            businesses.add(l.split('\t')[-1].strip())
    print 'Checkins %s, Businesses %s' % (lines, len(businesses))
    insert_query = """
        UNWIND {businesses} as b
        CREATE (n:Business {id: b});
        """
    insert(graph, list(businesses), insert_query, 'businesses')
    graph.cypher.execute('CREATE CONSTRAINT ON (b:Business) ASSERT b.id IS UNIQUE')
    # graph.cypher.execute('CREATE INDEX ON :Business(id)')
    print 'Created business nodes at %s' % (time.time(),)

    # Create social edges
    social = list()
    with open(edges) as f:
        for l in f:
            social.append(map(lambda x: x.strip(), l.split("\t")))
    insert_query = """
        UNWIND {friends} as r
        MATCH (p:Person {id: r[0]}), (b:Person {id: r[1]})
        CREATE (p)-[:FRIEND]->(b);
        """
    insert(graph, social, insert_query, 'friends')
    print '%d social links found' % (len(social),)
    print 'Created social edges at %s' % (time.time(),)

    # Create checkins edges
    chkins = list()
    with open(checkins) as f:
        for l in f:
            chkins.append(map(lambda x: x.strip(), l.split("\t")))
    # Each line is of the form
    # [user]    [check-in time]         [latitude]	[longitude]	    [location id]
    # 196514    2010-07-24T13:45:06Z    53.3648119  -2.2723465833   145064
    insert_query = """
            UNWIND {checkins} as r
            MATCH (p:Person {id: r[0]}), (b:Business {id: r[4]})
            CREATE (p)-[:REVIEWED {on: r[1], lat: r[2], lng: r[3]}]->(b);
            """
    insert(graph, chkins, insert_query, 'checkins')
    print '%d check-ins found' % (len(chkins),)
    print 'Created check-in edges at %s' % (time.time(),)


if __name__ == '__main__':
    http.socket_timeout = 9999

    secrets.env()()  # set environment settings
    graph = Graph(os.environ['neo_db_url'])
    main('/Volumes/350GB/Projects/GeoReachRecommender/dataset/gowalla/loc-gowalla_edges.txt',
         '/Volumes/350GB/Projects/GeoReachRecommender/dataset/gowalla/checkins-train.txt', graph)
