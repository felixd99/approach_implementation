class Action:
    def __init__(self, actor, action_token, direct_object, indirect_objects, is_optional=False):
        self.actor = actor
        self.action_token = action_token
        self.direct_object = direct_object
        self.indirect_objects = indirect_objects
        self.is_optional = is_optional


class ParticipantStory:
    def __init__(self, actor, actions):
        self.actor = actor
        self.actions = actions


def has_marker_in_children(token):
    for child in token.children:
        if child.dep_ == 'mark' and child.text.lower() in conditional_marks:
            return True
    return False


def get_main_sentence(sent):
    root_token = next(filter(lambda token: token.dep_ == 'ROOT', sent))
    conjuncts = list(filter(lambda token: token.dep_ == 'conj', sent))
    conjuncts = list(map(lambda token: token.text, conjuncts))
    main_sent = []

    for token in sent:
        if token.head == root_token or token.head.text in conjuncts \
            or token.dep_ == 'agent' or token.head.dep_ == 'agent':
            # remove adpositions and adverbs
            if token.pos_ == 'ADP' or token.pos_ == 'ADV':
                continue

            # remove punctuation
            if token.pos_ == 'PUNCT':
                continue

            # remove adverbial clause modifiers for now
            if token.dep_ == 'advcl':
                continue

            # remove empty sentences
            if token.dep_ == 'ROOT' and token.tag_ == '_SP':
                continue

            # qualified for main sentence, add
            main_sent.append(token)

    return main_sent


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


def build_action_name(action):
    action_name = action.action_token.lemma_
    action_name += ' ' + action.direct_object.text \
        if action.direct_object else ''

    for indirect_object in action.indirect_objects:
        preposition = ' '
        # If the object has a preposition (or dative), then we also print this
        if indirect_object.head.dep_ == 'prep' \
            or indirect_object.head.dep_ == 'dative':
            preposition = ' ' + indirect_object.head.text + ' '

        action_name += preposition + indirect_object.text

    return action_name


def print_participant_stories(participant_stories):
    for participant_story in participant_stories:
        print('--- ' + participant_story.actor.text + ' ---')

        for (number, participant_action) in enumerate(
            participant_story.actions):
            print(str(number + 1) + '. ' + participant_action)

        print('')
        print('')


def print_actions_for_sketch_miner(actions, nlp):
    for action in actions:
        # Check if the actor is a valid actor. If not (e.g. 'the process' or
        # 'the workflow', just ignore those actions
        if not is_valid_actor(action.actor, nlp):
            continue

        actor = nlp(action.actor.text)
        action_name = build_action_name(action)
        print(actor.text + ': ' + action_name)


def merge_actors(actions, nlp):
    new_actions = []

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
        action = build_action_name(action)

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