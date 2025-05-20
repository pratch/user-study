from itertools import product
import random
import pickle

random.seed(42)

subjects = ['074','104','218','253','264','302','304','306','460']
sentences = ['A','B']
baselines = ['ga','talkg','instag']

combinations = list(product(subjects, sentences, baselines))
random.shuffle(combinations)

# split into 3 sets (9 vids each) or 3 sets (18 vids each)
num_sets = 6
num_pairs_per_set = len(combinations) // num_sets
sets = []
for i in range(num_sets):
    sets.append(combinations[i*num_sets : i*num_sets + num_pairs_per_set])


# for each combination, append to the tuple a random boolean (ours_left)
for i, s in enumerate(sets):
    for j, c in enumerate(s):
        subject, sentence, baseline = c
        random_bool = random.choice([True, False])
        sets[i][j] = (subject, sentence, baseline, random_bool)

# print the sets 
for i, s in enumerate(sets):
    print(f"Set {i+1}:")
    for c in s:
        print(c)
    print()

# print set stats: number uniques (if bad distrib, reseed)
print("Set stats:")
print("===================================")
for i, s in enumerate(sets):
    subjects_set = set()
    sentences_set = set()
    baselines_set = set()
    for c in s:
        subjects_set.add(c[0])
        sentences_set.add(c[1])
        baselines_set.add(c[2])
    print(f"Set {i+1}:")
    print(f"Unique subjects: {len(subjects_set)}")
    print(f"Unique sentences: {len(sentences_set)}")
    print(f"Unique baselines: {len(baselines_set)}")
    print()

# concat vids
for i, s in enumerate(sets):
    for j, c in enumerate(s):
        subject, sentence, baseline, ours_left = c
        if ours_left:
            filename = f"set{i+1}-{j+1}_{subject}{sentence}_ours_vs_{baseline}.mp4"
        else:
            filename = f"set{i+1}-{j+1}_{subject}{sentence}_{baseline}_vs_ours.mp4"
        print(filename)
        
        ga_path = f"ga/{subject}{sentence}_{baseline}.mp4"
        talkg_path = f"talkg/{subject}{sentence}_{baseline}.mp4"
        instag_path = f"instag/{subject}{sentence}_{baseline}.mp4"
        ours_path = f"ours/{subject}{sentence}_ours.mp4"

        # make concat vid

# save the sets 
with open('random_sets.pkl', 'wb') as f:
    pickle.dump(sets, f)
