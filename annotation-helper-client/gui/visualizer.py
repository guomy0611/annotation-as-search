#!/usr/bin/env python3
# -*- coding: utf-8

import argparse

try:
    import visualize
except ImportError:
    from . import visualize



def visualize_solution(solution, complete=0):
    ''' visualise tree in html '''
    solution_strings = ['\t'.join(part) for part in solution]
    solution_string = '\n'.join(solution_strings)
    parser = argparse.ArgumentParser()
    g=parser.add_argument_group("Input/Output")
    g.add_argument(
            'input',
            nargs='?',
            help='input: string or nothing for reading on stdin'
            )
    g.add_argument(
            '--max_sent',
            type=int,
            default=0,
            help='How many trees to show? )0 for all. (default %(default)d)'
            )
    args = parser.parse_args([solution_string])
    html_tree = visualize.visualize(args, complete)
    # save in html-file for now
    with open("templates/visualized_tree.html", "w") as f:
        f.write(html_tree)


def main():
    with open('../../test/badender_lurch.conll09', 'r') as f:
        content = [token.strip().split('\t') for token in f.readlines()]
        visualize_solution(content, 1)


if __name__ == '__main__':
    main()
