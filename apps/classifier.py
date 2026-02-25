import joblib
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import Dict, List, Tuple
import logging
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class TextPreprocessor:
    def __init__(self):
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
    def preprocess(self, text: str) -> str:
        """Clean and preprocess text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) 
                 for token in tokens if token not in self.stop_words]
        
        return ' '.join(tokens)

class OpportunityClassifier:
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.domain_categories = [
            'ai', 'ml', 'ds', 'cs', 'ece', 'mech', 'bio', 
            'chem', 'physics', 'math', 'business', 'law', 
            'medicine', 'humanities'
        ]
        self.keyword_map = {
            "ai": ["artificial intelligence", "llm", "nlp", "computer vision", "deep learning", "neural"],
            "ml": ["machine learning", "supervised", "unsupervised", "model training", "regression"],
            "ds": ["data science", "analytics", "data analysis", "data mining", "business intelligence"],
            "cs": ["software", "algorithms", "programming", "computer science", "backend", "frontend"],
            "ece": ["electronics", "embedded", "vlsi", "signal processing", "microcontroller", "ece"],
            "mech": ["mechanical", "cad", "robotics", "manufacturing", "thermodynamics"],
            "bio": ["biomedical", "biotech", "genomics", "bioinformatics"],
            "chem": ["chemistry", "chemical", "organic", "inorganic"],
            "physics": ["physics", "quantum", "astrophysics", "particle"],
            "math": ["mathematics", "statistics", "calculus", "probability"],
            "business": ["business", "finance", "marketing", "consulting", "management"],
            "law": ["law", "legal", "jurisprudence", "policy", "litigation"],
            "medicine": ["medicine", "clinical", "healthcare", "medical", "public health"],
            "humanities": ["history", "philosophy", "literature", "sociology", "anthropology"],
        }
        self.zero_shot_classifier = self._load_zero_shot_model()
        
        # Load or create traditional ML model
        self.model_path = os.path.join(settings.BASE_DIR, 'models', 'classifier.pkl')
        self.vectorizer_path = os.path.join(settings.BASE_DIR, 'models', 'vectorizer.pkl')
        
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
        else:
            self.model = None
            self.vectorizer = None
    
    def _load_zero_shot_model(self):
        """
        Load transformer pipeline only if available locally.
        Falls back to keyword matching to keep the app functional offline.
        """
        try:
            from transformers import pipeline

            return pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1,
            )
        except Exception as exc:
            logger.warning("Zero-shot model unavailable; using keyword fallback. %s", exc)
            return None
            
    def classify_opportunity(self, opportunity_id):
        """Classify a single opportunity by ID"""
        from apps.opportunities.models import Opportunity
        
        try:
            opportunity = Opportunity.objects.get(id=opportunity_id)
            
            # Combine title and description for classification
            text = f"{opportunity.title} {opportunity.description}"
            
            # Get domain classification
            domain = self.predict_domain(text)
            
            # Extract requirements and skills
            requirements = self.extract_requirements(text)
            
            # Update opportunity
            opportunity.domain = domain
            opportunity.requirements = requirements
            opportunity.save()
            
            logger.info(f"Classified opportunity {opportunity_id} as {domain}")
            return domain
            
        except Exception as e:
            logger.error(f"Classification failed for {opportunity_id}: {str(e)}")
            return None
    
    def predict_domain(self, text: str) -> str:
        """Predict domain category for text"""
        cleaned_text = self.preprocessor.preprocess(text)
        
        if self.model and self.vectorizer:
            # Use trained ML model
            X = self.vectorizer.transform([cleaned_text])
            return self.model.predict(X)[0]
        else:
            if self.zero_shot_classifier:
                result = self.zero_shot_classifier(
                    text, 
                    candidate_labels=self.domain_categories
                )
                return result['labels'][0]
            return self._predict_by_keywords(cleaned_text)

    def _predict_by_keywords(self, cleaned_text: str) -> str:
        scores: Dict[str, int] = {domain: 0 for domain in self.domain_categories}
        for domain, keywords in self.keyword_map.items():
            for keyword in keywords:
                if keyword in cleaned_text:
                    scores[domain] += 1
        best_domain = max(scores, key=scores.get)
        return best_domain if scores[best_domain] > 0 else "cs"
    
    def extract_requirements(self, text: str) -> List[str]:
        """Extract key requirements from text"""
        # Use NER and keyword extraction
        requirements = []
        
        # Define requirement patterns
        patterns = {
            'gpa': r'\d+\.?\d*\s*GPA',
            'year': r'\d+[th]{2}\s+(year|semester)',
            'skill': r'(Python|Java|C\+\+|Machine Learning|Data Science|Research)',
            'degree': r'(Bachelor|Master|PhD|Undergraduate|Graduate)',
        }
        
        for req_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            requirements.extend(matches)
            
        return list(set(requirements))
    
    def train_model(self, training_data: List[Tuple[str, str]]):
        """Train the classification model"""
        texts = [self.preprocessor.preprocess(item[0]) for item in training_data]
        labels = [item[1] for item in training_data]
        
        # Create pipeline
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        
        # Fit
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)
        
        # Save models
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        
        logger.info(f"Model trained on {len(texts)} samples")
