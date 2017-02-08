#!/usr/bin/env python3
# coding: utf-8

def generate_sentence(conll_forest):
    sentence_annotated = conll_forest.split("\n\n")[0]
    sentence_words = [line.split("\t")[1] for line in sentence_annotated.split("\n")]
    sentence = " ".join(sentence_words)
    return sentence

if __name__ == '__main__':
    generate_sentence(open("loadedFiles/2069.conll09").read())
