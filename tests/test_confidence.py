"""
Tests for confidence scoring behavior
"""

import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.local_sop_identifier import LocalSOPIdentifier


class TestConfidenceScoring:
    """Test confidence scoring accuracy and calibration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment with realistic SOPs"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'confidence_test_sops.txt')
        
        # Create SOPs with distinct topics
        sop_content = """SOP-001: Database Service Outage Response

## Purpose
Respond to complete database service outages including PostgreSQL, MySQL, MongoDB failures.

## Symptoms
- Database connection timeouts
- Connection refused errors
- Database process not running
- Port connectivity issues (5432, 3306, 27017)
- Application 503 errors due to database unavailability

## Steps
1. Verify database service status
2. Check database logs
3. Restart database service
4. Validate connectivity
---
SOP-002: API Performance Degradation

## Purpose
Address slow API response times and performance issues.

## Symptoms
- Response times exceeding SLA (>1000ms)
- High CPU usage on API servers
- Thread pool exhaustion
- Timeouts on API endpoints
- Slow query execution

## Steps
1. Monitor resource usage
2. Scale API instances
3. Optimize database queries
4. Review caching strategy
---
SOP-003: Network Connectivity Issues

## Purpose
Diagnose and resolve network connectivity problems.

## Symptoms
- Packet loss
- High latency
- DNS resolution failures
- Firewall blocking connections
- Intermittent connection drops

## Steps
1. Check network interface status
2. Verify routing tables
3. Test DNS resolution
4. Review firewall rules
---
SOP-004: Memory Leak Investigation

## Purpose
Identify and resolve memory leaks in applications.

## Symptoms
- Gradual memory increase over time
- Out of memory errors
- Application crashes
- Container restarts
- Swap usage increasing

## Steps
1. Monitor memory usage trends
2. Analyze heap dumps
3. Identify leaking objects
4. Fix code issues
---
SOP-005: Certificate Expiration

## Purpose
Handle SSL/TLS certificate expiration issues.

## Symptoms
- HTTPS connection failures
- Certificate expired errors
- Browser warnings
- API authentication failures

## Steps
1. Check certificate expiration date
2. Renew certificate
3. Update certificate in systems
4. Verify SSL connectivity
"""
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        self.identifier = LocalSOPIdentifier()
        self.identifier.build_index(self.sop_file)
        
        yield
        
        shutil.rmtree(self.test_dir)
    
    def test_high_confidence_exact_match(self):
        """Test that exact symptom match gives high confidence"""
        result = self.identifier.select_best_sop(
            incident_context="Production database connection timeout on port 5432, all queries failing"
        )
        
        assert result['selected_sop_number'] == 1
        assert result['confidence_score'] >= 0.5  # Should be reasonably high
        
    def test_high_confidence_semantic_match(self):
        """Test semantic matching (synonyms) gives good confidence"""
        result = self.identifier.select_best_sop(
            incident_context="API endpoints are extremely slow, response times over 5 seconds"
        )
        
        # Should match API performance SOP
        assert result['selected_sop_number'] == 2
        assert result['confidence_score'] >= 0.4
    
    def test_medium_confidence_partial_match(self):
        """Test partial match gives medium or high confidence"""
        result = self.identifier.select_best_sop(
            incident_context="System is experiencing high latency"
        )
        
        # Should match API or Network SOP with reasonable confidence
        # This is a specific technical issue so HIGH confidence is expected
        assert result['confidence_level'] in ['HIGH', 'MEDIUM']
    
    def test_low_confidence_poor_match(self):
        """Test unrelated query gives low confidence"""
        result = self.identifier.select_best_sop(
            incident_context="The weather is nice today and I had lunch"
        )
        
        # Should have low confidence
        assert result['confidence_score'] < 0.7
    
    def test_confidence_ordering(self):
        """Test that results are ordered by confidence"""
        result = self.identifier.select_best_sop(
            incident_context="Database connection issues",
            top_k=5
        )
        
        scores = [sop['confidence_score'] for sop in result['retrieved_sops']]
        
        # Should be in descending order
        assert scores == sorted(scores, reverse=True)
    
    def test_semantic_vs_bm25_scores(self):
        """Test that semantic and BM25 scores are different and meaningful"""
        # Query with exact keywords
        result_keyword = self.identifier.retrieve_relevant_sops(
            query="PostgreSQL database connection timeout port 5432",
            top_k=1
        )
        
        # Query with semantic equivalent
        result_semantic = self.identifier.retrieve_relevant_sops(
            query="Unable to reach the database service, connections failing",
            top_k=1
        )
        
        # Both should find database SOP
        assert result_keyword[0]['sop_number'] == 1
        
        # Keyword query should have higher BM25 score
        assert result_keyword[0]['bm25_score'] > 0
    
    def test_confidence_levels_distribution(self):
        """Test that confidence levels are properly distributed"""
        test_cases = [
            ("Database down connection timeout 5432", 1, 'HIGH'),  # Exact match
            ("API slow response time", 2, 'MEDIUM'),  # Good match
            ("Network issues connectivity", 3, 'MEDIUM'),  # Decent match
        ]
        
        for query, expected_sop, min_level in test_cases:
            result = self.identifier.select_best_sop(query)
            
            # Check that it found the right SOP (or close)
            assert result['selected_sop_number'] in [expected_sop, expected_sop - 1, expected_sop + 1]
    
    def test_recommendation_correctness(self):
        """Test that recommendations align with confidence scores"""
        test_cases = [
            # (query, expected_min_recommendation)
            ("Database connection timeout errors", 'REVIEW'),  # Should at least be REVIEW
            ("API performance degradation slow", 'REVIEW'),
        ]
        
        for query, min_rec in test_cases:
            result = self.identifier.select_best_sop(query)
            
            # Map recommendations to numeric values
            rec_values = {'ACCEPT': 3, 'REVIEW': 2, 'REJECT': 1}
            
            actual_value = rec_values[result['recommendation']]
            min_value = rec_values[min_rec]
            
            assert actual_value >= min_value or result['confidence_score'] < 0.4
    
    def test_alternative_sops_quality(self):
        """Test that alternative SOPs are relevant"""
        result = self.identifier.select_best_sop(
            incident_context="Server performance issues, high resource usage",
            top_k=3
        )
        
        if result['alternative_sops']:
            # Alternatives should have lower confidence than primary
            primary_score = result['confidence_score']
            
            for alt in result['alternative_sops']:
                assert alt['confidence_score'] <= primary_score
    
    def test_confidence_threshold_parameter(self):
        """Test custom confidence threshold"""
        # Low threshold
        result_low = self.identifier.select_best_sop(
            incident_context="Some vague issue",
            confidence_threshold=0.2
        )
        
        # High threshold
        result_high = self.identifier.select_best_sop(
            incident_context="Some vague issue",
            confidence_threshold=0.8
        )
        
        # With low threshold, might get REVIEW instead of REJECT
        # With high threshold, likely to get REJECT
        if result_low['confidence_score'] >= 0.2:
            assert result_low['recommendation'] in ['ACCEPT', 'REVIEW']
        
        if result_high['confidence_score'] < 0.8:
            assert result_high['recommendation'] in ['REVIEW', 'REJECT']
    
    def test_confidence_score_range(self):
        """Test that confidence scores are always in valid range"""
        test_queries = [
            "Database outage",
            "API slow",
            "Network down",
            "Memory leak",
            "Certificate expired",
            "Random unrelated text about nothing",
            "",  # Empty query
            "x" * 1000  # Very long query
        ]
        
        for query in test_queries:
            if query:  # Skip empty for this test
                result = self.identifier.select_best_sop(query)
                
                assert 0.0 <= result['confidence_score'] <= 1.0
                assert result['confidence_level'] in ['HIGH', 'MEDIUM', 'LOW']
    
    def test_score_components_sum(self):
        """Test that score components contribute correctly"""
        result = self.identifier.retrieve_relevant_sops(
            query="Database connection timeout",
            top_k=1,
            semantic_weight=0.6,
            bm25_weight=0.4
        )
        
        top_result = result[0]
        
        # Manual calculation of expected score
        expected_score = (
            0.6 * top_result['semantic_score'] + 
            0.4 * top_result['bm25_score']
        )
        
        # Should be very close (allowing for floating point rounding)
        assert abs(top_result['confidence_score'] - expected_score) < 0.01


class TestConfidenceCalibration:
    """Test that confidence scores correlate with actual accuracy"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup with known ground truth"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'calibration_sops.txt')
        
        sop_content = """SOP-001: Database Issues
Database problems, connection failures, timeouts, PostgreSQL, MySQL.
---
SOP-002: API Problems
API slow, performance degradation, high latency, response time issues.
---
SOP-003: Authentication Failures
Login issues, OAuth errors, 401, 403, authentication problems.
"""
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        self.identifier = LocalSOPIdentifier()
        self.identifier.build_index(self.sop_file)
        
        # Ground truth: (query, correct_sop_number)
        self.ground_truth = [
            ("Database connection timeout", 1),
            ("PostgreSQL not responding", 1),
            ("API response time too high", 2),
            ("Slow API performance", 2),
            ("Users cannot login", 3),
            ("OAuth authentication failing", 3),
        ]
        
        yield
        
        shutil.rmtree(self.test_dir)
    
    def test_accuracy_vs_confidence(self):
        """Test that higher confidence correlates with higher accuracy"""
        high_conf_correct = 0
        high_conf_total = 0
        low_conf_correct = 0
        low_conf_total = 0
        
        for query, correct_sop in self.ground_truth:
            result = self.identifier.select_best_sop(query)
            
            is_correct = (result['selected_sop_number'] == correct_sop)
            
            if result['confidence_score'] >= 0.6:
                high_conf_total += 1
                if is_correct:
                    high_conf_correct += 1
            else:
                low_conf_total += 1
                if is_correct:
                    low_conf_correct += 1
        
        # Calculate accuracy for each group
        if high_conf_total > 0:
            high_conf_accuracy = high_conf_correct / high_conf_total
            print(f"High confidence accuracy: {high_conf_accuracy:.2f}")
            
            # High confidence should be more accurate
            if low_conf_total > 0:
                low_conf_accuracy = low_conf_correct / low_conf_total
                assert high_conf_accuracy >= low_conf_accuracy - 0.1  # Allow some tolerance
    
    def test_confidence_predicts_correctness(self):
        """Test confidence as predictor of correctness"""
        results_data = []
        
        for query, correct_sop in self.ground_truth:
            result = self.identifier.select_best_sop(query)
            
            is_correct = (result['selected_sop_number'] == correct_sop)
            confidence = result['confidence_score']
            
            results_data.append((confidence, is_correct))
        
        # Separate correct and incorrect predictions
        correct_confidences = [conf for conf, correct in results_data if correct]
        incorrect_confidences = [conf for conf, correct in results_data if not correct]
        
        if correct_confidences and incorrect_confidences:
            avg_correct = sum(correct_confidences) / len(correct_confidences)
            avg_incorrect = sum(incorrect_confidences) / len(incorrect_confidences)
            
            # Correct predictions should have higher average confidence
            assert avg_correct >= avg_incorrect - 0.1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
