"""
The gowalla dataset *checkins.txt file has lat and long separated, however MongoDB wants
them to be under the same key to create a 2D index

The data generated here can be imported as:
mongoimport --db gowalladata --collection business --jsonArray --file out.json
"""

import json


def main(f, o):
    """
    fix TXT input 'f' and save it as a JSON Array to output file 'o'
    Each line is of the form:
    [user]	[check-in time]		    [latitude]	    [longitude]	    [location id]
    196514  2010-07-24T13:45:06Z    53.3648119      -2.2723465833   145064
    :param f: input file path as a string
    :param o: output file path as a string
    :return: None
    """
    businesses = set()
    with open(f, 'r') as f:
        res = []
        for l in f:
            d = dict()
            user, checkin, lat, lng, bid = l.strip().split('\t')
            if bid not in businesses:
                businesses.add(bid)
                d['_id'] = bid
                d['loc'] = [float(lng), float(lat)]
                res.append(json.dumps(d))
        with open(o, 'w') as out:
            out.write('[' + ',\n'.join(res) + ']')


if __name__ == '__main__':
    main('./dataset/gowalla/checkins-train.txt', './dataset/gowalla/checkins-train-out.txt')
