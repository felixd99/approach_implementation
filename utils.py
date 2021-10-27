class Action:
    def __init__(self, actor, action_token, direct_object, indirect_objects, is_event=False, condition=None):
        self.actor = actor
        self.action_token = action_token
        self.direct_object = direct_object
        self.indirect_objects = indirect_objects
        self.is_event = is_event
        self.condition = condition

class ConditionAction:
    def __init__(self, condition_tokens=[]):
        self.condition_tokens = condition_tokens

class ParticipantStory:
    def __init__(self, actor, actions):
        self.actor = actor
        self.actions = actions


def has_marker_in_children(token):
    for child in token.children:
        if child.dep_ == 'mark' and child.text.lower() in conditional_marks:
            return True
    return False


def get_action(action_token, doc, previous_action, is_subclause=False):
    actor = None
    direct_object = None
    indirect_objects = []

    for token in action_token.subtree:
        head_token = token.head

        # Only get the main actor of the sentence
        if token.dep_ == 'nsubj' and head_token == action_token:
            actor = resolve_coreferences(token, doc)
            coref_actor = doc._.coref_chains.resolve(token)
            if coref_actor and len(coref_actor) > 0:
                actor = coref_actor[0]
            else:
                actor = token

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

    return Action(actor, action_token, direct_object, indirect_objects, is_subclause)


def resolve_coreferences(token, doc):
    # See if the direct object is a co-reference
    coref_object = doc._.coref_chains.resolve(token)
    if coref_object and len(coref_object) > 0:
        return coref_object[0]
    # No co-reference found, return normal token
    return token


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


def get_direct_ancestors(head_token, doc_):
    ancestors = []
    for token in doc_:
        if token.head == head_token:
            ancestors.append(token)
    return ancestors


def compare_actors(actor1, actor2):
    actor1_cleaned = clean_phrase(actor1).upper()
    actor2_cleaned = clean_phrase(actor2).upper()

    return actor1_cleaned == actor2_cleaned \
        or actor1_cleaned in actor2_cleaned or actor2_cleaned in actor1_cleaned


def is_valid_actor(actor, nlp):
    for actor_to_ignore in actors_to_ignore:
        if compare_actors(nlp(actor_to_ignore), actor):
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


def build_action_name(action, for_sketch_miner):
    action_name = ''
    # Check if the action is an event and passive
    if action.is_event and action.action_token.tag_ == 'VBN':
        if for_sketch_miner:
            action_name = build_sketch_miner_event_name(action)
        else:
            aux_pass = get_aux_pass(action.action_token)
            action_name = 'Event: ' + action.direct_object.text
            action_name += (' ' + aux_pass.text) if aux_pass else ''
            action_name += ' ' + action.action_token.text
    else:
        # Print special events in sketch miner
        if for_sketch_miner and action.action_token.lemma_ in special_event_indicators:
            action_name = build_sketch_miner_event_name(action)
        else:
            action_name = action.action_token.lemma_
            action_name += ' ' + action.direct_object.text \
                if action.direct_object else ''

    # Append indirect objects
    for indirect_object in action.indirect_objects:
        # Skip objects that don't provide any value e.g. "after that"
        if indirect_object.text.lower() in objects_to_ignore:
            continue

        preposition = ' '
        # If the object has a preposition (or dative), then we also print this
        if indirect_object.head.dep_ == 'prep' \
            or indirect_object.head.dep_ == 'dative':
            preposition = ' ' + indirect_object.head.text + ' '

        action_name += preposition + indirect_object.text

    if (action.is_event or action.action_token.lemma_ in special_event_indicators) \
        and for_sketch_miner:
        action_name += ')'

    return action_name


def build_sketch_miner_event_name(action):
    action_name = ''
    if action.action_token.lemma_ in special_event_indicators:
        action_name = '(' + action.action_token.lemma_
        action_name += ' ' + action.direct_object.text
    else:
        action_name = '(' + action.direct_object.text
        action_name += ' ' + action.action_token.text

    return action_name


def get_aux_pass(action):
    for token in action.children:
        if token.dep_ == 'auxpass':
            return token
    return None


def is_conditional_mark(token):
    pass


def print_participant_stories(participant_stories):
    for participant_story in participant_stories:
        print('--- ' + participant_story.actor.text + ' ---')

        for (number, participant_action) in enumerate(
            participant_story.actions):
            print(str(number + 1) + '. ' + participant_action)

        print('')
        print('')


def print_actions_for_sketch_miner(actions, nlp, number_of_actors):
    for action in actions:
        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not is_valid_actor(action.actor, nlp):
            continue

        actor = nlp(action.actor.text)
        action_name = build_action_name(action, True)
        # only print actor if we have valid ones
        print_actor = number_of_actors > 1 or \
                      (number_of_actors == 1 and not actor.text == 'Unknown actor')
        if print_actor:
            print(actor.text + ': ' + action_name)
        else:
            print(action_name)


def merge_actors(actions, nlp):
    actors = []

    for action in actions:
        actor = nlp(action.actor.text)

        # Check if there is already an actor in the list for this action
        actors_filtered = list(
            filter(lambda list_actor: compare_actors(nlp(list_actor.text), actor),
                   actors))

        if len(actors_filtered) > 0:
            actor = actors_filtered[0]
        else:
            actors.append(actor)

        action.actor = actor


def generate_participant_stores(actions, nlp):
    participant_stories = []
    for action in actions:
        actor = nlp(action.actor.text)

        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not is_valid_actor(actor, nlp):
            continue

        participant_story = find_participant_story_for_actor(actor, participant_stories)
        action = build_action_name(action, False)

        # Check if there is already a participant story for the actor, if so
        # just add the action to it
        if participant_story:
            participant_story.actions.append(action)
        else:
            participant_story = ParticipantStory(actor, [action])
            participant_stories.append(participant_story)

    return participant_stories

actors_to_ignore = [
    'process',
    'workflow',
    'procedure',
    'file'
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

special_event_indicators = [
    'receive',
    'send'
]

objects_to_ignore = [
    'that',
    'this',
    'addition'
]