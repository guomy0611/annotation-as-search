from . import visualize
import argparse

def visualize_solution(solution):
    solution_strings = ['\t'.join(part) for part in solution]
    solution_string = '\n'.join(solution_strings)
    parser = argparse.ArgumentParser(description='Trains the parser in a multi-core setting.')
    g=parser.add_argument_group("Input/Output")
    g.add_argument('input', nargs='?', help='Parser output file name, or nothing for reading on stdin')
    g.add_argument('--max_sent', type=int, default=0, help='How many trees to show? 0 for all. (default %(default)d)')
    args = parser.parse_args([solution_string])
    html_tree = visualize.visualize(args)
    # for now
    with open("visualized_tree.html", "w") as f:
        f.write(html_tree)
