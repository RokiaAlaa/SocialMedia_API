import pytest
from fastapi import status

class TestUserProfiles:
    """Test user profile endpoints"""

    def test_get_user_profile(self, client, test_user):
        """Test getting user profile"""

        response = client.get(f'/api/v1/users/{test_user.username}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['username'] == test_user.username
        assert data['email'] == test_user.email
        assert 'posts_count' in data
        assert 'followers_count' in data
        assert 'following_count' in data

    def test_get_nonexistent_user(self, client):
        """Test getting non-existent user profile"""

        response = client.get('/api/v1/users/nonexistent')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_own_profile(self, client, test_user, user_headers):
        """Test updating own profile"""

        response = client.put(
            f'/api/v1/users/{test_user.username}',
            headers=user_headers,
            json={
                'full_name': "New Name",
                'bio': 'New bio'
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['full_name'] == "New Name"
        assert data['bio'] == 'New bio'

    def test_update_password(self, client, test_user, user_headers):
        """Test password update"""

        response = client.put(
            f'/api/v1/users/{test_user.username}',
            headers=user_headers,
            json={'password': 'newpassword123'}
        )

        assert response.status_code == status.HTTP_200_OK

        response = client.post(
            '/api/v1/auth/login',
            data={
                'username': test_user.email,
                'password': 'newpassword123'
            }
        )

        assert response.status_code == status.HTTP_200_OK

        response = client.post(
            '/api/v1/auth/login',
            data={
                'username': test_user.email,
                'password': 'testpass123'
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_other_user_profile_forbidden(self, client, test_user, test_user2, user_headers):
        """Test updating another user's profile (should fail)"""

        response = client.put(
            f'/api/v1/users/{test_user2.username}',
            headers=user_headers,
            json={'full_name': "Hacked Name"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_profile_shows_follow_status(self, client, test_user, test_user2, user_headers, db):
        """Test profile shows is_following for authenticated user"""

        from app.models.follow import Follow
        follow = Follow(follower_id=test_user.id, following_id=test_user2.id)
        db.add(follow)
        db.commit()

        response = client.get(
            f'/api/v1/users/{test_user2.username}',
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK 
        data = response.json()
        assert data['is_following'] == True