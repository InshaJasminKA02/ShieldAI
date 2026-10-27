import pandas as pd

deepset_train = pd.read_parquet("datasets/deepset_train.parquet")
hackaprompt = pd.read_parquet("datasets/hackaprompt.parquet")
safeguard_train = pd.read_parquet("datasets/safeguard_train.parquet")

print("=== DEEPSET ===")
print(deepset_train.head(3))
print("Columns:", deepset_train.columns.tolist())

print("\n=== HACKAPROMPT ===")
print(hackaprompt.head(3))
print("Columns:", hackaprompt.columns.tolist())

print("\n=== SAFEGUARD ===")
print(safeguard_train.head(3))
print("Columns:", safeguard_train.columns.tolist())