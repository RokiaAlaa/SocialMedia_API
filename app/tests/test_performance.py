import pytest
import time
from fastapi import status

class TestPerformance:
    """Basic performance tests"""

    def test_list_posts_response_time(self, client, user_headers):
        """Test posts listing response time"""

        for i in range(100):
            client.post(
                '/api/v1/posts',
                headers=user_headers,
                json={'content': f'Post {i}'}
            )

        start = time.time()
        response = client.get('/api/v1/posts?limit=20')
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        assert duration < 0.5 ##

    def test_get_post_with_stats_performance(self, client, user_headers, test_post):
        """Test single post retrieval with stats"""

        for i in range(30):
            response = client.post(
                f'/api/v1/posts/{test_post.id}/comments',
                headers=user_headers,
                json={'content': 'Test Comment'}
            )

        start = time.time()
        response = client.get(f'/api/v1/posts/{test_post.id}')
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        assert duration < 0.3 