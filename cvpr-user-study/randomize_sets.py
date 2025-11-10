from itertools import product
import random
import pickle
import pandas as pd

random.seed(45) # need to keep reseeding until last bucket is unique, otherwise stuck in while loop


subjects = ['074','104','218','253','264','302','304','306','460']
sentences = ['A','B']
baselines = ['ga','gaga','4dgs','hr','ar','lam']

# combinations = list(product(subjects, sentences, baselines))
# random.shuffle(combinations)

# num_responders = 20
num_responders = 10

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
    # print(f"Combination {i+1}: {subject}, {sentence}, {baseline}, {ours_left}")


buckets = []
num_HITs = 120 # num_HITS = total combinations / 9 combinations per HIT = 9*2*6*10 / 9 = 240
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
# check if ('074','A','ga',True) appear exactly num_responders // 2 times in all buckets
# count = 0
# for i, b in enumerate(buckets):
#     for c in b:
#         subject, sentence, baseline, ours_left = c
#         if (subject, sentence, baseline, ours_left) == ('074','A','ga',True):
#             count += 1
# print(f"Count of ('074','A','ga',True): {count}")
# count = 0
# for i, b in enumerate(buckets):
#     for c in b:
#         subject, sentence, baseline, ours_left = c
#         if (subject, sentence, baseline, ours_left) == ('074','A','ga',False):
#             count += 1
# print(f"Count of ('074','A','ga',False): {count}")

# sanity check: do all buckets have unique combinations?
# for i, b in enumerate(buckets):
#     unique_combinations = set()
#     for c in b:
#         subject, sentence, baseline, ours_left = c
#         unique_combinations.add((subject, sentence, baseline))
#     if len(unique_combinations) != len(b):
#         print(f"Bucket {i+1} has duplicate combinations")
#     else:
#         print(f"Bucket {i+1} has unique combinations")

# sanity check: count number of apperances of each combination (should be 20, 10 for each ours_left)
# combination_counts = {}
# for i, b in enumerate(buckets):
#     for c in b:
#         subject, sentence, baseline, ours_left = c
#         if (subject, sentence, baseline) not in combination_counts:
#             combination_counts[(subject, sentence, baseline)] = 0
#         combination_counts[(subject, sentence, baseline)] += 1
# # print the counts
# for k, v in combination_counts.items():
#     subject, sentence, baseline = k
#     print(f"Combination {subject}, {sentence}, {baseline}: {v} times")

# generate csv where each row is in form of "pair_218_A_ours_vs_ga" (repeated 9 times, delimited by #) from the buckets

all_bucket_strings = []
for i, b in enumerate(buckets):
    row_pairs = []
    for j, c in enumerate(b):
        subject, sentence, baseline, ours_left = c
        if ours_left:
            filename = f"pair_{subject}_{sentence}_ours_vs_{baseline}"
        else:
            filename = f"pair_{subject}_{sentence}_{baseline}_vs_ours"
        row_pairs.append(filename)

    # combine the row into a string
    string_pairs = "#".join(row_pairs)
    all_bucket_strings.append(string_pairs)


# create pandas dataframe where each row is a bucket
df = pd.DataFrame(all_bucket_strings, columns=['q_strings'])
df.to_csv('final_csv/turk_hits.csv', index=False)

# split into first 10% and last 90% of the buckets & save as csv
df_10 = df.iloc[:12]
df_90 = df.iloc[12:]
df_10.to_csv('final_csv/turk_hits_10.csv', index=False)
df_90.to_csv('final_csv/turk_hits_90.csv', index=False)

# split into 3 groups, first 10%, middle 40%, last 50% of the buckets & save as csv
df_10 = df.iloc[:12]
df_40 = df.iloc[12:60]
df_50 = df.iloc[60:]
df_10.to_csv('final_csv/turk3split_hits_10.csv', index=False)
df_40.to_csv('final_csv/turk3split_hits_40.csv', index=False)
df_50.to_csv('final_csv/turk3split_hits_50.csv', index=False)