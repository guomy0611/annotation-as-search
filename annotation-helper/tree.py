import itertools, re, math
from collections import Counter
from subprocess import call
class Tree:
    def __init__(self):
        self.liste=[]
        self.dictio=dict()
    def add(self, sentence):
        tuple1=sentence.strip().split()
        self.liste.append(tuple(tuple1))
        self.dictio[tuple1[0]]=tuple1[1]
    def contains(self, tup):
        return any(tup==(self.dictio[x[0]]+x[0], self.dictio[x[8]]+x[8] if x[8]!="0" else "Root0", x[10]) for x in self.liste) 
    def get(self):
        #print(self.dictio)
        return [(self.dictio[x[0]]+x[0], self.dictio[x[8]]+x[8] if x[8]!="0" else "Root0", x[10]) for x in self.liste]
    def to_conll(self):
        return "\n".join("\t".join(x) for x in self.liste)
    def to_latex(self):
        string="""\documentclass[dvisgm]{minimal}
		\\usepackage{tikz-dependency}
		\\begin{document}
		\\begin{dependency}
		\\begin{deptext}[column sep=0.2cm]\n"""
        string+=" \& ".join(self.dictio[str(key)] for key in sorted([int(x) for x in self.dictio.keys()]))+"\\\\ \n"
        string+="\end{deptext}\n"
        for value in self.liste:
            if value[8]=="0":
                 string+="\deproot{"+str(value[0])+"}{root}\n"
            else:
                 string+="\depedge{"+str(value[0])+"}{"+str(value[8])+"}{"+value[10]+"}\n"
        string+="""\end{dependency}
                   \end{document}"""
        open("test10.tex", "w").write(string)
        print(string)
        call(["latex", "test10.tex"])
        call(["dvisvgm", "test10.dvi"])
class Forest:
    def __init__(self):
        self.liste=[]
    def add(self, tree):
        self.liste.append(tree)
    def getDict(self): 
        print(len(self.liste))
        return Counter([x for tree in self.liste for x in tree.get()]).most_common()
    def question(self):
        length=len(self.liste)
        return min(self.getDict(), key=lambda x: abs(x[1]-length/2))[0]
    def filter(self,Tuple, bool):
        self.liste=[tree for tree in self.liste if (tree.contains(Tuple))==bool]

class Forest2:
    def __init__(self):
        self.dictio=dict()
tree=Tree()
forest=Forest()
for line in open("conll_for_micha.conll"):
    if line=="\n":
        forest.add(tree)
        tree=Tree()
        continue
    tree.add(line)
while len(forest.liste)!=1:
    question=forest.question()
    print(" ".join(x[1] for x in forest.liste[0].liste))
    answer=input(question)
    if answer=="j":
        forest.filter(question, True)
    else:
        forest.filter(question, False)
    if len(forest.liste)==1:
        forest.liste[0].to_latex()
        print(forest.liste[0].to_conll())