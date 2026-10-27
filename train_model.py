import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import pickle

print("Loading dataset...")
df = pd.read_csv("datasets/final_dataset.csv")

print("\n===== LABEL 0 SAMPLES =====")
print(df[df['label'] == 0].head(20))

print("\n===== LABEL 1 SAMPLES =====")
print(df[df['label'] == 1].head(20))

X = df['text']
y = df['label']

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Converting text...")
vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

print("Training model...")
model = LogisticRegression(max_iter=1000, C=5)
model.fit(X_train_vec, y_train)

print("Testing model...")
y_pred = model.predict(X_test_vec)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, target_names=['Safe', 'Attack']))

pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))
print("Model saved!")
