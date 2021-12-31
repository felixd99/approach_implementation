import nlp_utils


class Action:
    def __init__(self, actor, verb, direct_object, indirect_objects, event_text=None, condition=None, is_a_copy=False):
        self.actor = actor
        self.verb = verb
        self.direct_object = direct_object
        self.indirect_objects = indirect_objects
        self.event_text = event_text
        self.condition = condition
        self.is_a_copy = is_a_copy


class ConditionAction:
    def __init__(self, condition_phrase, left_actions=[], right_actions=[]):
        self.condition_phrase = condition_phrase
        self.left_actions = left_actions
        self.right_actions = right_actions


class ParticipantStory:
    def __init__(self, actor, actions):
        self.actor = actor
        self.actions = actions


def get_marker_in_children(token):
    for child in token.subtree:
        if child.dep_ == 'mark' and child.text.lower() in conditional_marks:
            return child
    return None


def get_else_marker_in_children(token):
    for child in token.children:
        if (child.dep_ == 'mark' or child.dep_ == 'advmod') \
          and child.text.lower() in conditional_else_marks:
            return child
    return None


def get_event_marker_in_children(token):
    for child in token.children:
        if child.text.lower() in event_tokens \
          and token.sent[0].text.lower() in event_tokens:
            return child
    return None


def merge_previous_condition(actions, current_action, actions_to_remove):
    current_action_index = actions.index(current_action)
    previous_condition = None
    conditions_to_merge = []
    # Get all previous actions and see if there is a condition linked
    while not previous_condition and current_action_index >= 1:
        current_action_index = current_action_index - 1
        previous_action = actions[current_action_index]
        if previous_action.condition:
            previous_condition = previous_action
        elif previous_action not in actions_to_remove:
            # If there is no condition linked but it's between the 'Else'
            # condition, we merge it with the previous condition
            conditions_to_merge.append(previous_action)

    if previous_condition and len(conditions_to_merge) > 0:
        # Merge the conditions
        for condition_to_merge in conditions_to_merge:
            actions_to_remove.append(condition_to_merge)
            previous_condition.condition.left_actions.append(condition_to_merge)

    return previous_condition


def get_action(action_token, doc, previous_action, event_text=None):
    actor = None
    direct_object = None
    indirect_objects = []

    for token in action_token.subtree:
        head_token = token.head

        # Only get the main actor of the sentence
        if token.dep_ == 'nsubj' and head_token == action_token:
            actor = resolve_coreferences(token, doc)
            # If token is still a pronoun, choose previous actor
            if actor.pos_ == 'PRON' and previous_action:
                actor = previous_action.actor

        # Get objects directly related to the main action
        if token.dep_ == 'dobj' and head_token == action_token:
            direct_object = resolve_coreferences(token, doc)

        # Get objects that are affected indirectly
        if token.dep_ == 'pobj' \
            and head_token.head == action_token:
            # mark token as indirect object
            indirect_objects.append(token)

        # Check if sentence is passive and set passive object as actor
        if (head_token.dep_ == 'agent' or head_token.text == 'by') \
            and head_token.head == action_token and action_token.tag_ == 'VBN':
            actor = token

        # Add passive subject to objects
        if token.dep_ == 'nsubjpass' and head_token == action_token:
            direct_object = resolve_coreferences(token, doc)

    return Action(actor, action_token, direct_object, indirect_objects, event_text)


def resolve_coreferences(token, doc):
    # See if the direct object is a co-reference
    try:
        coref_object = doc._.coref_chains.resolve(token)
    except IndexError:
        return token

    if coref_object and len(coref_object) > 0:
        return coref_object[0]

    # No co-reference found, return normal token
    return token


def get_previous_action(action, all_actions):
    if action not in all_actions:
        # Action is not in array
        return None

    action_index = all_actions.index(action)

    if action_index == 0:
        # Action has no previous action
        return None

    return all_actions[action_index - 1]

# get similarity
def similarity(subjects):
    for subject1Index in range(len(subjects)):
        subject1 = subjects[subject1Index]

        for subject2Index in range(subject1Index + 1, len(subjects)):
            subject2 = subjects[subject2Index]
            similarity = subject1.similarity(subject2)

            print(
                'Similarity for ' + subject1.text + ' and ' + subject2.text + ': ' + str(
                    similarity))


def compare_actors(actor1, actor2):
    actor1_cleaned = clean_phrase(actor1).upper()
    actor2_cleaned = clean_phrase(actor2).upper()

    return actor1_cleaned == actor2_cleaned \
        or actor1_cleaned in actor2_cleaned or actor2_cleaned in actor1_cleaned


def is_valid_actor(actor, nlp):
    for actor_to_ignore in actors_to_ignore:
        actor0 = actor[0]
        if compare_actors(nlp(actor_to_ignore), actor) \
          and not actor[0].pos_ == 'PRON':
            return False
    return True


# Remove stop words (except for pronouns), punctuation and hyphens
# OR: If the token is uppercase, it might also be a valid actor (acronym that
# is recognized as a stop word (e.g. 'The GO'))
def clean_phrase(phrase):
    cleaned_phrase = ''
    for token in phrase:
        if token.pos_ == 'PRON' or not token.is_stop or token.text.isupper():
            cleaned_phrase += token.text
    return cleaned_phrase.replace('-', '').replace('.', '').replace('\'', '')


def find_participant_story_for_actor(actor, stories):
    for story in stories:
        if story.actor.text == actor.text:
            return story
    return None

def merge_actors(actions, nlp):
    actors = []
    previous_action = None
    condition_actions = actions.copy()

    for action in condition_actions:
        if action.condition:
            condition_actions.extend(action.condition.left_actions)
            condition_actions.extend(action.condition.right_actions)

        actor = nlp(action.actor.text)

        # Check if there is already an actor in the list for this action
        actors_filtered = list(
            filter(lambda list_actor: compare_actors(nlp(list_actor.text), actor),
                   actors))

        if len(actors_filtered) > 0:
            action.actor = actors_filtered[0]
        else:
            if action.actor and is_valid_actor(actor, nlp):
                actors.append(actor)
            elif previous_action and previous_action.actor:
                action.actor = previous_action.actor
            else:
                action.actor = actor
        previous_action = action


def is_a_start_or_end_event(action, nlp, doc):
    actor = nlp(action.actor.text)
    # See if we have a sentence like "The process starts when xxx"
    if not is_valid_actor(actor, nlp) or 'process' in action.actor.text.lower():
        for child in action.verb.children:
            if child.dep_ == 'advmod':
                event_text = nlp_utils.get_subclause_from_token_on(child, doc)
                return event_text


actors_to_ignore = [
    # 'process',
    'workflow',
    'procedure',
    'file',
    'activity',
]

# taken from http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.228.2293&rep=rep1&type=pdf
conditional_marks = [
    'if',
    'in case of',
    'in the case of',
    'in case',
    'for the case'
]

conditional_else_marks = [
    'else',
    'otherwise'
]

event_tokens = [
    'once',
    'when',
    'upon',
    'on',
    'whenever',
    'after'
]

process_begin_or_end_tokens = [
    'begin',
    'start',
    'initiate',
    'stop',
    'end',
    'terminate'
]