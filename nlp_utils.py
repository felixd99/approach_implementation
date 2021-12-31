def get_xcomp_ccomp_in_children(action):
    for child_token in action.verb.children:
       if child_token.dep_ in ['xcomp', 'ccomp']:
            return child_token
    return None


def has_mulitple_direct_objects(action):
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

    return other_conjunctions[0] if len(other_conjunctions) > 0 else None


def get_subclause_from_token_on(token, doc):
    head_token = token.head
    punct_token = None
    # Get the next punctation (most likely indicating that the subclause ennded)
    for right_action in token.sent:
        if right_action.pos_ == 'PUNCT':
            punct_token = right_action
            break

    if punct_token is None:
        return 'Unknown action'

    subclause_phrase = ''

    for i, subclause_token in enumerate(doc[token.i + 1:punct_token.i]):
        # Only add the word if it's in the subtree (== subclause)
        if subclause_token in head_token.subtree:
            if i != 0:
                subclause_phrase += ' '
            subclause_phrase += subclause_token.text

    return subclause_phrase