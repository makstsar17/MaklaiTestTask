from flask import Blueprint, request, jsonify
from nltk.tree import ParentedTree
import itertools

paraphrase_bp = Blueprint('paraphrase', __name__)


# Return first node in tree that have NP or NN label
def find_next_noun(tree):
    for node in tree:
        if node.label() in ('NP', 'NN'):
            return node.parent_index()

    return None


# Connect pairs of indices in NP groups
def connect_np_ind(noun_pairs):
    result = []
    prev_pair = noun_pairs.pop(0)
    while len(noun_pairs) != 0:
        next_pair = noun_pairs.pop(0)
        if prev_pair[-1] == next_pair[0]:
            prev_pair = prev_pair + next_pair[1:]
            continue
        result.append(prev_pair)
        prev_pair = next_pair
    result.append(prev_pair)
    return result


# Return all possible indices of nouns that can be paraphrased
def get_groups_for_paraphrase(tree):
    result = []
    for subtree in tree.subtrees():
        if subtree.label() != 'NP':
            continue
        if len(subtree) < 2:
            continue

        np_ind_pair = []
        prev_node_ind = find_next_noun(subtree)
        if prev_node_ind is None:
            continue
        while True:
            next_node_ind = find_next_noun(subtree[prev_node_ind + 1:])
            if next_node_ind is None:
                break

            check_flag = True
            for node in subtree[prev_node_ind + 1:next_node_ind]:
                if node.label() not in [',', 'CC']:
                    check_flag = False

            if check_flag:
                np_ind_pair.append((prev_node_ind, next_node_ind))

            prev_node_ind = next_node_ind

        if len(np_ind_pair) != 0:
            for np in connect_np_ind(np_ind_pair):
                np_groups_for_paraphrase = []
                for noun_ind in np:
                    np_groups_for_paraphrase.append(subtree[noun_ind].treeposition())
                result.append(tuple(np_groups_for_paraphrase))
    return result


# Return new paraphrased tree, created by permuting nouns using indices for paraphrase
def swap_np(tree, group_for_paraphrase):
    result_tree = tree.copy(deep=True)
    for np_group in group_for_paraphrase:
        sorted_group_ind = [pos for pos in result_tree.treepositions() if pos in np_group]

        for i, pos in enumerate(sorted_group_ind):
            if pos == np_group[i]:
                continue
            parent = result_tree[pos].parent()
            add_subtree = tree[np_group[i]].copy(deep=True)
            del result_tree[pos]
            parent.insert(pos[-1], add_subtree)

    return result_tree


@paraphrase_bp.route('/paraphrase', methods=["GET"])
def paraphrase_NP():
    tree_str = request.args.get('tree', type=str)
    if tree_str is None:
        return jsonify(error='Tree is required'), 400

    limit = request.args.get('limit', 20, type=int)

    # Create Parse tree
    try:
        ptree = ParentedTree.fromstring(tree_str)
        # print(ptree.pretty_print())
    except ValueError:
        return jsonify(error='Invalid tree description'), 400

    # Get all possible permutations of nouns in tree
    permutations_of_groups = []
    for np_group in get_groups_for_paraphrase(ptree):
        permutations = list(itertools.permutations(np_group))
        permutations_of_groups.append(tuple(permutations))
    paraphrases_ind = list(itertools.product(*permutations_of_groups))
    paraphrases_ind.pop(0)

    if len(paraphrases_ind) < limit:
        limit = len(paraphrases_ind)

    # Create new trees by permuting nouns
    paraphrases = [{"tree": str(swap_np(ptree, paraphrases_ind[i]))} for i in range(limit)]

    return jsonify(result='Success', paraphrases=paraphrases), 200
