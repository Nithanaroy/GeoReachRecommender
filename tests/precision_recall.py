import json, csv
from pymongo import MongoClient

regions = [[36.2259962378, -115.096893311, 36.0418815246, -115.372924805],
           [33.5814470822, -111.78314209, 33.3913194759, -112.059173584],
           [33.5328095927, -111.848373413, 33.3425751669, -112.124404907],
           [33.4778449201, -111.774215698, 33.2874899444, -112.050247192],
           [33.6197655606, -111.870346069, 33.4297222075, -112.146377563],
           [36.1838876271, -115.087966919, 35.9996740536, -115.363998413],
           [33.5934591835, -111.814041138, 33.4033579797, -112.090072632],
           [33.6003224905, -111.834640503, 33.410236376, -112.110671997]]

with MongoClient() as connection:
    db = connection.yelpdata
    business_in_region = {}
    for r in regions:
        query = {"loc": {"$geoWithin": {"$box": [[r[3], r[2]], [r[1], r[0]]]}}}
        business_in_region[','.join(map(str, r))] = [b['_id'] for b in
                                                     db.business.find(query, {'_id': 1})]

    with open('./ranked_paths_out.json') as f:
        with open('./accuracy.csv', 'w') as csvfile:
            o = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            o.writerow(
                ['user', 'region', '#biz_testdata (T)', '#actual_biz (A)', 'P@10', 'P@20', 'P@30', 'P@40', 'P@50',
                 'P@All', 'R@T', 'R@A'])
            # Each line in f has user, ranked paths, region and importance values for each path
            for l in f:
                p = json.loads(l)
                # for this user and region how many businesses are in test data
                ebiz = set([b['business_id'] for b in db.reviews_test.find(
                    {"user_id": p['user'], "business_id": {"$in": business_in_region[','.join(p['region']).strip()]}},
                    {"business_id": 1, "_id": 0})])
                # only considering user and not businesses
                # ebiz = set([b['business_id'] for b in
                #             db.reviews_test.find({"user_id": p['user']}, {"business_id": 1, "_id": 0})])
                # now check accuracy
                abiz = [path[-1]['props']['id'] for path in p['paths']]

                r1, r2 = None, None
                if len(ebiz) > 0:
                    r1 = sum([1 if b in ebiz else 0 for b in abiz[0:len(ebiz)]]) / float(len(ebiz))
                    r2 = sum([1 if b in ebiz else 0 for b in abiz]) / float(len(ebiz))

                precisions = [''] * 6  # for top 10, 20, 30, 40, 50 and all
                if len(ebiz) > 0:
                    for i, n in enumerate(range(10, min(51, len(abiz)), 10)):
                        precisions[i] = sum([1 if b in ebiz else 0 for b in abiz[0:n]]) / float(n)
                    k = [1 if b in ebiz else 0 for b in abiz]
                    precisions[-1] = sum([1 if b in ebiz else 0 for b in abiz]) / float(len(abiz))

                o.writerow([p['user'], json.dumps(p['region']).replace(',', ';'), len(ebiz), len(abiz)] +
                           precisions + [r1, r2])
