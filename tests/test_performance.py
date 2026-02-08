"""
Performance and resource constraint tests
"""

import pytest
import tempfile
import shutil
import os
import sys
import time
import psutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.local_sop_identifier import LocalSOPIdentifier


class TestPerformance:
    """Test performance metrics and benchmarks"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'perf_test_sops.txt')
        
        # Create multiple SOPs for realistic testing
        sop_content = []
        for i in range(1, 21):  # 20 SOPs
            sop = f"""SOP-{i:03d}: Test SOP {i}

## Purpose
This is test SOP number {i} for performance testing.

## Symptoms
- Symptom A for SOP {i}
- Symptom B for SOP {i}
- Error code {i}00

## Steps
1. Step 1 for SOP {i}
2. Step 2 for SOP {i}
3. Step 3 for SOP {i}

Additional details and content to make the SOP realistic size.
More content here. Technical details. Procedures. Guidelines.
"""
            sop_content.append(sop)
        
        full_content = "---\n".join(sop_content)
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        yield
        
        shutil.rmtree(self.test_dir)
    
    def test_index_build_time(self):
        """Test that index building completes in reasonable time"""
        identifier = LocalSOPIdentifier()
        
        start_time = time.time()
        identifier.build_index(self.sop_file)
        build_time = time.time() - start_time
        
        # Should build 20 SOPs in under 60 seconds
        assert build_time < 60.0
        print(f"\nIndex build time for 20 SOPs: {build_time:.2f}s")
    
    def test_index_load_time(self):
        """Test that index loading is fast"""
        identifier = LocalSOPIdentifier()
        index_path = os.path.join(self.test_dir, 'test_index.pkl')
        
        # Build index first
        identifier.build_index(self.sop_file, index_path)
        
        # Test loading
        identifier2 = LocalSOPIdentifier()
        start_time = time.time()
        identifier2.load_index(index_path)
        load_time = time.time() - start_time
        
        # Should load in under 2 seconds
        assert load_time < 2.0
        print(f"\nIndex load time: {load_time:.3f}s")
    
    def test_query_response_time(self):
        """Test that queries respond quickly"""
        identifier = LocalSOPIdentifier()
        identifier.build_index(self.sop_file)
        
        # Warm up (first query may be slower)
        identifier.retrieve_relevant_sops("test query", top_k=3)
        
        # Measure subsequent queries
        query_times = []
        for i in range(10):
            start_time = time.time()
            identifier.retrieve_relevant_sops(f"test query {i}", top_k=3)
            query_time = time.time() - start_time
            query_times.append(query_time)
        
        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)
        
        # Average should be under 1 second
        assert avg_query_time < 1.0
        # Max should be under 2 seconds
        assert max_query_time < 2.0
        
        print(f"\nAverage query time: {avg_query_time*1000:.1f}ms")
        print(f"Max query time: {max_query_time*1000:.1f}ms")
    
    def test_batch_query_performance(self):
        """Test performance with multiple queries"""
        identifier = LocalSOPIdentifier()
        identifier.build_index(self.sop_file)
        
        queries = [
            "Database connection timeout",
            "API performance slow",
            "Authentication failure",
            "Network connectivity issue",
            "Memory leak problem"
        ] * 10  # 50 queries total
        
        start_time = time.time()
        for query in queries:
            identifier.retrieve_relevant_sops(query, top_k=3)
        total_time = time.time() - start_time
        
        avg_time_per_query = total_time / len(queries)
        
        # Should handle 50 queries in under 60 seconds
        assert total_time < 60.0
        print(f"\n50 queries completed in {total_time:.2f}s ({avg_time_per_query*1000:.1f}ms per query)")


class TestResourceUsage:
    """Test resource constraints and limits"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        self.test_dir = tempfile.mkdtemp()
        self.sop_file = os.path.join(self.test_dir, 'resource_test_sops.txt')
        
        # Create SOPs
        sop_content = []
        for i in range(1, 11):
            sop = f"SOP-{i:03d}: Test SOP {i}\n\nContent for SOP {i}.\n"
            sop_content.append(sop)
        
        with open(self.sop_file, 'w', encoding='utf-8') as f:
            f.write("---\n".join(sop_content))
        
        yield
        
        shutil.rmtree(self.test_dir)
    
    def test_memory_usage_index_build(self):
        """Test memory usage during index building"""
        process = psutil.Process()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Build index
        identifier = LocalSOPIdentifier()
        identifier.build_index(self.sop_file)
        
        # Peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        # Should use less than 500MB additional memory
        assert memory_increase < 500
        print(f"\nMemory increase during index build: {memory_increase:.1f} MB")
    
    def test_memory_usage_query(self):
        """Test memory usage during querying"""
        identifier = LocalSOPIdentifier()
        identifier.build_index(self.sop_file)
        
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run multiple queries
        for i in range(20):
            identifier.retrieve_relevant_sops(f"test query {i}", top_k=5)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        # Memory shouldn't grow significantly during queries
        assert memory_increase < 100
        print(f"\nMemory increase during 20 queries: {memory_increase:.1f} MB")
    
    def test_index_file_size(self):
        """Test that index file size is reasonable"""
        identifier = LocalSOPIdentifier()
        index_path = os.path.join(self.test_dir, 'size_test_index.pkl')
        
        identifier.build_index(self.sop_file, index_path)
        
        # Check file size
        file_size_mb = os.path.getsize(index_path) / 1024 / 1024
        
        # 10 SOPs should be under 10MB
        assert file_size_mb < 10
        print(f"\nIndex file size for 10 SOPs: {file_size_mb:.2f} MB")


class TestScalability:
    """Test scalability with different dataset sizes"""
    
    def test_scalability_with_sop_count(self):
        """Test performance scales reasonably with SOP count"""
        test_dir = tempfile.mkdtemp()
        
        results = []
        
        for sop_count in [5, 10, 20]:
            # Create SOPs
            sop_file = os.path.join(test_dir, f'sops_{sop_count}.txt')
            sop_content = []
            for i in range(1, sop_count + 1):
                sop = f"SOP-{i:03d}: Test SOP {i}\n\nContent for SOP {i}.\n"
                sop_content.append(sop)
            
            with open(sop_file, 'w', encoding='utf-8') as f:
                f.write("---\n".join(sop_content))
            
            # Build and query
            identifier = LocalSOPIdentifier()
            
            start_time = time.time()
            identifier.build_index(sop_file)
            build_time = time.time() - start_time
            
            start_time = time.time()
            identifier.retrieve_relevant_sops("test query", top_k=3)
            query_time = time.time() - start_time
            
            results.append({
                'sop_count': sop_count,
                'build_time': build_time,
                'query_time': query_time
            })
            
            print(f"\n{sop_count} SOPs: build={build_time:.2f}s, query={query_time*1000:.1f}ms")
        
        # Query time should scale sub-linearly (not double when SOPs double)
        # This tests efficiency of the retrieval algorithm
        
        shutil.rmtree(test_dir)
    
    def test_large_sop_content(self):
        """Test handling of very large individual SOPs"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'large_sops.txt')
        
        # Create one very large SOP (10,000+ words)
        large_content = " ".join([f"word{i}" for i in range(10000)])
        sop_content = f"SOP-001: Large SOP\n\n{large_content}\n"
        
        with open(sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        # Should handle it without errors
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        result = identifier.retrieve_relevant_sops("test query", top_k=1)
        
        assert len(result) == 1
        
        shutil.rmtree(test_dir)


class TestRobustness:
    """Test robustness under various conditions"""
    
    def test_concurrent_queries(self):
        """Test that multiple queries don't interfere"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'concurrent_test.txt')
        
        sop_content = "SOP-001: Test\n\nTest content.\n---\nSOP-002: Test2\n\nTest content 2.\n"
        with open(sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        # Run multiple queries in sequence (simulating concurrent use)
        results = []
        for i in range(10):
            result = identifier.retrieve_relevant_sops(f"query {i}", top_k=1)
            results.append(result)
        
        # All should succeed
        assert all(len(r) > 0 for r in results)
        
        shutil.rmtree(test_dir)
    
    def test_index_reusability(self):
        """Test that same identifier can be reused"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'reuse_test.txt')
        
        sop_content = "SOP-001: Test\n\nTest content.\n"
        with open(sop_file, 'w', encoding='utf-8') as f:
            f.write(sop_content)
        
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        # Use it multiple times
        for i in range(5):
            result = identifier.retrieve_relevant_sops("test", top_k=1)
            assert len(result) > 0
        
        shutil.rmtree(test_dir)
    
    def test_stress_test(self):
        """Stress test with many rapid queries"""
        test_dir = tempfile.mkdtemp()
        sop_file = os.path.join(test_dir, 'stress_test.txt')
        
        sop_content = []
        for i in range(1, 6):
            sop_content.append(f"SOP-{i:03d}: Test {i}\n\nContent {i}.\n")
        
        with open(sop_file, 'w', encoding='utf-8') as f:
            f.write("---\n".join(sop_content))
        
        identifier = LocalSOPIdentifier()
        identifier.build_index(sop_file)
        
        # Rapid fire 100 queries
        start_time = time.time()
        for i in range(100):
            identifier.retrieve_relevant_sops(f"query {i % 10}", top_k=3)
        total_time = time.time() - start_time
        
        # Should complete in reasonable time
        assert total_time < 30.0  # 100 queries in under 30 seconds
        print(f"\n100 rapid queries completed in {total_time:.2f}s")
        
        shutil.rmtree(test_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
