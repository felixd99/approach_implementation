def get_xcomp_ccomp_in_children(action):
    for child_token in action.action_token.children:
       if child_token.dep_ in ['xcomp', 'ccomp']:
            return child_token
    return None