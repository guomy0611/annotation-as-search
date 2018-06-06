conll=[]
import re, sys
output=open(sys.argv[2], "w")
for line in open(sys.argv[1]):
    if len(line.split("\t"))==14:
        conll.append(line.split("\t"))
    if line.startswith("ParseNBest"):
        #print(re.findall("\[[^\]]+]?", line))
        for result in re.findall("\[[^\]]+]?", line):
            for conll1, value in zip(conll, result.split("@@@")[1].split("]")[0].strip().split()[1:]):
                conll1[9]=value.split(",")[0]
                conll1[11]=value.split(",")[1]
            for line in conll:
                output.write("\t".join(line))
            output.write("\n")