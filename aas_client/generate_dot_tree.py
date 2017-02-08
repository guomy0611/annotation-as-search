#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import graphviz

def generate_dot_tree(tree, format_info, fileformat='svg',
        default_shape="box", fixed_shape="box", treated_shape="box",
        default_color="red", fixed_color="black", treated_color="green",
        default_fontcolor="red", fixed_fontcolor="black",
        treated_fontcolor="green"):
    '''
    Generate a dot graph from a tree object as specified in the AaS
    protocol. Use the format_info to find out what columns of the tree
    are to be drawn. The returned graphviz.Digraph object can be
    rendered and saved using its 'render' method.
    '''

    # Throughout this function, a 'column' is used to index into a node and
    # retrieve the value of a field, while an 'index' is used to index into the
    # tree and retrieve a node.

    id_column = format_info['id']
    form_column = format_info['form']
    label_column = format_info['label']
    head_column = format_info['head']
    relation_column = format_info['relation']

    comment = 'Relation type: {}; label type: {}'.format(
        format_info['relation_type'], format_info['label_type'])
    dot = graphviz.Digraph(comment=comment, format=fileformat)

    # Generate the dot nodes.
    for node_index, node in enumerate(tree['nodes']):
        if label_column in tree['overlays']['treated'][node_index]:
            shape = treated_shape
            color = treated_color
            fontcolor = treated_fontcolor
        elif label_column in tree['overlays']['fixed'][node_index]:
            shape = fixed_shape
            color = fixed_color
            fontcolor = fixed_fontcolor
        else:
            shape = default_shape
            color = default_color
            fontcolor = default_fontcolor

        dot_label = '{} ({})'.format(node[form_column], node[label_column])
        dot.node(node[id_column], label=dot_label, shape=shape,
            color=color, fontcolor=fontcolor)

    # Generate the dot edges.
    # Here we need to make sure to skip the root node because it has no real
    # head.
    for node_index, node in enumerate(tree['nodes']):
        try:
            head_index = int(node[head_column]) - 1
        except ValueError:
            # Either head specifier is invalid or it is the root specifier,
            # which sometimes uses strings like 'ROOT' to indicate its head.
            continue

        try:
            if head_index >= 0:
                # head_index < 0 would probably be the root specifier.
                head_id = tree['nodes'][head_index][id_column]
                if relation_column in tree['overlays']['treated'][node_index]:
                    fontcolor = treated_fontcolor
                elif relation_column in tree['overlays']['fixed'][node_index]:
                    fontcolor = fixed_fontcolor
                else:
                    fontcolor = default_fontcolor

                if head_column in tree['overlays']['treated'][node_index]:
                    color = treated_color
                elif head_column in tree['overlays']['fixed'][node_index]:
                    color = fixed_color
                else:
                    color = default_color

                dot.edge(head_id, node[id_column], label=node[relation_column],
                    color=color, fontcolor=fontcolor)
        except IndexError:
            return 'This tree is not possible!'

    return dot
