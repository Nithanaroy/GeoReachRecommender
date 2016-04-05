"""
Split a file into train and test data
"""

import random, pickle


def save(f, lines):
    """
    saves the list with one item per line in the given file
    :param f: output file path as a string
    :param lines: list of entities to save
    :return: None
    """
    with open(f, 'w') as f:
        for l in lines[:-1]:
            print>> f, l
        f.write(lines[-1])


def main(f, train_percent, train, test):
    """
    splits the file into train and test by given train percent
    :param f: input file path as string
    :param train_percent: percentage of data as train as float, e.g. 0.8. The remaining will be test
    :param train: file path of train file as string
    :param test: file path of test file as string
    :return: None
    """
    with open(f, 'r') as f:
        data = f.read().splitlines()
    random.shuffle(data)
    train_lines = int(len(data) * train_percent)
    save(train, data[:train_lines])
    save(test, data[train_lines:])


if __name__ == '__main__':
    main('../dataset/review.json', 0.8, '../dataset/review_train.json', '../dataset/review_test.json')
