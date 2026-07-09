"""
NLP Processor for Medical Report Summarization
Implements simple extractive summarization using sentence ranking
"""

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import string
import time

# Download required NLTK data
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)


class NLPProcessor:
    """Simple NLP-based text summarizer using extractive approach"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
    
    def preprocess_text(self, text):
        """Clean and tokenize text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        return text
    
    def remove_stopwords(self, words):
        """Remove common English stopwords"""
        return [word for word in words if word not in self.stop_words]
    
    def calculate_word_frequency(self, text):
        """Calculate frequency of important words"""
        words = word_tokenize(text)
        words = self.remove_stopwords(words)
        
        freq = {}
        for word in words:
            freq[word] = freq.get(word, 0) + 1
        
        return freq
    
    def rank_sentences(self, sentences, word_freq):
        """Rank sentences based on word frequency scores"""
        sentence_scores = {}
        
        for idx, sentence in enumerate(sentences):
            score = 0
            words = word_tokenize(sentence.lower())
            words = self.remove_stopwords(words)
            
            for word in words:
                if word in word_freq:
                    score += word_freq[word]
            
            # Normalize by sentence length to avoid bias towards longer sentences
            if len(words) > 0:
                score = score / len(words)
            
            sentence_scores[idx] = score
        
        return sentence_scores
    
    def summarize(self, text, num_sentences=2):
        """
        Generate extractive summary by selecting top-ranked sentences
        
        Args:
            text: Input text to summarize
            num_sentences: Number of sentences to include in summary
            
        Returns:
            Dictionary with summary text and processing time
        """
        start_time = time.time()
        
        # Handle empty or very short text
        if not text or len(text.strip()) < 50:
            return {
                'summary': text,
                'processing_time': 0,
                'method': 'NLP (Extractive)'
            }
        
        # Tokenize into sentences
        sentences = sent_tokenize(text)
        
        # If text has few sentences, return as-is
        if len(sentences) <= num_sentences:
            return {
                'summary': text,
                'processing_time': round((time.time() - start_time) * 1000, 2),
                'method': 'NLP (Extractive)'
            }
        
        # Calculate word frequencies
        word_freq = self.calculate_word_frequency(text)
        
        # Rank sentences
        sentence_scores = self.rank_sentences(sentences, word_freq)
        
        # Get top sentences by score
        ranked_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
        top_indices = ranked_indices[:num_sentences]
        
        # Sort selected indices by original order for coherence
        top_indices.sort()
        
        # Build summary
        summary_sentences = [sentences[i] for i in top_indices]
        summary = ' '.join(summary_sentences)
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'summary': summary,
            'processing_time': processing_time,
            'method': 'NLP (Extractive)',
            'original_length': len(text),
            'summary_length': len(summary),
            'compression_ratio': round((1 - len(summary)/len(text)) * 100, 1) if len(text) > 0 else 0
        }


def summarize_medical_report(text):
    """
    Convenience function to summarize medical report
    
    Args:
        text: Medical report text
        
    Returns:
        Dictionary with summary results
    """
    processor = NLPProcessor()
    return processor.summarize(text)


if __name__ == "__main__":
    # Test the NLP processor
    sample_text = """
    Patient blood glucose level is 180 mg/dL. 
    Hemoglobin count shows 11 g/dL. 
    Total cholesterol measured at 220 mg/dL.
    The patient reports frequent urination and excessive thirst.
    Blood pressure reading was 140/90 mmHg.
    """
    
    result = summarize_medical_report(sample_text)
    print("Original Text:")
    print(sample_text)
    print("\nNLP Summary:")
    print(result['summary'])
    print(f"\nProcessing Time: {result['processing_time']}ms")
