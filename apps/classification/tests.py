from django.test import TestCase

from apps.classification.classifier import OpportunityClassifier


class OpportunityClassifierTests(TestCase):
    def test_keyword_fallback_domain_prediction(self):
        classifier = OpportunityClassifier()
        classifier.model = None
        classifier.vectorizer = None
        classifier.zero_shot_classifier = None

        domain = classifier.predict_domain("Machine learning and deep learning internship.")
        self.assertIn(domain, classifier.domain_categories)
        self.assertEqual(domain, "ai")

    def test_extract_requirements(self):
        classifier = OpportunityClassifier()
        requirements = classifier.extract_requirements(
            "Applicants must have 3.5 GPA and strong Python background. Final year students preferred."
        )
        self.assertTrue(isinstance(requirements, list))
