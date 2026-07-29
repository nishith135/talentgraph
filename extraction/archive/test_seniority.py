from transformers import pipeline

# Load a zero-shot classifier
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Test on a sample job description
sample_text = "We are looking for a Python Developer with 7+ years of experience in backend systems, microservices architecture, and team leadership."

labels = ["junior", "mid-level", "senior"]

result = classifier(sample_text, labels)
print(result)