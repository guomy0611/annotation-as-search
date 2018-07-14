import re, sys
from pprint import pprint

def getNBest_single(f):
    """
    convert the parsers output to conll strings for file with A SINGLE SENTENCE
    @:param: parse_out string
    """
    conll = []
    trees =[]
    with open(f,encoding='utf-8') as op:
        parse_out = op.read()
    for line in parse_out.split("\n"):
        if len(line.split("\t"))==14:
            conll.append(line.split("\t"))

        if line.startswith("ParseNBest"):
            #print(re.findall("\[[^\]]+]?", line))
            for result in re.findall("\[[^\]]+]?", line):
                for conll1, value in zip(conll, result.split("@@@")[1].split("]")[0].strip().split()[1:]):
                    conll1[9]=value.split(",")[0]
                    conll1[11]=value.split(",")[1]
                line_ = ["\t".join(line) for line in conll]
                tree = "\n".join(line_)
                trees.append(tree)
            res = "\n\n".join(trees)
    return res

def getNBest_multiple(parese_out):
    """
    convert the parsers output to conll strings for file with MUTIPLE SENTENCES
    @:param: parse_out string
    """
    strings = parese_out.strip().split('\n\n')
    conlls = [getNBest_single(out) for out in strings]
    res = "\n\n\n".join(conlls)
    return res

if __name__ == "__main__":
    print(getNBest_single("output.txt"))

    # s = open("n-best.out1",encoding='utf-8').read()
    # print(getNBest_multiple(s))

