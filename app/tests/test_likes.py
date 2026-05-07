import pytest
from fastapi import status

class TestLikes:
    """Test like/reaction endpoints"""

    def test_like_post(self, client, test_post, user_headers):
        """Test liking a post"""
        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'like'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['post_id'] == test_post.id
        assert data['reaction_type'] == 'like'

    def test_like_post_unauthorized(self, client, test_post):
        """Test liking without auth"""
        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            json={'reaction_type': 'like'}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_reaction_type(self, client, test_post, user_headers):
        """Test changing reaction type"""
        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'like'}
        )

        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'love'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['reaction_type'] == 'love'

    def test_unlike_post(self, client, test_post, user_headers):
        """Test unliking a post"""

        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'like'}
        )

        response = client.delete(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_post_likes(self, client, test_post, user_headers):
        """Test getting post likes"""

        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'like'}
        )

        response = client.get(f'/api/v1/posts/{test_post.id}/likes')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_likes'] > 0
        assert 'reactions' in data

    def test_post_enrichment_includes_like_status(self, client, test_post, user_headers):
        """Test that post includes user's like status"""

        client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'like'}
        )

        response = client.get(
            f'/api/v1/posts/{test_post.id}',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_liked'] == True