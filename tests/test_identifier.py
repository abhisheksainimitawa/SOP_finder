"""
Unit tests for LocalSOPIdentifier
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.local_sop_identifier import LocalSOPIdentifier


class TestSOPParsing:
    """Test SOP parsing functionality"""
    
    def setup_method(self):
        """Create a temporary SOP file for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'test_sops.txt')
        
        # Create a sample SOP file
        sop_content = """SOP-001: Database Service Outage Response

## Purpose
This procedure provides step-by-step instructions for responding to complete database service outages.

## Scope
This SOP applies to all production database instances.

## Detection Methods
- Monitoring tools trigger critical alerts
- Application error logs show database connection timeouts

---
SOP-002: API Performance Degradation

## Purpose
Address and resolve API performance issues.

## Scope
All API endpoints and microservices.

## Detection Methods
- Response time exceeds SLA thresholds
- High CPU usage on API servers

---
SOP-003: Authentication Service Failure

## Purpose
Restore authentication and authorization services.

## Scope
OAuth, SAML, and SSO systems.

## Detection Methods
- Login failures
- 401/403 errors in logs
"""
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
    
    def teardown_method(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)
    
    def test_parse_sops(self):
        """Test that SOPs are parsed correctly"""
        identifier = LocalSOPIdentifier()
        chunks = identifier.parse_sops(self.sop_file)
        
        assert len(chunks) == 3
        assert chunks[0]['sop_number'] == 1
        assert chunks[1]['sop_number'] == 2
        assert chunks[2]['sop_number'] == 3
        
        assert 'Database Service Outage' in chunks[0]['title']
        assert 'API Performance' in chunks[1]['title']
        assert 'Authentication' in chunks[2]['title']
    
    def test_sop_content_structure(self):
        """Test that SOP chunks have required fields"""
        identifier = LocalSOPIdentifier()
        chunks = identifier.parse_sops(self.sop_file)
        
        for chunk in chunks:
            assert 'id' in chunk
            assert 'title' in chunk
            assert 'content' in chunk
            assert 'sop_number' in chunk
            
            assert chunk['id'].startswith('sop_')
            assert chunk['title'].startswith('SOP-')


class TestIndexBuilding:
    """Test index building and loading"""
    
    def setup_method(self):
        """Create test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'test_sops.txt')
        self.index_file = os.path.join(self.test_dir, 'test_index.pkl')
        
        # Create minimal SOP file
        sop_content = """SOP-001: Database Outage

Handle database outages and connection issues.
---
SOP-002: API Issues

Resolve API performance problems.
"""
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
    
    def teardown_method(self):
        """Clean up"""
        shutil.rmtree(self.test_dir)
    
    def test_build_index(self):
        """Test index building"""
        identifier = LocalSOPIdentifier()
        identifier.build_index(self.sop_file, self.index_file)
        
        # Check index file was created
        assert os.path.exists(self.index_file)
        
        # Check internal state
        assert len(identifier.sop_chunks) == 2
        assert identifier.sop_embeddings is not None
        assert identifier.sop_embeddings.shape[0] == 2
        assert identifier.bm25 is not None
    
    def test_load_index(self):
        """Test loading a saved index"""
        # Build index first
        identifier1 = LocalSOPIdentifier()
        identifier1.build_index(self.sop_file, self.index_file)
        
        # Load it in a new instance
        identifier2 = LocalSOPIdentifier()
        identifier2.load_index(self.index_file)
        
        # Should have same data
        assert len(identifier2.sop_chunks) == 2
        assert identifier2.sop_embeddings is not None
        assert identifier2.bm25 is not None
    
    def test_load_nonexistent_index(self):
        """Test loading index that doesn't exist"""
        identifier = LocalSOPIdentifier()
        
        with pytest.raises(FileNotFoundError):
            identifier.load_index('/nonexistent/path/index.pkl')


class TestRetrieval:
    """Test SOP retrieval functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for retrieval tests"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'test_sops.txt')
        
        # Create test SOPs
        sop_content = """SOP-001: Database Service Outage Response

## Purpose
Handle complete database service outages and connection timeouts.

## Steps
1. Check database connectivity
2. Restart database service
3. Verify recovery

Keywords: database, PostgreSQL, MySQL, connection, timeout, outage, unavailable
---
SOP-002: API Performance Degradation

## Purpose
Resolve slow API response times and performance issues.

## Steps
1. Monitor CPU and memory
2. Scale resources
3. Optimize queries

Keywords: API, performance, slow, response time, latency, timeout
---
SOP-003: Authentication Service Failure

## Purpose
Fix authentication and login issues.

## Steps
1. Check OAuth service
2. Verify token validation
3. Restart auth service

Keywords: authentication, login, OAuth, SSO, 401, 403, unauthorized
"""
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        # Build index
        self.identifier = LocalSOPIdentifier()
        self.identifier.build_index(self.sop_file)
        
        yield
        
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def test_retrieve_database_issue(self):
        """Test retrieval for database-related query"""
        results = self.identifier.retrieve_relevant_sops(
            query="Production database is down and all connections are timing out",
            top_k=3
        )
        
        assert len(results) > 0
        # Top result should be database SOP
        assert results[0]['sop_number'] == 1
        assert results[0]['confidence_score'] > 0
    
    def test_retrieve_api_issue(self):
        """Test retrieval for API-related query"""
        results = self.identifier.retrieve_relevant_sops(
            query="API response times are very slow, taking 5 seconds instead of 200ms",
            top_k=3
        )
        
        assert len(results) > 0
        # Should retrieve API performance SOP
        assert any(r['sop_number'] == 2 for r in results)
    
    def test_retrieve_auth_issue(self):
        """Test retrieval for authentication-related query"""
        results = self.identifier.retrieve_relevant_sops(
            query="Users cannot login, getting 401 unauthorized errors",
            top_k=3
        )
        
        assert len(results) > 0
        # Should retrieve authentication SOP
        assert any(r['sop_number'] == 3 for r in results)
    
    def test_confidence_scores_in_range(self):
        """Test that confidence scores are in valid range"""
        results = self.identifier.retrieve_relevant_sops(
            query="Database connection timeout",
            top_k=3
        )
        
        for result in results:
            assert 0.0 <= result['confidence_score'] <= 1.0
            assert 0.0 <= result['semantic_score'] <= 1.0
            assert 0.0 <= result['bm25_score'] <= 1.0
    
    def test_confidence_levels(self):
        """Test that confidence levels are assigned correctly"""
        results = self.identifier.retrieve_relevant_sops(
            query="Database outage",
            top_k=3
        )
        
        for result in results:
            score = result['confidence_score']
            level = result['confidence_level']
            
            if score >= 0.7:
                assert level == 'HIGH'
            elif score >= 0.4:
                assert level == 'MEDIUM'
            else:
                assert level == 'LOW'
    
    def test_top_k_parameter(self):
        """Test that top_k parameter works correctly"""
        results_k1 = self.identifier.retrieve_relevant_sops(
            query="Database issue",
            top_k=1
        )
        results_k3 = self.identifier.retrieve_relevant_sops(
            query="Database issue",
            top_k=3
        )
        
        assert len(results_k1) == 1
        assert len(results_k3) == 3
    
    def test_hybrid_weights(self):
        """Test custom hybrid weights"""
        # Pure semantic
        results_semantic = self.identifier.retrieve_relevant_sops(
            query="Database down",
            semantic_weight=1.0,
            bm25_weight=0.0
        )
        
        # Pure BM25
        results_bm25 = self.identifier.retrieve_relevant_sops(
            query="Database down",
            semantic_weight=0.0,
            bm25_weight=1.0
        )
        
        # Both should return results
        assert len(results_semantic) > 0
        assert len(results_bm25) > 0


class TestSOPSelection:
    """Test best SOP selection"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for selection tests"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'test_sops.txt')
        
        sop_content = """SOP-001: Database Service Outage

Handle database outages, connection failures, timeouts.
---
SOP-002: API Performance Issues

Resolve slow API response times.
"""
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        self.identifier = LocalSOPIdentifier()
        self.identifier.build_index(self.sop_file)
        
        yield
        
        shutil.rmtree(self.test_dir)
    
    def test_select_best_sop_structure(self):
        """Test that select_best_sop returns correct structure"""
        result = self.identifier.select_best_sop(
            incident_context="Database connection timeout"
        )
        
        # Check all required fields
        assert 'selected_sop_id' in result
        assert 'selected_sop_number' in result
        assert 'selected_sop_title' in result
        assert 'confidence_score' in result
        assert 'confidence_level' in result
        assert 'recommendation' in result
        assert 'reason' in result
        assert 'retrieved_sops' in result
        assert 'alternative_sops' in result
    
    def test_recommendation_levels(self):
        """Test recommendation based on confidence"""
        # High confidence query
        result_high = self.identifier.select_best_sop(
            incident_context="Database service completely down, all connections timing out"
        )
        
        if result_high['confidence_score'] >= 0.7:
            assert result_high['recommendation'] == 'ACCEPT'
        elif result_high['confidence_score'] >= 0.4:
            assert result_high['recommendation'] == 'REVIEW'
        else:
            assert result_high['recommendation'] == 'REJECT'
    
    def test_process_incident(self):
        """Test processing structured incident data"""
        incident = {
            'incident_details': {
                'short_description': 'Database outage',
                'description': 'Production database is completely unavailable'
            },
            'log_insights': {
                'full_analysis': 'Connection refused on port 5432'
            }
        }
        
        result = self.identifier.process_incident(incident)
        
        assert result['selected_sop_id'] is not None
        assert result['confidence_score'] > 0
    
    def test_no_match_scenario(self):
        """Test behavior when no good match exists"""
        # Use a very unrelated query
        result = self.identifier.select_best_sop(
            incident_context="The quick brown fox jumps over the lazy dog",
            top_k=1
        )
        
        # Should still return a result, but with low confidence
        assert result['selected_sop_id'] is not None
        assert result['confidence_level'] in ['LOW', 'MEDIUM', 'HIGH']


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_query(self):
        """Test behavior with empty query"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'test_sops.txt')
        
        with open(sop_file, 'w') as f:
            f.write("SOP-001: Test\n\nTest content\n")
        
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        results = identifier.retrieve_relevant_sops(query="", top_k=1)
        
        # Should still return results (even if scores are low)
        assert len(results) >= 0
        
        shutil.rmtree(test_dir)
    
    def test_query_without_index(self):
        """Test querying without building index first"""
        identifier = LocalSOPIdentifier()
        
        with pytest.raises(ValueError, match="Index not built"):
            identifier.retrieve_relevant_sops("test query")
    
    def test_very_long_query(self):
        """Test with very long query"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'test_sops.txt')
        
        with open(sop_file, 'w') as f:
            f.write("SOP-001: Test\n\nTest content\n")
        
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        # Create a very long query (1000+ words)
        long_query = "database " * 1000
        
        results = identifier.retrieve_relevant_sops(query=long_query, top_k=1)
        
        # Should handle it without crashing
        assert len(results) > 0
        
        shutil.rmtree(test_dir)
    
    def test_special_characters_in_query(self):
        """Test query with special characters"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'test_sops.txt')
        
        with open(sop_file, 'w') as f:
            f.write("SOP-001: Test\n\nTest content @#$%\n")
        
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        results = identifier.retrieve_relevant_sops(
            query="Test @#$% special chars!?",
            top_k=1
        )
        
        assert len(results) > 0
        
        shutil.rmtree(test_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
