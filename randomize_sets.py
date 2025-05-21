from itertools import product
import random
import pickle

random.seed(44)

num_responders = 20

subjects = ['074','104','218','253','264','302','304','306','460']
sentences = ['A','B']
baselines = ['ga','talkg','instag']

# combinations = list(product(subjects, sentences, baselines))
# random.shuffle(combinations)

num_responders = 20

# create a list of all combinations, duplicated num_responders times
# half of the responders will have ours_left = True, half will have ours_left = False
combinations = []
for i in range(num_responders // 2):
    for subject, sentence, baseline in product(subjects, sentences, baselines):
        combinations.append((subject, sentence, baseline, True))
        combinations.append((subject, sentence, baseline, False))

# show all combinations
for i, c in enumerate(combinations):
    subject, sentence, baseline, ours_left = c
    print(f"Combination {i+1}: {subject}, {sentence}, {baseline}, {ours_left}")


buckets = []
num_HITs = 120
for i in range(num_HITs):
    # need to keep reseeding until last bucket is unique, otherwise stuck in while loop
    # if i == 119:
    #     print("Last bucket")
    #     print(combinations)
    bucket = []
    for j in range(9):
        # get a random combination
        random_index = random.randint(0, len(combinations) - 1)
        subject, sentence, baseline, ours_left = combinations[random_index]
        # if this (subject, sentence, baseline) is already in the bucket, resample until we find a unique one
        while (subject, sentence, baseline) in [(x[0], x[1], x[2]) for x in bucket]:
            random_index = random.randint(0, len(combinations) - 1)
            subject, sentence, baseline, ours_left = combinations[random_index]
        
        # remove the combination from the list
        combinations.pop(random_index)
        # add the combination to the bucket
        bucket.append((subject, sentence, baseline, ours_left))
    # add the bucket to the list of buckets
    buckets.append(bucket)
    print(f"Bucket {i+1}:")
    for c in bucket:
        subject, sentence, baseline, ours_left = c
        print(f"{subject}, {sentence}, {baseline}, {ours_left}")

# sanity check:  
# check if ('074','A','ga',True) appear exactly 10 times in all buckets
count = 0
for i, b in enumerate(buckets):
    for c in b:
        subject, sentence, baseline, ours_left = c
        if (subject, sentence, baseline, ours_left) == ('074','A','ga',True):
            count += 1
print(f"Count of ('074','A','ga',True): {count}")
count = 0
for i, b in enumerate(buckets):
    for c in b:
        subject, sentence, baseline, ours_left = c
        if (subject, sentence, baseline, ours_left) == ('074','A','ga',False):
            count += 1
print(f"Count of ('074','A','ga',False): {count}")

# generate csv where each row is in form of "pair_218_A_ours_vs_ga" (repeated 9 times, delimited by #) from the buckets
for i, b in enumerate(buckets):
    row = []
    for j, c in enumerate(b):
        subject, sentence, baseline, ours_left = c
        if ours_left:
            filename = f"pair_{subject}_{sentence}_ours_vs_{baseline}"
        else:
            filename = f"pair_{subject}_{sentence}_{baseline}_vs_ours"
        row.append(filename)
    # combine the row into a string
    row = "#".join(row)
    # print(f"Row {i+1}: {row}")
    print(row)

# sanity check: unique combi in all buckets


# create pandas dataframe where each row
        


# # print set stats: number uniques (if bad distrib, reseed)
# print("Set stats:")
# print("===================================")
# for i, s in enumerate(sets):
#     subjects_set = set()
#     sentences_set = set()
#     baselines_set = set()
#     for c in s:
#         subjects_set.add(c[0])
#         sentences_set.add(c[1])
#         baselines_set.add(c[2])
#     print(f"Set {i+1}:")
#     print(f"Unique subjects: {len(subjects_set)}")
#     print(f"Unique sentences: {len(sentences_set)}")
#     print(f"Unique baselines: {len(baselines_set)}")
#     print()

# # concat vids
# for i, s in enumerate(sets):
#     for j, c in enumerate(s):
#         subject, sentence, baseline, ours_left = c
#         if ours_left:
#             filename = f"set{i+1}-{j+1}_{subject}{sentence}_ours_vs_{baseline}.mp4"
#         else:
#             filename = f"set{i+1}-{j+1}_{subject}{sentence}_{baseline}_vs_ours.mp4"
#         print(filename)
        
#         ga_path = f"ga/{subject}{sentence}_{baseline}.mp4"
#         talkg_path = f"talkg/{subject}{sentence}_{baseline}.mp4"
#         instag_path = f"instag/{subject}{sentence}_{baseline}.mp4"
#         ours_path = f"ours/{subject}{sentence}_ours.mp4"

#         # make concat vid

# # save the sets 
# with open('random_sets.pkl', 'wb') as f:
#     pickle.dump(sets, f)
