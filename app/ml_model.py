from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

training_sentences = [
    "track my order",
    "where is my order",
    "cancel my order",
    "talk to agent",
    "connect me to support"
]

training_labels = [
    "track",
    "track",
    "cancel",
    "agent",
    "agent"
]

vectorizer = TfidfVectorizer()
X_train = vectorizer.fit_transform(training_sentences)

model = MultinomialNB()
model.fit(X_train, training_labels)

def predict_intent(text):
    vec = vectorizer.transform([text.lower()])
    return model.predict(vec)[0]