# PDF Upload Feature Guide

## Overview
The Medical Report Summarizer now supports **PDF file uploads**! You can directly upload medical report PDFs, and the system will automatically extract the text and analyze it.

## How to Use PDF Upload

### Step 1: Click "Upload PDF Report"
- Locate the dashed upload area at the top of the input section
- Click the blue "📄 Upload PDF Report" button
- Select a PDF file from your computer

### Step 2: Automatic Text Extraction
- The system will automatically extract text from the PDF
- Extracted text will appear in the textarea below
- File name and size will be displayed with a green background

### Step 3: Analyze
- Click "Analyze Report" as usual
- The system processes the extracted text
- View all results: summary, issues, advice, NLP summary, and comparison

### Step 4: Remove or Clear
- To remove uploaded file: click the red × button
- To clear everything: use the "Clear" button

## Supported Files

✅ **Supported:**
- Text-based PDF files
- Scanned documents with OCR (Optical Character Recognition)
- Multi-page PDFs
- Files up to 16MB in size

❌ **Not Supported:**
- Image-only PDFs (without OCR)
- Password-protected PDFs
- Corrupted or damaged PDF files
- Non-PDF file types

## Technical Details

### Backend Processing
1. **File Upload**: Secure file upload via HTTP POST
2. **Text Extraction**: PyPDF2 library extracts text from each page
3. **Cleanup**: Uploaded files are automatically deleted after extraction
4. **Validation**: File type and size validation

### Privacy & Security
- Files are processed locally on the server
- No files are stored permanently
- Automatic cleanup after text extraction
- Secure filename sanitization

## Example PDF Content

Your medical report PDF should contain text like:

```
PATIENT MEDICAL REPORT

Patient Name: John Doe
Date: March 28, 2026
Age: 45 years

LABORATORY RESULTS

Blood Chemistry:
- Fasting Glucose: 180 mg/dL
- Hemoglobin: 11 g/dL  
- Total Cholesterol: 220 mg/dL
- HDL: 45 mg/dL
- LDL: 150 mg/dL

Complete Blood Count:
- WBC: 7,500/mm³
- RBC: 4.8 million/mm³
- Platelets: 250,000/mm³

IMPRESSION:
- Elevated blood glucose levels
- Low hemoglobin count
- High cholesterol

RECOMMENDATIONS:
- Dietary modifications
- Regular exercise
- Follow-up in 2 weeks
```

## Troubleshooting

### Issue: "Could not extract text from PDF"
**Cause**: PDF is image-based or scanned without OCR
**Solution**: 
- Use a text-based PDF
- Run OCR on the PDF first using tools like Adobe Acrobat or online OCR services
- Manually copy-paste the text instead

### Issue: "File size must be less than 16MB"
**Cause**: PDF file is too large
**Solution**:
- Compress the PDF using online tools
- Split multi-page PDFs into smaller files
- Remove unnecessary images or graphics

### Issue: Upload button doesn't respond
**Cause**: Browser compatibility issue
**Solution**:
- Refresh the page
- Try a different browser (Chrome, Firefox, Edge)
- Check browser console for errors

### Issue: Extracted text is garbled or unreadable
**Cause**: PDF encoding issues or complex formatting
**Solution**:
- Try copying text manually from the PDF
- Ensure PDF is properly formatted
- Use a simpler PDF format

## Benefits of PDF Upload

✨ **Convenience**: No need to manually copy-paste text
✨ **Speed**: Automatic extraction in seconds
✨ **Accuracy**: Preserves original text content
✨ **Multi-page**: Handles long reports easily
✨ **Professional**: Works with official medical report formats

## Limitations

⚠️ **Text-Based Only**: Must contain selectable text (not just images)
⚠️ **Formatting**: Some formatting may be lost during extraction
⚠️ **Tables**: Complex tables may not extract perfectly
⚠️ **Handwriting**: Cannot extract handwritten notes

## Best Practices

1. **Use Quality PDFs**: Ensure PDF is clear and text-based
2. **Check Extraction**: Review extracted text for accuracy
3. **Edit if Needed**: Modify extracted text before analysis
4. **One at a Time**: Upload one PDF at a time for best results

## Alternative: Copy-Paste Method

If PDF upload doesn't work, you can still:
1. Open the PDF in a PDF reader
2. Select and copy all text (Ctrl+A, Ctrl+C)
3. Paste into the textarea (Ctrl+V)
4. Click "Analyze Report"

## Future Enhancements

Potential improvements:
- OCR integration for scanned documents
- Support for DOC/DOCX files
- Image upload with text recognition
- Batch PDF processing
- Cloud storage integration
- PDF annotation support

---

**Note**: This PDF upload feature is designed for educational and demonstration purposes. Always verify extracted text accuracy for critical applications.
