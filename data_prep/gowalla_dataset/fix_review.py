import json


def main(inp, out):
    with open(inp) as f:
        with open(out, 'w') as o:
            checkins = []
            for l in f:
                user_id, date, lat, lng, business_id = l.strip().split('\t')
                checkins.append(json.dumps({'user_id': user_id, 'business_id': business_id, 
                    'loc': [float(lng), float(lat)]}))
            o.write('[%s]' % (','.join(checkins)))


if __name__ == '__main__':
    main('../../dataset/gowalla/test.txt', 'review_test_for_mongo.json')
