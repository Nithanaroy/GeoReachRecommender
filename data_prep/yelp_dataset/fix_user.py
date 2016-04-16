"""
{
    'type': 'user',
    'user_id': (encrypted user id),
    'name': (first name),
    'review_count': (review count),
    'average_stars': (floating point average, like 4.31),
    'votes': {(vote type): (count)},
    'friends': [(friend user_ids)],
    'elite': [(years_elite)],
    'yelping_since': (date, formatted like '2012-03'),
    'compliments': {
        (compliment_type): (num_compliments_of_this_type),
        ...
    },
    'fans': (num_fans),
}
"""
import json


def main(f, o):
    with open(f, 'r') as fp:
        res = []
        out = open(o, 'w')
        for u in fp.read().splitlines():
            user = json.loads(u)
            d = {}
            d['_id'] = user['user_id']
            d['name'] = user['name']
            d['review_count'] = user['review_count']
            d['friends_count'] = len(user['friends'])
            res.append(json.dumps(d))
        out.write('[' + ',\n'.join(res) + ']')
        out.close()


if __name__ == '__main__':
    main('../dataset/user.json', '../dataset/out.json')
