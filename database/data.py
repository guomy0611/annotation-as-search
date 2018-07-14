from sqlalchemy.orm import sessionmaker
from model import engine, Sentence
from nbest_to_conll import getNBest_single
import subprocess
import tempfile
import os

Session = sessionmaker(bind=engine)

#work flow here: get subcat first, and update the tweet file, since there may be tweets without subcats, those should be deleted
#and there will also be repeated tweets due to multiple verbs
#and the subcat extraction project runs on python 2..due to the sentence splitter twitter library, so the work flow can't be intergrated :(


def get_conll_forest(f_sh,f_sent):
    """
    get mate parsing forest from a sent file to a forest file
    @:param:f_sh:shell script for mate parser, f_sent:updated tweet file
    """
    f_forest = f_sent.replace('_sent','_forest')
    subprocess.call("{} {} {}".format(f_sh,f_sent, f_forest), shell=True)

def get_conll_forest_s(f_sh,f_in,f_out):
    """
    get mate parsing forest from a sent file to a forest file
    @:param:f_sh:shell script for mate parser, f_single_sent:tmp file containing only one sent(because mate parser only takes file as input)
    """

    forest = subprocess.call("{} {} {}".format(f_sh,f_in,f_out), shell=True)
    return forest


def insert(f_sent,f_subcat,f_sh):
    """
    get subcat and conll forest of for tweets(referenced by index)
    insert them into the database
    @:param: 3 files
    """
    session = Session()
    with open(f_sent, encoding='utf8') as f1, open(f_subcat, encoding='utf8') as f2:
        for sent, subcat in zip(f1,f2):
            op = open('../Parser/parse_commands/input.txt','w', encoding = 'utf8')
            op.write(sent)
            op.close()
            get_conll_forest_s(f_sh, "input.txt", "output2.txt")
            forest = getNBest_single("../Parser/parse_commands/output2.txt")
            print(forest)
            sent = Sentence(sentence=sent, conll_forest=forest, subcat_suggested=subcat)
            session.add(sent)
    session.commit()

if __name__ == '__main__':
    f_sh = '/Users/muyan/PycharmProjects/aas_subcat/Parser/parse_commands/Parser_'
    f = '/Users/muyan/PycharmProjects/aas_subcat/Parser/parse_commands/single.txt'
    f_sent = './files/test_10_sent'
    f_subcat = './files/test_10_subcat'
    f_forest = './files/test_10_forest'

    #get_conll_forest_s(f_sh,f,"output1.txt")


    # forest = getNBest_single("/Users/muyan/PycharmProjects/aas_subcat/Parser/parse_commands/output.txt")
    # print(forest)
    insert(f_sent,f_subcat,f_sh)