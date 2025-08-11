import os
import re
import pandas as pd
import numpy as np

# Paths
# Note: output directory is set to be one directory up
# from the current script's location
output_dir = "../word_instances/"
os.makedirs(output_dir, exist_ok=True)

# Paths to transcript, and videos on ccn2 
path_to_diarised_transcripts = os.path.join(os.sep, 'ccn2', 'dataset', 'babyview', 'outputs_20250312', 'transcripts', 'diarised')
video_base_dir = os.path.join(os.sep, "ccn2", "dataset", "babyview", "unzip_2025", "babyview_main_storage")
# Target word list is saved inside the folder of this script
path_to_target_word_list = os.path.join(os.path.dirname(__file__), 'MCDI_items_with_AoA.csv')


# Helper function to find the video corresponding to a given transcript
# This is used to ensure we only process transcripts that have a corresponding video
def find_video_for_stem(video_base_dir, stem):
    def first_mp4_in_dir(d):
        try:
            if os.path.isdir(d):
                mp4s = [x for x in os.listdir(d) if x.lower().endswith(".mp4")]
                if mp4s:
                    return os.path.join(d, mp4s[0])
        except Exception:
            pass
        return None

    p = first_mp4_in_dir(os.path.join(video_base_dir, stem))
    if p: return p
    if stem.endswith("_word_instances"):
        p = first_mp4_in_dir(os.path.join(video_base_dir, stem[:-15]))
        if p: return p
    try:
        for d in os.listdir(video_base_dir):
            full = os.path.join(video_base_dir, d)
            if os.path.isdir(full) and (d.startswith(stem) or stem.startswith(d)):
                p = first_mp4_in_dir(full)
                if p: return p
    except Exception:
        pass
    return None

# Load target words
# Here we are omitting function words - change if you want to include them
target_word_df = pd.read_csv(path_to_target_word_list)
target_words = (
    target_word_df.loc[target_word_df['lexical_category'] != 'function_words', 'uni_lemma']
    .dropna().astype(str).unique()
)

# Gather transcript files
transcript_files = []
for root, dirs, files in os.walk(path_to_diarised_transcripts):
    for file in files:
        if file.endswith('.csv'):
            transcript_files.append(os.path.join(root, file))

print(f"Found {len(transcript_files)} transcript files.")
if not transcript_files:
    raise SystemExit("No transcript CSVs found.")

transcript_files = transcript_files

# Allowed inflectional suffixes (kept conservative to avoid false positives)
# Examples hit: read->reads/reading/reader/readers; play->plays/played/playing/player
SUFFIX_GROUP = r"(?:s|es|ed|ing|er|ers|est)"

for transcript_file in transcript_files:
    transcript_filename = os.path.basename(transcript_file)
    stem = os.path.splitext(transcript_filename)[0]

    # Only process if a matching video exists
    video_path = find_video_for_stem(video_base_dir, stem)
    if not video_path:
        print(f"❌ No video found for '{stem}'. Skipping.")
        continue

    print(f"📝 Processing transcript with video: {transcript_filename}")

    try:
        df = pd.read_csv(transcript_file)
    except Exception as e:
        print(f"⚠️ Error reading {transcript_filename}: {e}")
        continue

    if 'token' not in df.columns:
        print(f"⚠️ Transcript {transcript_filename} has no 'token' column; skipping.")
        continue

    out_df = df.copy()
    token_series = out_df['token'].astype(str)

    # Pre-create all target word columns at once (no fragmentation)
    zeros = pd.DataFrame(0, index=out_df.index, columns=target_words, dtype=np.uint8)

    # Pattern logic:
    #   ^<word>  — must start at beginning of token (prevents "unhappy" for "happy")
    #   then one of:
    #       - <SUFFIX_GROUP> (like "ing", "ed", "s", "er", "ers", "est"), optionally followed by possessive 's
    #       - direct possessive 's
    #       - OR a non-letter/right boundary immediately after the base word (bare word with punctuation/boundary)
    #
    # This matches: "read", "reading", "reads", "reader", "readers", and with punctuation/possessive:
    #   "reading,", "read's", "readers’"
    # It will NOT match "ready" or "readme" (not in the suffix list), nor "unhappy" for "happy".
    for w in target_words:
        base = re.escape(w)
        patt = rf"^{base}(?:(?:{SUFFIX_GROUP})(?:[’']s)?|[’']s|(?=[^A-Za-z]|$))"
        mask = token_series.str.contains(patt, case=False, na=False, regex=True)
        if mask.any():
            zeros.loc[mask, w] = 1

    # Attach all word columns at once
    out_df = pd.concat([out_df, zeros], axis=1, copy=False)

    # Quick summary 
    total_marked_rows = int((zeros.sum(axis=1) >= 1).sum())
    num_words_with_hits = int((zeros.sum(axis=0) > 0).sum())
    print(f"   ➤ Rows with any target word: {total_marked_rows} | Words that appeared: {num_words_with_hits}")

    output_path = os.path.join(output_dir, f"{stem}_word_instances.csv")
    out_df.to_csv(output_path, index=False)
    print(f"✅ Saved annotated transcript to: {output_path}")
