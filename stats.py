from os import listdir
import re

# Needs to be installed with 'pip install syllables'
import syllables

files = listdir("Texts")

# Exclude the files (as they are excluded in the evaluation)
exclude_files = [
    'Hospital.txt',
    'Hotel.txt',
    'HotelService.txt',
    'Model2-1.txt',
    'Model2-2.txt',
    'Model4-1.txt',
    'Model5-3.txt',
    'Model6-3.txt',
    'Model6-4.txt',
    'Model8-1.txt',
    'Model9-1.txt',
    'Model9-6.txt',
    'Self-service-restaurant.txt',
    'Underwriter.txt'
]

# Setup metrics
measured_texts = 0
all_words = []
all_sentences_count = 0
all_words_count = 0
all_syllables_count = 0
min_words_per_sent = 9999
max_words_per_sent = 0
hard_words_count = 0
long_words_count = 0

# Analyzing
for file in files:
    # Skip excluded files
    if file in exclude_files:
        continue

    measured_texts += 1

    # Read files
    path = 'Texts/' + file
    text = open(path).read()
    # Replace empty new lines
    text = re.sub('\n\n', '\n', text)
    # Replace new lines with space
    text = re.sub('.\n', '. ', text)
    # Replace occurrences of abbreviations
    text = re.sub('i\.e\.', 'ie', text)
    text = re.sub('etc\.', 'etc', text)
    text = re.sub('e\.g\.', 'eg', text)
    text = re.sub('approx\.', 'approx', text)
    text = re.sub('cf\.', 'cf', text)

    # text.replace('\n', ' ')

    sents = text.split('.')
    all_sentences_count += len(sents)

    for sent in sents:
        words = sent.split()
        all_words_count += len(words)
        all_words.extend(sent.split())
        # Only consider sentences that are longer than 2 words (as otherwise
        # they are noise sentence)
        min_words_per_sent = len(words) \
            if min_words_per_sent > len(words) > 2 else min_words_per_sent

        max_words_per_sent = len(words) \
            if len(words) > max_words_per_sent else max_words_per_sent

        for word in words:
            syllables_count = syllables.estimate(word)
            all_syllables_count += syllables_count
            # Hard words (more than 2 syllables)
            if syllables_count >= 3 and not '-' in word:
                hard_words_count += 1
            # Long words (more than 6 characters)
            if len(word) > 6:
                long_words_count += 1

# Average words per sentence
aws = all_words_count / all_sentences_count

# Calculate Flesch-Reading-Ease (https://en.wikipedia.org/wiki/Readability#The_Flesch_formulas)
fre = 206.835 - 1.015 * aws - 84.6*(all_syllables_count / all_words_count)

# Calculate Gunning fog index (https://en.wikipedia.org/wiki/Readability#The_Gunning_fog_formula)
gfi = 0.4 * (aws + 100 * (hard_words_count / all_words_count))

print('All texts:', measured_texts)
print('All sentences:', all_sentences_count)
print('All words:', all_words_count)
print('Average words per sentence:', round(aws, 2))
print('Unique words:', len(set(all_words)))
print('Hard words:', hard_words_count, '(' + str(round((hard_words_count / all_words_count) * 100, 2)) + '%)')
print('Long words:', long_words_count, '(' + str(round((long_words_count / all_words_count) * 100, 2)) + '%)')
print('All syllables:', all_syllables_count)
print('Syllables per word:', round(all_syllables_count / all_words_count, 2))
print('Flesch reading ease score:', round(fre, 2))
print('Gunning fog index:', round(gfi, 2))
print('Min words per sentence:', min_words_per_sent)
print('Max words per sentence:', max_words_per_sent)
