import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB, GaussianNB
import random

class ProbabilisticAnalyzer:
    def __init__(self):
        self._initialize_department_classifier()
        self._initialize_disease_risk_model()
        
    def _initialize_department_classifier(self):
        """
        Initializes a Text-based Naive Bayes model to classify the medical department.
        """
        # Simulated training data for text classification
        texts = [
            "heart rate fast blood pressure high chest pain",
            "ekg abnormal hypertension cholesterol elevated",
            "glucose insulin high blood sugar thirsty diabetes",
            "kidney function impaired urea creatinine levels",
            "hemoglobin low rbc count iron deficiency anemia",
            "blood counts wbc platelets bleeding clotting",
            "fracture broken bone x-ray sprain joint pain",
            "stomach ache acid reflux digestive pain ulcer",
            "frequent urination weight loss high a1c levels",
            "palpitations shortness of breath cardiac arrest"
        ]
        
        self.labels = [
            "Cardiology", "Cardiology",
            "Endocrinology", "Nephrology",
            "Hematology", "Hematology",
            "Orthopedics", "Gastroenterology",
            "Endocrinology", "Cardiology"
        ]
        
        self.vectorizer = CountVectorizer()
        X = self.vectorizer.fit_transform(texts)
        
        # Multinomial Naive Bayes is ideal for text/bag-of-words
        self.dept_clf = MultinomialNB()
        self.dept_clf.fit(X, self.labels)
        
    def _initialize_disease_risk_model(self):
        """
        Initializes a Gaussian Naive Bayes model (acting like a simple Bayesian Network)
        to predict the probability of a health condition based on lab values.
        Features: [Glucose, Hemoglobin, Cholesterol]
        """
        # Simulated lab parameter data
        # Let class 0 = Healthy, 1 = Diabetic Risk, 2 = Anemic Risk, 3 = Cardiovascular Risk
        
        # [Glucose, Hemoglobin, Cholesterol]
        X_nums = [
            [90, 14, 180], [105, 15, 160], [80, 13, 190],   # Healthy
            [200, 14, 190], [180, 15, 210], [250, 14, 180],  # Diabetic
            [95, 9, 170], [100, 10, 180], [85, 8, 160],      # Anemic
            [110, 14, 280], [105, 15, 300], [90, 14, 260]    # Cardiovascular
        ]
        
        y_nums = [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]
        
        self.risk_labels = {
            0: "Healthy / General",
            1: "Metabolic / Diabetic Risk",
            2: "Anemic Risk",
            3: "Cardiovascular Risk"
        }
        
        # Gaussian Naive Bayes is ideal for continuous/numeric features
        self.risk_clf = GaussianNB()
        self.risk_clf.fit(X_nums, y_nums)

    def predict_department(self, text):
        """
        Predicts the department and returns probabilities using text-based Naive Bayes.
        """
        if not text or len(text.strip()) < 10:
            return {"predicted": "General Practice", "confidence": "Medium", "probabilities": []}
            
        X_test = self.vectorizer.transform([text])
        probs = self.dept_clf.predict_proba(X_test)[0]
        
        # Get top 3 predictions
        top_indices = np.argsort(probs)[-3:][::-1]
        
        results = []
        for idx in top_indices:
            if probs[idx] > 0.05: # Only include if probability > 5%
                results.append({
                    "department": self.labels[self.dept_clf.classes_[idx] if isinstance(self.dept_clf.classes_[0], int) else idx], # Handle sklearn label encoding
                    "probability": round(probs[idx] * 100, 1)
                })
        
        # Determine confidence
        max_prob = probs[top_indices[0]]
        if max_prob > 0.6: confidence = "High"
        elif max_prob > 0.4: confidence = "Medium"
        else: confidence = "Low"
                
        # Handle string labels properly
        predicted_dept = self.dept_clf.classes_[top_indices[0]]
        
        return {
            "predicted": predicted_dept,
            "confidence": confidence,
            "probabilities": results
        }

    def predict_disease_risk(self, values):
        """
        Predicts disease risk probabilities using Gaussian Naive Bayes on numeric features.
        """
        # Extract values or use medians for missing data
        glucose = values.get('glucose') or 100
        hemoglobin = values.get('hemoglobin') or 14
        cholesterol = values.get('cholesterol') or 180
        
        features = [[glucose, hemoglobin, cholesterol]]
        
        probs = self.risk_clf.predict_proba(features)[0]
        
        results = []
        for i, class_id in enumerate(self.risk_clf.classes_):
            if probs[i] > 0.01: # Include if prob > 1%
                results.append({
                    "risk_category": self.risk_labels[class_id],
                    "probability": round(probs[i] * 100, 1)
                })
                
        # Sort by probability
        results = sorted(results, key=lambda x: x["probability"], reverse=True)
        
        # Top Risk
        top_class_id = self.risk_clf.classes_[np.argmax(probs)]
        
        return {
            "primary_risk": self.risk_labels[top_class_id],
            "max_probability": round(np.max(probs) * 100, 1),
            "all_probabilities": results
        }
