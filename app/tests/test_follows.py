import pytest
from fastapi import status

class TestFollowSystem:
    """Test follow/unfollow functionality"""
    
    def test_follow_user(self, client, test_user2, user_headers):
        """Test following a user"""

        response = client.post(
            f'/api/v1/users/{test_user2.username}/follow',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['is_following'] == True
        assert data['followers_count'] == 1

    def test_follow_self_forbidden(self, client, test_user, user_headers):
        """Test that user cannot follow themselves"""

        response = client.post(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'cannot follow yourself' in data['detail'].lower()

    def test_follow_already_following(self, client, test_user2, user_headers):
        """Test following user already followed"""

        client.post(
            f'/api/v1/users/{test_user2.username}/follow',
            headers=user_headers
        )

        response = client.post(
            f'/api/v1/users/{test_user2.username}/follow',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'already following' in data['detail'].lower()

    def test_follow_nonexistent_user(self, client, user_headers):
        """Test following non-existent user"""

        response = client.post(
            f'/api/v1/users/nonexistent/follow',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unfollow_user(self, client, test_user2, user_headers):
        """Test unfollowing a user"""

        client.post(
            f'/api/v1/users/{test_user2.username}/follow',
            headers=user_headers
        )

        response = client.delete(
            f'/api/v1/users/{test_user2.username}/follow',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_following'] == False

    def test_unfollow_not_following(self, client, test_user2, user_headers):
        """Test unfollowing user not followed"""

        response = client.delete(
            f'/api/v1/users/{test_user2.username}/follow',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_followers(self, client, test_user, test_user2, user2_headers):
        """Test getting user's followers"""

        client.post(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user2_headers
        )

        response = client.get(f'/api/v1/users/{test_user.username}/followers')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['username'] == test_user2.username

    def test_get_following(self, client, test_user, test_user2, user2_headers):
        """Test getting users that user follows"""

        client.post(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user2_headers
        )

        response = client.get(f'/api/v1/users/{test_user2.username}/following')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['username'] == test_user.username
    
    def test_follow_affects_profile_stats(self, client, test_user, test_user2, user2_headers):
        """Test that following updates profile counts"""

        client.post(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user2_headers
        )

        response = client.get(f'/api/v1/users/{test_user2.username}')
        data = response.json()
        assert data['following_count'] == 1


        response = client.get(f'/api/v1/users/{test_user.username}')
        data = response.json()
        assert data['followers_count'] == 1