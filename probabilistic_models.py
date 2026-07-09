import numpy as np
from collections import defaultdict, Counter
from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

try:
    from hmmlearn.hmm import GaussianHMM

    _HMM_AVAILABLE = True
except ImportError:
    GaussianHMM = None
    _HMM_AVAILABLE = False

class ProbabilisticAnalyzer:
    def __init__(self):
        self._train_department_model()
        self._train_risk_model()
        
    def _train_department_model(self):
        # Massively Expanded Dataset for Departments (TF-IDF Ready)
        texts = [
            # Cardiology
            "heart rate fast blood pressure high chest pain", "ekg abnormal hypertension cholesterol elevated", 
            "palpitations shortness of breath cardiac arrest", "myocardial infarction flutter angina arteries blocked", 
            "tachycardia bradycardia arrhythmia ecg pacing",
            # Endocrinology
            "glucose insulin high blood sugar thirsty diabetes", "frequent urination weight loss high a1c levels",
            "thyroid tsh hormone imbalance hyperthyroidism", "metabolic syndrome obesity hormone replacement",
            "polycystic ovary syndrome pcos insulin resistance",
            # Nephrology
            "kidney function impaired urea creatinine levels", "renal failure dialysis chronic kidney disease",
            "glomerular filtration rate low gfr stones", "proteinuria hematuria acute tubular necrosis",
            "kidney stone painful urination high urea",
            # Hematology
            "hemoglobin low rbc count iron deficiency anemia", "blood counts wbc platelets bleeding clotting",
            "leukemia lymphoma bone marrow biopsy", "sickle cell trait blood transfusion required",
            "coagulation profile abnormal low platelets hematocrit",
            # Gastroenterology
            "stomach ache acid reflux digestive pain ulcer", "liver cirrhosis hepatitis fatty liver disease",
            "gallstones endoscopy colonoscopy biopsy required", "irritable bowel syndrome crohns abdominal pain",
            "reflux gerd heartburn esophagitis stomach cramps",
            # Orthopedics
            "fracture broken bone x-ray sprain joint pain", "arthritis osteoporosis joint swelling pain knee",
            "spinal cord compression disc herniation mri", "ligament tear acl sports injury bone graft",
            "osteoarthritis hip replacement joint dislocation",
            # Neurology & Imaging
            "mri brain scan infarcts ischemic hyperintensities white matter", "ct scan head neurology cerebral hemorrhage stroke",
            "cerebral atrophy ventricles sulci sella cisterns normal", "seizures epilepsy eeg abnormal brain waves",
            "axon degenerative neuropathy stroke recovery head trauma",
            # Radiology
            "x-ray fractured bone radiology imaging chest lungs", "ultrasound liver kidney stone abdominal imaging",
            "ct protocol contrast administered scan clear", "fluoroscopy mammogram dense biopsy guided",
            "positron emission tomography tumor staging pet scan",
            # Oncology
            "malignant tumor chemotherapy radiation oncology", "carcinoma melanoma cancer stages metastasis",
            "biopsy malignant cells positive pd-l1 pd-1", "brca1 mutation breast screening lumpectomy",
            "squamous cell carcinoma lung mass nodule finding"
        ]
        
        self.labels = [
            # Cardiology
            "Cardiology", "Cardiology", "Cardiology", "Cardiology", "Cardiology",
            # Endocrinology
            "Endocrinology", "Endocrinology", "Endocrinology", "Endocrinology", "Endocrinology",
            # Nephrology
            "Nephrology", "Nephrology", "Nephrology", "Nephrology", "Nephrology",
            # Hematology
            "Hematology", "Hematology", "Hematology", "Hematology", "Hematology",
            # Gastroenterology
            "Gastroenterology", "Gastroenterology", "Gastroenterology", "Gastroenterology", "Gastroenterology",
            # Orthopedics
            "Orthopedics", "Orthopedics", "Orthopedics", "Orthopedics", "Orthopedics",
            # Neurology
            "Neurology / MRI Center", "Neurology / MRI Center", "Neurology / MRI Center", "Neurology", "Neurology",
            # Radiology
            "Radiology", "Radiology", "Radiology", "Radiology", "Radiology",
            # Oncology
            "Oncology", "Oncology", "Oncology", "Oncology", "Oncology"
        ]
        
        # Upgraded to TF-IDF instead of CountVectorizer for far better accuracy on rare medical terms
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        X = self.vectorizer.fit_transform(texts)
        
        self.dept_clf = MultinomialNB(alpha=0.5)
        self.dept_clf.fit(X, self.labels)
        
    def _train_risk_model(self):
        # Features map: [Glucose, Hemoglobin, Cholesterol, TSH, Vitamin D, Heart Rate, WBC, Systolic BP, Diastolic BP]
        # Normal Defaults = [100, 14, 180, 2.0, 35, 75, 7.5, 110, 70]
        
        X_numeric = [
            # Healthy
            [95,  14.2, 175, 2.1, 38, 72, 6.8, 115, 75],
            [104, 13.8, 185, 1.8, 40, 78, 7.5, 110, 70],
            [98,  15.0, 160, 2.5, 45, 65, 5.5, 120, 80],
            [108, 14.5, 195, 2.0, 32, 80, 8.2, 118, 78],
            [90,  13.5, 150, 1.5, 50, 60, 6.0, 105, 65],
            # Metabolic / Diabetic Risk
            [250, 13.8, 190, 2.0, 35, 75, 7.5, 110, 70],
            [300, 14.2, 210, 1.9, 32, 82, 8.0, 125, 80],
            [180, 14.5, 185, 2.1, 38, 70, 7.2, 115, 75],
            [400, 13.5, 250, 2.2, 30, 88, 8.5, 130, 85],
            [210, 14.0, 195, 1.8, 36, 76, 7.8, 118, 78],
            # Anemic Risk
            [100, 8.5,  180, 2.0, 35, 95, 7.5, 110, 70],
            [95,  9.0,  175, 1.9, 38, 100, 6.8, 105, 65],
            [105, 7.8,  185, 2.1, 32, 110, 8.0, 115, 75],
            [98,  10.2, 160, 1.8, 40, 85, 7.0, 112, 72],
            [102, 6.5,  190, 2.2, 30, 120, 8.5, 100, 60],
            # Cardiovascular Risk (BP, HR, Chol)
            [100, 14.0, 320, 2.0, 35, 98,  7.5, 160, 95],
            [95,  14.5, 280, 1.9, 38, 90,  6.8, 150, 90],
            [105, 13.8, 350, 2.1, 32, 105, 8.0, 170, 100],
            [98,  15.0, 260, 1.8, 40, 85,  7.0, 145, 85],
            [102, 14.2, 400, 2.2, 30, 115, 8.5, 180, 110],
            # Thyroid Disorder (High TSH)
            [100, 14.0, 180, 12.5, 35, 55, 7.5, 110, 70],
            [95,  14.5, 175, 15.0, 38, 50, 6.8, 115, 75],
            [105, 13.8, 185, 10.2, 32, 60, 8.0, 105, 65],
            [98,  15.0, 160, 20.5, 40, 45, 7.0, 120, 80],
            [102, 14.2, 190, 8.8,  30, 58, 8.5, 112, 72],
            # Thyroid Disorder (Low TSH)
            [100, 14.0, 180, 0.1, 35, 115, 7.5, 110, 70],
            [95,  14.5, 175, 0.05, 38, 120, 6.8, 115, 75],
            [105, 13.8, 185, 0.2, 32, 110, 8.0, 105, 65],
            [98,  15.0, 160, 0.01, 40, 130, 7.0, 120, 80],
            [102, 14.2, 190, 0.3,  30, 105, 8.5, 112, 72],
            # Infection / Inflammatory
            [100, 14.0, 180, 2.0, 35, 95, 18.5, 110, 70],
            [95,  14.5, 175, 1.9, 38, 100, 22.0, 115, 75],
            [105, 13.8, 185, 2.1, 32, 90, 15.2, 105, 65],
            [98,  15.0, 160, 1.8, 40, 105, 25.5, 120, 80],
            [102, 14.2, 190, 2.2, 30, 85, 14.8, 112, 72]
        ]
        
        self.risk_labels = (
            ["Healthy / General"] * 5 +
            ["Metabolic / Diabetic Risk"] * 5 +
            ["Anemic Risk"] * 5 +
            ["Cardiovascular Risk"] * 5 +
            ["Hypothyroidism Risk"] * 5 +
            ["Hyperthyroidism Risk"] * 5 +
            ["Acute Infection / Inflammatory Risk"] * 5
        )
        
        X_arr = np.asarray(X_numeric, dtype=float)
        self.risk_clf = GaussianNB()
        self.risk_clf.fit(X_numeric, self.risk_labels)

        self.risk_rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=14,
            min_samples_leaf=1,
            random_state=42,
            class_weight="balanced_subsample",
        )
        self.risk_rf.fit(X_arr, self.risk_labels)

        # Isolation Forest for Anomaly Detection
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.anomaly_detector.fit(X_numeric)

        # Gaussian Mixture Model on scaled lab features — soft clustering of risk profiles
        self._risk_scaler = StandardScaler()
        X_scaled = self._risk_scaler.fit_transform(np.asarray(X_numeric, dtype=float))
        n_comp = 7
        self.gmm = GaussianMixture(
            n_components=n_comp,
            covariance_type="full",
            max_iter=300,
            random_state=42,
            n_init=3,
        )
        self.gmm.fit(X_scaled)
        # Map each mixture component to the majority risk label among training points most aligned to that component
        assign = self.gmm.predict(X_scaled)
        self.gmm_component_labels = {}
        risk_arr = np.array(self.risk_labels)
        for k in range(n_comp):
            mask = assign == k
            if not np.any(mask):
                self.gmm_component_labels[k] = "Mixed / Uncertain"
                continue
            labs, cnt = np.unique(risk_arr[mask], return_counts=True)
            self.gmm_component_labels[k] = str(labs[np.argmax(cnt)])

        # Hidden Markov Model: each patient's labs form a 9-step sequence (one dimension per timestep)
        self.risk_hmm = None
        self.hmm_state_labels = {}
        if _HMM_AVAILABLE:
            try:
                seqs = [X_scaled[i].reshape(-1, 1) for i in range(len(X_scaled))]
                X_hmm = np.vstack(seqs)
                lengths = [9] * len(seqs)
                hmm = GaussianHMM(
                    n_components=7,
                    covariance_type="diag",
                    n_iter=200,
                    random_state=42,
                    init_params="stmc",
                )
                hmm.fit(X_hmm, lengths)
                self.risk_hmm = hmm
                vote_buckets = [[] for _ in range(7)]
                for i, row in enumerate(X_scaled):
                    seg = row.reshape(-1, 1)
                    path = hmm.predict(seg)
                    for s in path:
                        vote_buckets[s].append(self.risk_labels[i])
                for s in range(7):
                    if not vote_buckets[s]:
                        self.hmm_state_labels[s] = "Mixed / Uncertain"
                    else:
                        u, c = np.unique(np.array(vote_buckets[s]), return_counts=True)
                        self.hmm_state_labels[s] = str(u[np.argmax(c)])
            except Exception:
                self.risk_hmm = None

    def predict_department(self, text):
        if not text or len(text.strip()) < 10:
            return {"predicted": "General Practice", "confidence": "Medium", "probabilities": []}
            
        X_test = self.vectorizer.transform([text])
        probs = self.dept_clf.predict_proba(X_test)[0]
        
        top_indices = np.argsort(probs)[-4:][::-1]
        
        results = []
        for idx in top_indices:
            if probs[idx] > 0.05:
                dept_name = self.dept_clf.classes_[idx]
                if isinstance(dept_name, (int, np.integer)):
                    dept_name = self.labels[dept_name]
                    
                results.append({
                    "department": dept_name,
                    "probability": round(probs[idx] * 100, 1)
                })
        
        max_prob = probs[top_indices[0]]
        if max_prob > 0.6: confidence = "High"
        elif max_prob > 0.4: confidence = "Medium"
        else: confidence = "Low"
                
        predicted_dept = self.dept_clf.classes_[top_indices[0]]
        if isinstance(predicted_dept, (int, np.integer)):
            predicted_dept = self.labels[predicted_dept]
        
        return {
            "predicted": predicted_dept,
            "confidence": confidence,
            "probabilities": results
        }

    def _feature_vector(self, values):
        defaults = [100, 14, 180, 2.0, 35, 75, 7.5, 110, 70]
        return [
            values.get("Glucose", defaults[0]),
            values.get("Hemoglobin", defaults[1]),
            values.get("Cholesterol", defaults[2]),
            values.get("TSH", defaults[3]),
            values.get("Vitamin D", defaults[4]),
            values.get("Heart Rate", defaults[5]),
            values.get("WBC", defaults[6]),
            values.get("Systolic BP", defaults[7]),
            values.get("Diastolic BP", defaults[8]),
        ]

    def _gmm_profile(self, features):
        """Soft assignment over mixture components, aggregated by clinical risk label."""
        fs = self._risk_scaler.transform([np.asarray(features, dtype=float)])
        comp_probs = self.gmm.predict_proba(fs)[0]
        agg = defaultdict(float)
        for k, p in enumerate(comp_probs):
            lab = self.gmm_component_labels.get(k, "Mixed / Uncertain")
            agg[lab] += float(p)
        ranked = sorted(agg.items(), key=lambda x: -x[1])
        mixture_detail = []
        for k, p in enumerate(comp_probs):
            if p > 0.005:
                mixture_detail.append({
                    "component": k,
                    "mapped_risk": self.gmm_component_labels.get(k, "Mixed / Uncertain"),
                    "responsibility_percent": round(p * 100, 1),
                })
        mixture_detail.sort(key=lambda x: -x["responsibility_percent"])
        primary = ranked[0][0] if ranked else "Unknown"
        primary_pct = round(ranked[0][1] * 100, 1) if ranked else 0.0
        all_gmm = [{"risk_profile": lab, "probability": round(pr * 100, 1)} for lab, pr in ranked[:5]]
        return {
            "primary_profile": primary,
            "profile_confidence_percent": primary_pct,
            "mixture_probabilities": all_gmm,
            "component_breakdown": mixture_detail[:7],
            "note": "Gaussian Mixture Model soft-clusters your lab vector into overlapping risk profiles.",
        }

    def _rf_prob_list(self, features, top_k=4):
        p = self.risk_rf.predict_proba([features])[0]
        idx = np.argsort(p)[-top_k:][::-1]
        out = []
        for j in idx:
            if p[j] <= 0.005:
                continue
            lab = self.risk_rf.classes_[j]
            if isinstance(lab, (int, np.integer)):
                lab = self.risk_labels[lab]
            out.append({"risk_category": str(lab), "probability": round(float(p[j]) * 100, 1)})
        return out

    def _nb_rf_ensemble(self, features):
        """Average calibrated posteriors from Gaussian NB and Random Forest."""
        nb_p = self.risk_clf.predict_proba([features])[0]
        rf_p = self.risk_rf.predict_proba([features])[0]
        classes_nb = [str(c) if not isinstance(c, (int, np.integer)) else str(self.risk_labels[c]) for c in self.risk_clf.classes_]
        classes_rf = [str(c) if not isinstance(c, (int, np.integer)) else str(self.risk_labels[c]) for c in self.risk_rf.classes_]
        merged = defaultdict(float)
        for c, v in zip(classes_nb, nb_p):
            merged[c] += 0.5 * float(v)
        for c, v in zip(classes_rf, rf_p):
            merged[c] += 0.5 * float(v)
        ranked = sorted(merged.items(), key=lambda x: -x[1])
        return merged, ranked

    def _hmm_profile(self, features):
        row = self._risk_scaler.transform([np.asarray(features, dtype=float)])[0]
        seq = row.reshape(-1, 1)
        if self.risk_hmm is None:
            return {
                "available": False,
                "note": "Hidden Markov model unavailable (install hmmlearn or check training).",
                "primary_risk": None,
                "path_summary": [],
            }
        try:
            path = self.risk_hmm.predict(seq)
            mapped = [self.hmm_state_labels.get(int(s), "Mixed / Uncertain") for s in path]
            cnt = Counter(mapped)
            total = len(mapped)
            scores = [{"risk_category": lab, "along_path_percent": round(100.0 * n / total, 1)} for lab, n in cnt.most_common()]
            primary = cnt.most_common(1)[0][0]
            return {
                "available": True,
                "note": "Interprets your nine lab dimensions as an ordered sequence; hidden states summarize patterns along that sequence.",
                "primary_risk": primary,
                "hidden_state_path": [int(s) for s in path],
                "path_summary": scores[:5],
            }
        except Exception as e:
            return {
                "available": False,
                "note": f"HMM inference skipped: {e}",
                "primary_risk": None,
                "path_summary": [],
            }

    def predict_disease_risk(self, values):
        """
        Ensemble (Gaussian NB + Random Forest) + Isolation Forest + GMM + Gaussian HMM sequence model.
        """
        features = self._feature_vector(values)

        is_anomaly = self.anomaly_detector.predict([features])[0] == -1

        merged, ranked = self._nb_rf_ensemble(features)
        top = [item for item in ranked[:5] if item[1] > 0.01]

        all_probs = [{"risk_category": c, "probability": round(p * 100, 1)} for c, p in top]
        primary_risk = top[0][0] if top else "Unknown"
        max_prob_percent = round(top[0][1] * 100, 1) if top else 0.0

        nb_only = self.risk_clf.predict_proba([features])[0]
        nb_idx = int(np.argmax(nb_only))
        nb_top = self.risk_clf.classes_[nb_idx]
        if isinstance(nb_top, (int, np.integer)):
            nb_top = self.risk_labels[nb_top]

        rf_top_idx = int(np.argmax(self.risk_rf.predict_proba([features])[0]))
        rf_top = self.risk_rf.classes_[rf_top_idx]
        if isinstance(rf_top, (int, np.integer)):
            rf_top = self.risk_labels[rf_top]

        if is_anomaly and "Healthy" not in str(primary_risk):
            primary_risk = str(primary_risk) + " (SEVERE STATISTICAL ANOMALY)"
        elif is_anomaly and "Healthy" in str(primary_risk):
            primary_risk = "Abnormal Parameter Combination (Anomaly)"
            all_probs.insert(0, {"risk_category": "Statistical Anomaly", "probability": 100})

        gmm_block = self._gmm_profile(features)
        hmm_block = self._hmm_profile(features)

        return {
            "primary_risk": primary_risk,
            "max_probability": max_prob_percent,
            "all_probabilities": all_probs,
            "gmm_mixture": gmm_block,
            "random_forest": {
                "top_probabilities": self._rf_prob_list(features),
                "tree_ensemble_note": "Random forest averages many decision trees on the same nine lab features.",
            },
            "ensemble_detail": {
                "method": "50% Gaussian Naive Bayes + 50% Random Forest",
                "naive_bayes_peak": str(nb_top),
                "random_forest_peak": str(rf_top),
            },
            "hidden_markov": hmm_block,
        }
