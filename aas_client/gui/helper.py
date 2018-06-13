#!/usr/bin/env python3
# coding: utf-8



# def generate_sentence(conll_forest):
#     sentence_annotated = conll_forest.split("\n\n")[0]
#     sentence_words = [line.split("\t")[1] for line in sentence_annotated.split("\n")]
#     sentence = " ".join(sentence_words)
#     return sentence

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

if __name__ == '__main__':
    # s = generate_sentence(open("../../test/badender_lurch.conll06").read())
    # s = get_subcatframe(open("../../test/badender_lurch.conll06").read())
    # print(s)

    conll = open("../../test/badender_lurch.conll06").read().split('\n\n')[0].split('\n')
    conll = [line.split('\t') for line in conll]
    subcat = [3,'badet','(subj,obj)']
    s = save_result(conll,subcat,'sc.txt')



