import main
from os import listdir
import sys

def transform_all():
    files = listdir("Texts")
    for file in files:
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

transform_all()