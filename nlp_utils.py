def get_xcomp_ccomp_in_children(action):
    for child_token in action.action_token.children:
       if child_token.dep_ in ['xcomp', 'ccomp']:
            return child_token
    return None


def has_mulitple_direct_objects(action):
    has_direct_object = False
    filtered_actions = list(filter(lambda child: child.dep_ == 'dobj', list(action.children)))
    return len(filtered_actions) > 1


def get_connecting_conjunction(doc, main_token, conjunction_token):
    other_conjunctions = []
    for token in doc[main_token.i:conjunction_token.i]:
        if token.dep_ == 'cc':
            # Found the main conjunction
            if token in main_token.children:
                return token
            elif token in main_token.subtree:
                other_conjunctions.append(token)

    return other_conjunctions[0]
