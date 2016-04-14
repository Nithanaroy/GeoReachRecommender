import json


def main(inp, out):
    with open(inp) as f:
        with open(out, 'w') as o:
            o.write('[\n')  # required for mongoimport as a json array
            for l in f:
                p = json.loads(l)
                p['_id'] = p.pop('review_id')
                p.pop('text')  # remove the actual review as we are not doing any NLP
                p.pop('type')  # remove type as it always has the value 'review'
                o.write(json.dumps(p) + ',\n')
            o.write(']')
            # Remember to manually remove the trailing comma after the last document before import


if __name__ == '__main__':
    main('./dataset/review_test.json', './dataset/review_test_for_mongo.json')
