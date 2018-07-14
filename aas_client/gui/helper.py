#!/usr/bin/env python3
# coding: utf-8
from aas_client.generate_dot_tree import generate_dot_tree
import json
#format_info = {"name": "conll09_gold", "id": 0,"form": 1,"label": 4,"label_type": "pos","head": 8,"relation": 10,"relation_type": "deprel"}

def generate_sentence(conll_forest):
    sentence_annotated = conll_forest.split("\n\n")[0]
    sentence_words = [line.split("\t")[1] for line in sentence_annotated.split("\n")]
    sentence = " ".join(sentence_words)
    return sentence

def get_tokens(conll_forest):
    sentence_annotated = conll_forest.split("\n\n")[0]
    tokens = [(line.split("\t")[1],line.split("\t")[0]) for line in sentence_annotated.split("\n")]
    return tokens

# def generate_sentence(conll_forests):
#     sentences = []
#     conll_forests = conll_forests.split("\n\n\n")
#     for conll_forest in conll_forests:
#         first_tree = conll_forest.split("\n\n")[0]
#         sentence_words = [line.split("\t")[1] for line in first_tree.split("\n")]
#         sentence = " ".join(sentence_words)
#         sentences.append(sentence)
#     return sentences

def generate_sentence(conll_forest):
    """
    get raw sentence string from conll forest string
    @:param conll_forest: conll file string containing forest of one or multiple forests
    @:return: the raw sentence string
    """
    first_tree = conll_forest.split("\n\n")[0]
    sentence_words = [line.split("\t")[1] for line in first_tree.split("\n")]
    sentence = " ".join(sentence_words)
    return sentence

def get_subcatframe(conll_forest):
    """
    get the subcatframe from forest string
    assume that the subcatframe is always saved in the last column of the conll string
    :return: (verb, subcatframe): tuple
    """
    subcatframe = None
    first_tree = conll_forest.split("\n\n")[0]
    for line in first_tree.split("\n"):
        if line.split("\t")[-1] != "_":
            subcatframe = [line.split("\t")[0], line.split("\t")[2], line.split("\t")[-1]] #[index,verb,subcat]
            return subcatframe
    if subcatframe == None:
        raise ValueError("This sentence doesn't contain information about subcatframe.")

def save_result(nodes, subcat,file):
    """
    write the correct dependency tree and subcat frame back to conll file
    @:param:conll nodes of the final solution
    @:param:subcat [index,verb,subcat]
    @:param:file to write
    """

    #assign subcat
    print(subcat)
    nodes[int(subcat[0])-1][-1] = subcat[2]
    #reasseble tree
    lines = ["\t".join(line) for line in nodes]
    new_tree = "\n".join(lines)

    with open(file,'a') as op:
        op.write(new_tree)
        op.write("\n\n")

# taken from server.py
def update_config(config, new_pairs):
    """
    Update the config dict (conll-formats) with the key-value-pairs in new_data.

    Args:
        config: The current configuration dict.
        new_pairs: A dict or an argparse.Namespace containing the
            key-value-pairs that are to be inserted. In the case of a
            namespace, only names not starting with an underscore are added to
            the config. If a vale is None, the pair is ignored.
    """
    if isinstance(new_pairs, dict):
        config.update({k: v for k, v in new_pairs.items() if v is not None})
    elif isinstance(new_pairs, argparse.Namespace):
        for key in dir(new_pairs):
            if not key.startswith('_'):
                value = getattr(new_pairs, key)
                if value is not None:
                    config[key] = value
    else:
        msg = '{} is neither a dict nor an argparse.Namespace.'
        raise TypeError(msg.format(new_pairs))

# taken from server.py
def read_configfile(configfile):
    """
    Read a json-formatted configuration file and return the resulting dict.
    """
    try:
        return json.load(open(configfile))
    except FileNotFoundError as e:
        return dict()

def get_conll_formats(formats, format_aliases):
    """ Save information about conll-formats in a dictionary.

    Store conll-information in a dictionary. Each entry has the form
    conll_formats[format] = all information  in config regarding this format.
    Each format-alias is given the same information as the original as value.
    If this information is not given in the config, the name of the original
    is taken as value.

    Args:
        formats: The formats-dict specified in the config.
        format_aliases: The format_aliases dict specified in the config.
    Returns a dict containing all conll-formats and the specification needed to
    start the AaS-server.
    """
    conll_formats = formats
    for alias in format_aliases.keys():
        if format_aliases[alias] in conll_formats.keys():
            conll_formats[alias] = conll_formats[format_aliases[alias]]
        else:
            conll_formats[alias] = format_aliases[alias]
    return conll_formats

def handle_solution(data):
    """ Return conll representation of annotated tree """
    solution = data['tree']['nodes']
    words = ['\t'.join(word) for word in solution]
    tree = '\n'.join(words)
    return tree


def handle_question(question):
    visualise(question)


def visualise(data, format_info):
    """ Visualize given tree

    Vizualize the given tree: Color fixed edges green, uncertain edges red, all
    others black

    Arguments:
        data: message sent by the AnnotationHelper-server
    Returns a svg-image of the best tree (first tree in the list of trees) or
    a svg-image of the last given tree (solution case)
    """
    try:
        if data['type'] == 'question':
            return generate_dot_tree(data['best_tree'], format_info).pipe().decode('utf-8')
        visual = generate_dot_tree(data['tree'], format_info)
        if type(visual) == str:
            return visual
        return visual.pipe().decode('utf-8')
    # catch eventual parser not found error thrown by the AaS-server
    except KeyError:
        return 'Parser was not found.'

if __name__ == '__main__':
    # s = generate_sentence(open("../../test/badender_lurch.conll06").read())
    # s = get_subcatframe(open("../../test/badender_lurch.conll06").read())
    # print(s)

    conll = open("../../test/badender_lurch.conll06").read().split('\n\n')[0].split('\n')
    conll = [line.split('\t') for line in conll]
    subcat = [3,'badet','(subj,obj)']
    s = save_result(conll,subcat,'sc.txt')



