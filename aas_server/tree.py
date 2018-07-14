'''
Module to work with CONLL parses by allowing to ask and answer questions
about the parse trees, allowing to filter a parse forest until only
one parse tree remains.
'''

from collections import Counter
from subprocess import call
import sys
import re

class Tree(object):
    '''
    Class to contain the complete CONLL parse of a sentence and many methods
    to work with it.
    '''

    def __init__(self, format_info=None, id_=0, form=1, head=None, rel=None,
            rel_type=None): #needs to specify the index of fields due to different formats, later in config file
        '''
        Initialize the Tree with an empty list later containing the CONLL-Tuples
        and an empty dictionary later containing the position -> word mapping.
        '''
        self.nodes = []

        if format_info is not None:
            try:
                self.format = format_info['name']
                self.id = format_info['id']
                self.form = format_info['form']
                self.head = format_info['head']
                self.rel = format_info['relation']
                self.rel_type = format_info['relation_type']
            except KeyError as e:
                msg = 'format_info does not specify all necessary information.'
                raise ValueError(msg) from e
        else:
            self.format = 'unspecified'
            self.id = id_
            self.form = form
            self.head = head
            self.rel = rel
            self.rel_type = rel_type

        self.dictio = dict()
        self.tuples = None

    @classmethod
    def from_string(cls, tree_string, **kwargs):
        '''
        Initialize a tree object from an already formatted conll string.
        '''
        tree = cls(**kwargs) #keyword-args
        lines = [
            line.strip()
            for line in tree_string.split('\n')
            # Ignore empty lines and lines starting with '#'
            if not re.match(r'(^\s*$)|(^#.*$)', line)
            ]
        for line in lines:
            tree.add(line)

        return tree

    def add(self, conll_line):
        '''
        Gets a CONLL-Line, splits it and then converts it into a tuple to
        be added into the list. Also puts a new entry into the dictionary
        containing the position -> word mapping of this line.
        '''
        conll_parts = conll_line.strip().split('\t')
        self.nodes.append(tuple(conll_parts))

        # fills mapping position -> word
        self.dictio[conll_parts[self.id]] = conll_parts[self.form] #position -> word mapping

    def contains(self, tup):
        '''
        Checks if a 3-tuple (for example ('Es-1', 'ist-2', 'SB') ) is contained
        in this tree.
        '''
        return tup in self.get()

    def contains_subcat(self, subcat):
        """
        checks if the tree contains the subcat structure
        :param subcat: list of subcat:[('Lurch-6', 'badet-3', 'SB'),('in-7', 'badet-3', 'MO')]
        :return:boolean
        """

        for dep in subcat:
            if tuple(dep) not in self.get():
                return False
        return True


    def overlap(self, other):
        '''
        Returns the number of triples contained in the tree and a given
        other tree.
        '''
        return len(set(self.get())&set(other.get()))

    def get(self):
        '''
        Gets a list of 3-tuples from the list containing the CONLL-tuples.
        '''


        """
             ( dependent-id, head-id, relation)
        e.g. ('toller-4', 'Satz-5', 'NK')

        """
        if self.tuples is not None: return self.tuples
        #TODO: try except KeyError return ErrorMessage: indicated format and file format doesn't match
        self.tuples={(self.dictio[x[0]]+"-"+x[0], #Look up the index
                 #in the dictionary, take the word and add the
                 #the index to the word.
                 self.dictio[x[self.head]]+"-"+x[self.head] if x[self.head] != "0" else "Root-0",
                 #Look up the index of the target word in the dictionary
                 #take the word and add the index to it.
                 x[self.rel]) for x in self.nodes}
                 #Last element of the tuple is the relation type.
        return self.tuples

    def to_conll(self):
        '''
        Returns a complete CONLL Representation of the parse contained
        in this object.
        '''
        return "\n".join("\t".join(x) for x in self.nodes)

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
        for value in self.nodes:
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

    def as_dict(self):
        return {'nodes': self.nodes}

class Forest(object):
    '''
    A Forest object is there to deal with multiple tree objects.
    '''

    def __init__(self):
        '''
        Forest is there to contain many tree objects.
        '''
        self.trees = []
        self.originaltrees = None
        self.answeredtuples=[]

    @classmethod
    def from_string(cls, forest_string, **tree_kwargs):
        '''
        Initialize a forest object from a long string formatted like a conll
        file.
        '''
        forest = cls()
        for tree_string in forest_string.strip().split('\n\n'):
            forest.add(Tree.from_string(tree_string, **tree_kwargs))
        return forest

    def solved(self):
        '''
        True if the forest clears and only one tree remains.
        '''
        return len(self.trees) == 1

    def add(self, finishedtree):
        '''
        Adds a filled tree into the parse forest.
        '''
        self.trees.append(finishedtree)

    def get_dict(self):
        '''
        Returns a list containing 3-tuples and their counts.
        Example: ('Es1', 'ist2', 'SB'): 540
        '''
        return Counter([x for tree in self.trees for x \
                           in tree.get()]).most_common()

    def get_best_tuple(self):
        '''
        Chooses the tuple minimizing the equation:
                      lambda x: abs(x[1]-length/2
        This is the tuple having the best chance to halve
        the search space.
        '''
        length = len(self.trees)
        return min(self.get_dict(), key=lambda x: abs(x[1]-length/2))[0]

    def question(self):
        '''
        Find the best question to ask and return it.
        '''
        dependent, head, relation = self.get_best_tuple()
        return {
            'head': head,
            'dependent': dependent,
            'relation': relation,
            'relation_type': self.trees[0].rel_type
            }

    def filter(self, asked_dict, boolean):
        '''
        Wrapper around the _filter method that adds asked_tuples to a
        list of answered tuples. This list can then be used by the undo
        method.
        '''
        asked_tuple=(asked_dict['dependent'], asked_dict['head'], asked_dict['relation'])
        if self.originaltrees is None:
            self.originaltrees = self.trees[:]
        self.answeredtuples.append((asked_tuple, boolean))
        self._filter(asked_tuple, boolean)

    def _filter(self, asked_tuple, boolean):
        '''
        Filters the treelist based on a tuple and a boolean value.
        if True: keeps all the lists where the tuple is contained.
        if False: keeps all the list where the tuple isnt.
        '''
        self.trees = [tree for tree in self.trees
            if tree.contains(asked_tuple) == boolean]

    def undo(self, n=1):
        '''
        Restore the state the forest was in n questions earlier.
        '''
        self.answeredtuples = self.answeredtuples[:-n]
        self.trees = (
            self.originaltrees[:]
            if self.originaltrees is not None
            else self.trees[:]
            )
        for question, answer in self.answeredtuples:
            self._filter(question, answer)

    def get_fixed_edges(self):
        '''
        Function that returns the tuples that are fixed (additional
        answers wont change them).
        '''
        length = len(self.trees)
        return [x for x,y in self.get_dict() if y==length]

    def get_fixed_nodes(self):
        '''
        Find the nodes that exist in every tree and return them as a list.
        This method assumes that all trees in the forest have the same number
        of nodes.
        '''
        fixed_nodes = []
        if len(self.trees) == 0:
            return fixed_nodes

        for node_index in range(len(self.trees[0].nodes)):
            for tree in self.trees:
                if tree.nodes[node_index] != self.trees[0].nodes[node_index]:
                    break
            else:
                fixed_nodes.append(self.trees[0].nodes[node_index])

        return fixed_nodes

    def get_fixed_fields(self):
        '''
        Find the fields that exist in every tree and return them as a list.
        This method assumes that all trees in the forest have the same number
        of nodes.
        '''

        #compare each field of each node of each tree the first tree in the forest, (because the first one is the best??)

        fixed_fields = []
        if len(self.trees) == 0:
            return fixed_fields

        for node_index in range(len(self.trees[0].nodes)):
            liste=[]
            for field_index in range(len(self.trees[0].nodes[node_index])):
                for tree in self.trees:
                    if tree.nodes[node_index][field_index] != self.trees[0].nodes[node_index][field_index]:
                        break
                else:
                    liste.append(field_index)
            fixed_fields.append(liste)
        return fixed_fields


    def get_treated_fields(self):
        indices=[int(x) for x in self.get_treated_nodes()]
        liste=[]
        for node in self.trees[0].nodes:
            if int(node[0]) in indices:
                liste.append([self.trees[0].head, self.trees[0].rel])
            else:
                liste.append([])
        return liste

    def get_treated_nodes(self):
        return [x[0].split("-")[-1] for x,y in self.answeredtuples if y]

    def get_best_tree(self):
        '''
        Find the best guess for the correct tree. As it stands, we
        assume that the first tree in the list is the best guess.
        '''
        if len(self.trees) > 0:
            return self.trees[0]
        else:
            raise ValueError('This forest contains no trees.')

    def subcat_trees(self, subcat):
        """

        :return: list of trees containing the suggsted subcat frame
        """
        li = []
        for tree in self.trees:
            if tree.contains_subcat(subcat):
                li.append(tree)
        return li

if __name__ == "__main__":
    from pprint import pprint
    # tree = Tree(head = 9, rel = 11, rel_type = "deprel")
    # forest = Forest()
    # for line in open("output.txt"): #sys.argv[1]):
    #     if line == "\n":
    #         forest.add(tree)
    #         tree = Tree(head = 9, rel = 11, rel_type = "deprel")
    #         continue
    #     tree.add(line)
    #     print(tree.nodes)

    forest = Forest.from_string(open('../test/badender_lurch.conll09').read(), head=8, rel=10, rel_type="deprel")
    for tree in forest.trees:
        pprint(tree.dictio)
        pprint(tree.get())
        print(forest.subcat_trees([('Lurch-6', 'badet-3', 'SB'),('in-7', 'badet-3', 'MO')]))


    # while len(forest.trees) != 1:
    #
    #     question = forest.question()
    #     print(" ".join(x[1] for x in forest.trees[0].nodes))
    #     answer = input(question)
    #     if answer == "j":
    #         forest.filter(question, True)
    #     else:
    #         forest.filter(question, False)
    #     if len(forest.trees) == 1:
    #         #forest.trees[0].to_latex()
    #         print(forest.trees[0].to_conll())


    # tree = Tree()
    # tree = Tree.from_string(open('../test/single_tree.conll09').read(),head = 9, rel = 11, rel_type = "deprel")
    #
    # #pprint(tree.nodes)
    # pprint(tree.dictio)
    # pprint(tree.get())



