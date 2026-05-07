import pytest
from fastapi import status

class TestComments:
    """Test comment endpoints"""

    def test_get_post_comments(self, client, test_post):
        """Test getting post comments"""
        response = client.get(f'/api/v1/posts/{test_post.id}/comments')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_create_comment(self, client, test_post, user_headers):
        """Test creating comment"""
        response = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user_headers,
            json={'content': 'Test Comment'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['content'] == 'Test Comment'
        assert data['post_id'] == test_post.id

    def test_create_comment_unauthorized(self, client, test_post):
        """Test creating comment without auth"""
        response = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            json={'content': 'Test'}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
  
    def test_create_comment_nonexistent_post(self, client, user_headers):
        """Test commenting on non-existent post"""
        response = client.post(
            '/api/v1/posts/99999/comments',
            headers=user_headers,
            json={'content': 'Test'}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reply_to_comment(self, client, test_post, user_headers):
        """Test replying to a comment"""
        parent = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user_headers,
            json={'content': 'Parent Comment'}
        )
        parent = parent.json()

        response = client.post(
            f'/api/v1/comments/{parent['id']}/reply',
            headers=user_headers,
            json={'content': 'Reply comment'}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['parent_id'] == parent['id']
        assert data['content'] == 'Reply comment'

    def test_update_own_comment(self, client, test_post, user_headers):
        """Test updating own comment"""
        comment = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user_headers,
            json={'content': 'Original'}
        )
        comment = comment.json()


        response = client.put(
            f'/api/v1/comments/{comment['id']}',
            headers=user_headers,
            json={'content': 'updated'}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['content'] == 'updated'

    def test_delete_own_comment(self, client, test_post, user_headers): 
        comment = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user_headers,
            json={'content': 'To delete'}
        )
        comment = comment.json()


        response = client.delete(
            f'/api/v1/comments/{comment['id']}',
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_nested_replies_structure(self, client, test_post, user_headers):
        """Test nested comment structure"""

        parent = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user_headers,
            json={'content': 'Parent Comment'}
        )
        parent = parent.json()

        reply = client.post(
            f'/api/v1/comments/{parent['id']}/reply',
            headers=user_headers,
            json={'content': 'Reply comment'}
        )


        response = client.get(f'/api/v1/posts/{test_post.id}/comments')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        parent_comment = next(c for c in data if c['id'] == parent['id'])
        assert len(parent_comment['replies']) > 0