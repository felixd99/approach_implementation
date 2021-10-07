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
def clean_phrase(phrase):
    cleaned_phrase = ''
    for token in phrase:
        if token.pos_ == 'PRON' or not token.is_stop:
            cleaned_phrase += token.text
    return cleaned_phrase.replace('-', '').replace('.', '').replace('\'', '')


def find_participant_story_for_actor(actor, stories):
    for story in stories:
        if compare_actors(story.actor, actor):
            return story
    return None


def build_action_name(action):
    action_name = action.action_token.lemma_ + ' '

    for object in action.objects:
        if object._.indirect_object:
            action_name += ' to '
        action_name += object.text

    return action_name


actors_to_ignore = [
    'process',
    'workflow',
    'procedure'
]