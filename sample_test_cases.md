# Sample Medical Reports for Testing

## Test Case 1: Multiple Issues
```
Patient Information: John Doe, Age 45
Date: March 28, 2026

Blood Test Results:
- Fasting glucose level measured at 180 mg/dL
- Hemoglobin count shows 11 g/dL
- Total cholesterol measured at 220 mg/dL
- Blood pressure: 140/90 mmHg

Symptoms:
The patient reports frequent urination and excessive thirst over the past two weeks. 
Also complains of fatigue and occasional dizziness.

Recommendations:
Follow-up appointment scheduled in 2 weeks. Lifestyle modifications discussed.
```

**Expected Results:**
- High Blood Sugar (Diabetes Risk)
- Low Hemoglobin (Anemia Risk)
- High Cholesterol

---

## Test Case 2: Normal Report
```
Annual Health Checkup - March 2026

Laboratory Findings:
Glucose (fasting): 95 mg/dL
Hemoglobin: 14.5 g/dL
Total Cholesterol: 175 mg/dL
Triglycerides: 140 mg/dL
HDL Cholesterol: 55 mg/dL
LDL Cholesterol: 100 mg/dL

Clinical Assessment:
All values within normal limits. Patient appears healthy.
No abnormal findings detected during examination.

Physician Notes:
Continue current healthy lifestyle. Schedule next checkup in 12 months.
```

**Expected Results:**
- No issues detected
- Normal report summary

---

## Test Case 3: Single Issue
```
Medical Laboratory Report
Patient ID: 12345

Biochemistry Panel:
Serum Glucose: 165 mg/dL (elevated)
Complete Blood Count:
  Hemoglobin: 13.8 g/dL
  RBC: Normal morphology
Lipid Profile:
  Cholesterol: 190 mg/dL
  HDL: 45 mg/dL
  LDL: 120 mg/dL

Interpretation:
Glucose level indicates possible impaired glucose tolerance.
Other parameters are unremarkable.
```

**Expected Results:**
- High Blood Sugar (Diabetes Risk)
- Other values normal

---

## Test Case 4: Critical Values
```
EMERGENCY DEPARTMENT LAB REPORT
Date: 03/28/2026 Time: 14:30

STAT Laboratory Results:
Blood Glucose: 250 mg/dL - CRITICALLY HIGH
Hemoglobin: 8.5 g/dL - LOW
Cholesterol: 280 mg/dL - HIGH

Additional Findings:
Ketones present in urine
Patient exhibits confusion and rapid breathing
History of Type 2 Diabetes Mellitus

Immediate Actions Required:
Endocrinology consultation requested
Insulin therapy initiated
```

**Expected Results:**
- Severe High Blood Sugar
- Significant Anemia Risk
- Very High Cholesterol
- Multiple health advisories

---

## Test Case 5: Borderline Values
```
Routine Health Screening

Metabolic Panel Results:
Fasting Glucose: 135 mg/dL (high-normal)
Hemoglobin A1C: 5.9%
Complete Blood Count:
  Hemoglobin: 12.1 g/dL (low-normal)
Lipid Studies:
  Total Cholesterol: 198 mg/dL (borderline)
  HDL: 42 mg/dL
  LDL: 130 mg/dL

Assessment:
Values approaching threshold levels. 
Preventive measures recommended.

Plan:
Dietary counseling scheduled.
Exercise program to be initiated.
Repeat testing in 3 months.
```

**Expected Results:**
- Borderline values (may or may not trigger alerts depending on exact thresholds)

---

## Test Case 6: NLP Testing (Long Form)
```
COMPREHENSIVE MEDICAL EVALUATION REPORT

Patient Demographics:
Name: Sarah Johnson
Age: 52 years
Gender: Female
Date of Visit: March 28, 2026
MRN: 987654

Chief Complaint:
Patient presents for annual physical examination with no acute complaints. 
Reports feeling generally well but notes some increased fatigue over recent months.

History of Present Illness:
The patient is a 52-year-old female who comes to clinic for routine follow-up. 
She reports compliance with medications including metformin 500mg twice daily. 
Home glucose monitoring shows readings ranging from 140-180 mg/dL fasting. 
She denies any chest pain, shortness of breath, or palpitations.

Physical Examination:
Vital Signs: BP 138/88 mmHg, HR 78 bpm, Temp 98.6°F, Weight 185 lbs
General: Well-developed, well-nourished female in no acute distress
Cardiovascular: Regular rate and rhythm, no murmurs
Respiratory: Clear to auscultation bilaterally
Extremities: No edema, pulses 2+ bilaterally

Laboratory Data:
Comprehensive Metabolic Panel completed this morning shows:
- Fasting blood glucose: 158 mg/dL (reference range: 70-100 mg/dL)
- Hemoglobin: 11.2 g/dL (reference range: 12.0-16.0 g/dL)  
- Total cholesterol: 215 mg/dL (reference range: <200 mg/dL)
- HbA1c: 7.2% (reference range: <5.7%)
- Creatinine: 0.9 mg/dL (normal)
- BUN: 18 mg/dL (normal)
- Liver function tests within normal limits

Assessment and Plan:
1. Type 2 Diabetes Mellitus - suboptimally controlled
   - Increase metformin to 750mg twice daily
   - Reinforce dietary modifications
   - Continue home glucose monitoring

2. Anemia - likely iron deficiency
   - Order iron studies
   - Consider iron supplementation
   - Dietary counseling regarding iron-rich foods

3. Hyperlipidemia
   - Discuss statin therapy options
   - Emphasize heart-healthy diet
   - Recommend regular aerobic exercise

4. Hypertension - borderline
   - Continue current ACE inhibitor
   - Encourage sodium restriction
   - Home blood pressure monitoring

Follow-up:
Return to clinic in 6 weeks for repeat laboratory evaluation.
Sooner if symptoms worsen or new concerns develop.

Provider: Dr. Michael Chen, MD
Specialty: Internal Medicine
Contact: (555) 123-4567
```

**Expected Results:**
- All three main issues detected
- Comprehensive NLP summary
- Detailed explanations
- Rich advice generation

---

## Instructions for Testing

1. Copy any of the above test cases
2. Paste into the application's textarea
3. Click "Analyze Report"
4. Compare results across different test cases
5. Test both Rule-Based and NLP summarization
6. Review the comparison table

### Additional Testing Scenarios:

- **Empty Input**: Test error handling
- **Very Short Text**: Test minimum length handling
- **Unformatted Text**: Test robustness
- **Numbers without Units**: Test regex flexibility
- **Multiple Measurements**: Test value extraction accuracy
