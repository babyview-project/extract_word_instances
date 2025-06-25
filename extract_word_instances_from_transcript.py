import pandas as pd
import os
import time


# Set the paths to the diarised transcripts and target word list
# Adjust these paths according to your directory structure
path_to_diarised_transcripts = os.path.join(os.sep, 'ccn2', 'dataset', 'babyview', 'outputs_20250312', 'transcripts', 'diarised')
path_to_target_word_list = os.path.join(os.path.dirname(__file__), 'MCDI_items_with_AoA.csv')
print('file paths set')
# Load the target word list
# Ensure the CSV file has the correct structure with 'uni_lemma' and 'lexical_category' columns
target_word_df = pd.read_csv(path_to_target_word_list)
# Filter the target word list to exclude function words
# Comment out this line if including function words
target_word_df = target_word_df[target_word_df['lexical_category'] != 'function_words']
print('target words selected')
print(target_word_df.head())

# Collect all transcript csv files from the diarised transcripts directory
transcript_files = []
for root, dirs, files in os.walk(path_to_diarised_transcripts):
    for file in files:
        if file.endswith('.csv'):
            transcript_files.append(os.path.join(root, file))
print('transcript directories set')
i = 0
# Loop over each transcript file and read the CSV 
for transcript_file in transcript_files:
    # just for testing, run only 1 transcript_file
    i += 1
    if i > 1:
        break
    print('before reading transcript file:', transcript_file)
    try:
        print(f"Checking file size: {transcript_file}")
        print("Size (MB):", os.path.getsize(transcript_file) / (1024 * 1024))

        start_time = time.time()
        transcript_df = pd.read_csv(transcript_file)
        end_time = time.time()

        print(f"read transcript file: {transcript_file}")
        print(f"Time taken to read: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error reading {transcript_file}: {e}")
        continue
    # Loop over each target word in the target word list
    #for word in target_word_df['uni_lemma']:
        # Use regex to match the word at the start of the token, allowing for suffixes (e.g., plurals, tenses, contractions)
    #    matches = transcript_df[transcript_df['token'].str.contains(rf'^{word}\b', case=False, na=False)]
    #    if not matches.empty:
    #        print(f"{word}:")
    #        for token in matches['token']:
    #            print(token)

