from os import listdir
import sys
import main


def transform_single(file):
    path = 'Texts/' + file
    # Transform for BPMN Sketch Miner
    sys.stdout = open("ProcessedTexts/SketchMinerInput/" + file, "w")
    main.transform_text(path, False, False, True, False)
    sys.stdout.close()

    # Transform for (numerical) Participant Stories
    sys.stdout = open("ProcessedTexts/ParticipantStories/" + file, "w")
    main.transform_text(path, True, False, False, False)
    sys.stdout.close()

    # Transform for agile User Stories
    sys.stdout = open("ProcessedTexts/AgileStories/" + file, "w")
    main.transform_text(path, False, True, False, False)
    sys.stdout.close()


def get_stats():
    files = listdir("Texts")
    all_actions = 0
    all_actors = 0
    all_objects = 0
    conjunctions = 0
    conditions = 0
    for file in files:
        path = 'Texts/' + file
        analzyed_data = main.transform_text(path, False, False, False, False)
        actions = analzyed_data["actions"]
        all_actions += len(actions)
        all_actors += len(analzyed_data["participant_stories"])
        for action in actions:
            all_objects = all_objects + (1 if action.direct_object else 0)
            all_objects += len(action.indirect_objects)
            conjunctions += len(action.action_token.conjuncts)
            if action.condition:
                conditions = conditions + 1
                all_actions = all_actions + len(action.condition.left_actions)
                all_actions = all_actions + len(action.condition.right_actions)

    print('All actors', all_actors)
    print('All actions', all_actions)
    print('All objects', all_objects)
    print('All conjunctions', conjunctions)
    print('All conditions (Exclusive Gateways)', conditions)

# transform_all()
# transform_single('Model7-1.txt')
# get_stats()

if len(sys.argv) != 2:
    print('Invalid use. Use: python evaluation.py <Path-To-Text>')
else:
    transform_single(sys.argv[1])
