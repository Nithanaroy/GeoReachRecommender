"""
The yelp dataset *business.json file has lat and long as a separate keys, however MongoDB wants
them to be under the same key to create a 2D index

The data generated here can be imported as:
mongoimport --db yelpdata --collection business --jsonArray --file out.json
"""

import json


def main(f, o):
    """
    fix JSON input 'f' and save it as a JSON Array to output file 'o'
    :param f: input file path as a string
    :param o: output file path as a string
    :return: None
    """
    with open(f) as f:
        l = f.read().splitlines()
        res = []
        out = open(o, 'w')
        for line in l:
            j = json.loads(line)
            d = {}
            d['_id'] = j['business_id']
            d['name'] = j['name']
            d['loc'] = [j['longitude'], j['latitude']]
            d['stars'] = j['stars']
            res.append(json.dumps(d))
        out.write('[' + ',\n'.join(res) + ']')
        out.close()


if __name__ == '__main__':
    main('./yelp_academic_dataset_business.json', './out.json')
