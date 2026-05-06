import pytest
from fastapi import status

class TestAuthentication:
    """Test authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""

        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'newuser@example.com',
                'username': 'newuser',
                'full_name': 'New User',
                'password': 'password123'
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['email'] == 'newuser@example.com'
        assert data['username'] == 'newuser'
        assert 'hashed_password'not in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""

        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': test_user.email,
                'username': 'different', 
                'password': 'password123'
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'already registered' in data['detail'].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""

        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'different@example.com',
                'username': test_user.username, 
                'password': 'password123'
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'already taken' in data['detail'].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""

        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'notanemail',
                'username': 'testuser',
                'password': 'password123'
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT 

    def test_register_short_password(self, client):
        """Test registration with short password"""

        response = client.post(
            '/api/v1/auth/register',
            json={
                'email': 'test@example.com',
                'username': 'testuser',
                'password': '123'
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT 

    def test_login_success(self, client, test_user):
        """Test successful login"""

        response = client.post(
            '/api/v1/auth/login',
            data={ 
                'username': test_user.email,
                'password': 'testpass123'
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'

    def test_login_with_username(self, client, test_user):
        """Test login with username instead of email"""

        response = client.post(
            '/api/v1/auth/login',
            data={ 
                'username': test_user.username,
                'password': 'testpass123'
            }
        )

        assert response.status_code == status.HTTP_200_OK

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""

        response = client.post(
            '/api/v1/auth/login',
            data={ 
                'username': test_user.email,
                'password': 'wrongpassword'
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""

        response = client.post(
            '/api/v1/auth/login',
            data={ 
                'username': 'nonexistent@example.com',
                'password': 'password123'
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user(self, client, test_user, user_headers):
        """Test getting current user profile"""

        response = client.get('/api/v1/auth/me', headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['email'] == test_user.email
        assert data['username'] == test_user.username

    def test_get_current_user_unauthorized(self, client):
        """Test getting profile without token"""

        response = client.get('/api/v1/auth/me')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Test getting profile with invalid token"""
        headers = {'Authorization': "Bearer invalid_token_here"}
        response = client.get('/api/v1/auth/me', headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile(self, client, test_user, user_headers):
        """Test updating user profile"""

        response = client.put(
            '/api/v1/auth/me',
            headers=user_headers,
            json={ 
                'full_name': 'Updated Name',
                'bio': 'Updated bio'
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['full_name'] == 'Updated Name'
        assert data['bio'] == 'Updated bio'

    def test_update_password(self, client, test_user, user_headers):
        """Test password update"""

        response = client.put(
            '/api/v1/auth/me',
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