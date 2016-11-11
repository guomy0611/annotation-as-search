'''
Module to work with CONLL parses by allowing to ask and answer questions
about the parse trees, allowing to filter a parse forest until only
one parse tree remains.
'''

from collections import Counter
from subprocess import call


class Tree(object):
    '''
    Class to contain the complete CONLL parse of a sentence and many methods
    to work with it.
    '''

    def __init__(self):
        '''
        Initialize the Tree with an empty list later containing the CONLL-Tuples
        and an empty dictionary later containing the position -> word mapping.
        '''
        self.liste = []
        self.dictio = dict()

    def add(self, sentence):
        '''
        Gets a CONLL-Line, splits it and then converts it into a tuple to
        be added into the list. Also puts a new entry into the dictionary
        containing the position -> word mapping of this line.
        '''
        tuple1 = sentence.strip().split()
        self.liste.append(tuple(tuple1))
        self.dictio[tuple1[0]] = tuple1[1] #fills mapping position -> word

    def contains(self, tup):
        '''
        Checks if a 3-tuple (for example ('Es1', 'ist2', 'SB') ) is contained
        in this tree.
        '''
        return any(tup == (self.dictio[x[0]]+x[0], #Look up the index
                           #in the dictionary, take the word and add the
                           #the index to the word.
                           self.dictio[x[8]]+x[8] if x[8] != "0" else "Root0",
                           #Look up the index of the target word in the
                           #dictionary. take the word and add the index to it.
                           x[10]) for x in self.liste)
                           #Last element of the tuple is the relation type.

    def get(self):
        '''
        Gets a list of 3-tuples from the list containing the CONLL-tuples.
        '''
        #print(self.dictio)
        return [(self.dictio[x[0]]+x[0], #Look up the index
                 #in the dictionary, take the word and add the
                 #the index to the word.
                 self.dictio[x[8]]+x[8] if x[8] != "0" else "Root0",
                 #Look up the index of the target word in the dictionary
                 #take the word and add the index to it.
                 x[10]) for x in self.liste]
                 #Last element of the tuple is the relation type.

    def to_conll(self):
        '''
        Returns a complete CONLL Representation of the parse contained
        in this object.
        '''
        return "\n".join("\t".join(x) for x in self.liste)

    def to_latex(self):
        '''
        Writes latex to a hard-coded latexfile and then generates a
        parse visualization from it.
        '''
        string = """\\documentclass[dvisgm]{minimal}
		\\usepackage{tikz-dependency}
		\\begin{document}
		\\begin{dependency}
		\\begin{deptext}[column sep=0.2cm]\n"""
        string += " \\& ".join(self.dictio[str(key)] for key in \
                   sorted([int(x) for x in self.dictio.keys()]))+"\\\\ \n"
        string += "\\end{deptext}\n"
        for value in self.liste:
            if value[8] == "0":
                string += "\\deproot{"+str(value[0])+"}{root}\n"
            else:
                string += "\\depedge{"+str(value[0])+"}{"+str(value[8])+"}\
                            {"+value[10]+"}\n"
        string += """\\end{dependency}
                   \\end{document}"""
        open("test10.tex", "w").write(string)
        print(string)
        call(["latex", "test10.tex"])
        call(["dvisvgm", "test10.dvi"])


class Forest(object):
    '''
    A Forest object is there to deal with multiple tree objects.
    '''

    def __init__(self):
        '''
        Forest is there to contain many tree objects.
        '''
        self.liste = []

    def add(self, finishedtree):
        '''
        Adds a filled tree into the parse forest.
        '''
        self.liste.append(finishedtree)

    def get_dict(self):
        '''
        Returns a Liste containing 3-tuples and their counts.
        Example: ('Es1', 'ist2', 'SB'): 540
        '''
        print(len(self.liste))
        return Counter([x for tree in self.liste for x \
                           in tree.get()]).most_common()

    def question(self):
        '''
        Chooses the tuple minimizing the equation:
                      lambda x: abs(x[1]-length/2
        This is the tuple having the best chance to halve
        the search space.
        '''
        length = len(self.liste)
        return min(self.get_dict(), key=lambda x: abs(x[1]-length/2))[0]

    def filter(self, asked_tuple, boolean):
        '''
        Filters the treelist based on a tuple and a boolean value.
        if True: keeps all the lists where the tuple is contained.
        if False: keeps all the list where the tuple isnt.
        '''
        self.liste = [tree for tree in self.liste if \
                          (tree.contains(asked_tuple)) == boolean]


tree = Tree()
forest = Forest()
for line in open("conll_for_micha.conll"):
    if line == "\n":
        forest.add(tree)
        tree = Tree()
        continue
    tree.add(line)
while len(forest.liste) != 1:
    question = forest.question()
    print(" ".join(x[1] for x in forest.liste[0].liste))
    answer = input(question)
    if answer == "j":
        forest.filter(question, True)
    else:
        forest.filter(question, False)
    if len(forest.liste) == 1:
        forest.liste[0].to_latex()
        print(forest.liste[0].to_conll())
