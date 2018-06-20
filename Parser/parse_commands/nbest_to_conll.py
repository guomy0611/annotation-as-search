conll=[]
import re, sys
# output=open(sys.argv[2], "w")
# for line in open(sys.argv[1]):


# def writeNBest(file_in,file_out):
#     with open(file_out,'w') as op:
#         for sent in open(file_in).split("\n\n"):
#             writeNBest()




def getNBest_single(parse_out):
    """
    interpret the parsers output to conll strings FOR A SINGLE SENTENCE
    """
    conll = []
    for line in parse_out.split("\n"):
        if len(line.split("\t"))==14:
            conll.append(line.split("\t"))

        if line.startswith("ParseNBest"):
            #print(re.findall("\[[^\]]+]?", line))
            for result in re.findall("\[[^\]]+]?", line):
                for conll1, value in zip(conll, result.split("@@@")[1].split("]")[0].strip().split()[1:]):
                    conll1[9]=value.split(",")[0]
                    conll1[11]=value.split(",")[1]
                    conll = ["\t".join(line) for line in conll]
                    conll = "\n".join(conll)
    return conll

if __name__ == "__main__":
    s = open("la").read()
    print(getNBest_single(s))