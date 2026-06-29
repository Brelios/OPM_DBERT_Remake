import pandas as pd
import sys
import os

# Set standard output encoding to utf-8 to avoid console print crashes on Windows
sys.stdout.reconfigure(encoding='utf-8')

print("Starting dataset preparation...")

# 1. Load Dataset-SA.csv
print("Processing Dataset-SA.csv...")
try:
    df_sa = pd.read_csv('Dataset-SA.csv', usecols=['Review', 'Rate'])
    df_sa['Rate'] = pd.to_numeric(df_sa['Rate'], errors='coerce')
    df_sa = df_sa.dropna(subset=['Review', 'Rate'])
    df_sa = df_sa[df_sa['Rate'].isin([1, 2, 3, 4, 5])]
    # Map to 0-4
    df_sa['Label'] = df_sa['Rate'].astype(int) - 1
    df_sa = df_sa[['Review', 'Label']]
    print(f"Loaded Dataset-SA: {df_sa.shape[0]} rows")
except Exception as e:
    print(f"Error loading Dataset-SA.csv: {e}")
    df_sa = pd.DataFrame(columns=['Review', 'Label'])

# 2. Load flipkart_product.csv
print("Processing flipkart_product.csv...")
try:
    df_fp = pd.read_csv('flipkart_product.csv', encoding='latin1', usecols=['Review', 'Rate'])
    df_fp['Rate'] = pd.to_numeric(df_fp['Rate'], errors='coerce')
    df_fp = df_fp.dropna(subset=['Review', 'Rate'])
    df_fp = df_fp[df_fp['Rate'].isin([1, 2, 3, 4, 5])]
    df_fp['Label'] = df_fp['Rate'].astype(int) - 1
    df_fp = df_fp[['Review', 'Label']]
    print(f"Loaded flipkart_product: {df_fp.shape[0]} rows")
except Exception as e:
    print(f"Error loading flipkart_product.csv: {e}")
    df_fp = pd.DataFrame(columns=['Review', 'Label'])

# 3. Load IMDB-Dataset.csv
print("Processing IMDB-Dataset.csv...")
try:
    df_imdb = pd.read_csv('IMDB-Dataset.csv', usecols=['review', 'sentiment'])
    df_imdb = df_imdb.dropna(subset=['review', 'sentiment'])
    df_imdb = df_imdb.rename(columns={'review': 'Review'})
    # Map binary sentiment: positive -> 3 (Positive), negative -> 1 (Negative)
    sentiment_map = {'positive': 3, 'negative': 1}
    df_imdb['Label'] = df_imdb['sentiment'].str.strip().str.lower().map(sentiment_map)
    df_imdb = df_imdb.dropna(subset=['Label'])
    df_imdb['Label'] = df_imdb['Label'].astype(int)
    df_imdb = df_imdb[['Review', 'Label']]
    print(f"Loaded IMDB-Dataset: {df_imdb.shape[0]} rows")
except Exception as e:
    print(f"Error loading IMDB-Dataset.csv: {e}")
    df_imdb = pd.DataFrame(columns=['Review', 'Label'])

# Combine Training Data
print("Combining training datasets...")
df_train = pd.concat([df_sa, df_fp, df_imdb], ignore_index=True)
df_train = df_train.dropna(subset=['Review', 'Label'])
df_train['Review'] = df_train['Review'].astype(str).str.strip()
df_train = df_train[df_train['Review'] != '']
# Shuffle training data
df_train = df_train.sample(frac=1, random_state=42).reset_index(drop=True)
print(f"Total merged training rows: {df_train.shape[0]}")
print("Label counts in training data:")
print(df_train['Label'].value_counts())

# Save clean training data
train_path = 'train_clean.csv'
df_train.to_csv(train_path, index=False, encoding='utf-8')
print(f"Saved merged training data to {train_path}")

# 4. Load and clean test.csv
print("Processing test.csv...")
try:
    df_test = pd.read_csv('test.csv', encoding='utf-8', usecols=['Review', 'Label'])
    df_test = df_test.dropna(subset=['Review', 'Label'])
    df_test['Label'] = pd.to_numeric(df_test['Label'], errors='coerce')
    df_test = df_test.dropna(subset=['Label'])
    # Map labels: 2 -> 3 (Positive), 1 -> 1 (Negative)
    df_test = df_test[df_test['Label'].isin([1, 2])]
    test_map = {1: 1, 2: 3}
    df_test['Label'] = df_test['Label'].map(test_map).astype(int)
    df_test['Review'] = df_test['Review'].astype(str).str.strip()
    df_test = df_test[df_test['Review'] != '']
    df_test = df_test.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Loaded and cleaned test.csv: {df_test.shape[0]} rows")
    
    test_path = 'test_clean.csv'
    df_test.to_csv(test_path, index=False, encoding='utf-8')
    print(f"Saved cleaned testing data to {test_path}")
except Exception as e:
    print(f"Error loading/processing test.csv: {e}")

print("Dataset preparation complete!")
