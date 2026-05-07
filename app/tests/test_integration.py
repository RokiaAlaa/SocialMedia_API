import pytest
from fastapi import status

class TestCompleteUserFlow:
    """Test complete user journey"""

    def test_new_user_complete_flow(self, client):
        """Test complete flow from registration to creating content"""

        # 1. Register
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

        # 2. Login
        response = client.post(
            '/api/v1/auth/login',
            data={ 
                'username': 'newuser@example.com',
                'password': 'password123'
            }
        )
        assert response.status_code == status.HTTP_200_OK
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # 3. Update profile
        response = client.put(
            '/api/v1/users/newuser',
            headers=headers,
            json={'bio': 'Updated bio'}
        )

        assert response.status_code == status.HTTP_200_OK

        # 4. Create post
        response = client.post(
            '/api/v1/posts',
            headers=headers,
            json={
                'content': 'New test post',
                'tag_names': ['test', 'python']
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        post_data = response.json()
        post_id = post_data['id']

        # 5. View own post
        response = client.get(f'/api/v1/posts/{post_id}', headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # 6. Edit post
        response = client.put(
            f'/api/v1/posts/{post_id}',
            headers=headers,
            json={'content': 'updated content'}
        )

        assert response.status_code == status.HTTP_200_OK

        # 7. View posts in feed
        response = client.get(f'/api/v1/posts/feed', headers=headers)
        assert response.status_code == status.HTTP_200_OK

    def test_social_interaction_flow(self, client, test_user, test_post, user2_headers):
        """Test social interactions between users"""

        # 1. User2 views user1's profile
        response = client.get(f'/api/v1/users/{test_user.username}')
        assert response.status_code == status.HTTP_200_OK

        # 2. User2 follows user1
        response = client.post(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user2_headers
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 3. User2 likes user1's post
        response = client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user2_headers,
            json={'reaction_type': 'like'}
        )

        assert response.status_code == status.HTTP_201_CREATED

        # 4. User2 comments on user1's post
        response = client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user2_headers,
            json={'content': 'Test Comment'}
        )

        assert response.status_code == status.HTTP_201_CREATED

        # 5. User2 views user1's post
        response = client.get(f'/api/v1/posts/{test_post.id}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['is_liked'] == True
        assert data['likes_count'] > 0
        assert data['comments_count'] > 0

        # 6. User2 views feed
        response = client.get(f'/api/v1/posts/feed', headers=user2_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        post_ids = [p['id'] for p in data]
        assert test_post.id in post_ids

    def test_content_discovery_flow(self, client, test_post, test_tag, db):
        """Test content discovery through tags and search"""
        
        test_post.tags.append(test_tag)
        db.commit()

        # 1. Search by content
        response = client.get('/api/v1/posts?search=Test') 
        assert response.status_code == status.HTTP_200_OK

        # 2. Browse by tag
        response = client.get(f'/api/v1/posts?tag={test_tag.slug}') 
        assert response.status_code == status.HTTP_200_OK

        # 3. view trending tags
        response = client.get(f'/api/v1/tags/trending') 
        assert response.status_code == status.HTTP_200_OK

        # 4. view posts by tag directly
        response = client.get(f'/api/v1/tags/{test_tag.slug}/posts') 
        assert response.status_code == status.HTTP_200_OK

class TestDataConsistency:
    """Test data consistency across operations"""

    def test_delete_user_cascades(self, client, test_user, user_headers, test_post, db):
        """Test that deleting user removes related data"""
        from app.models.post import Post

        response = client.delete(
            f'/api/v1/users/{test_user.username}',
            headers=user_headers,
        )       
        assert response.status_code == status.HTTP_204_NO_CONTENT

        db.refresh(test_user)

        assert test_user.is_active == False
        assert db.query(Post).filter(Post.id == test_post.id).count() == 0

    def test_delete_post_cascades(self, client, user_headers, test_post, db):
        """Test that deleting post removes comments and likes"""
        from app.models.comment import Comment
        from app.models.like import Like

        client.post(
            f'/api/v1/posts/{test_post.id}/comments',
            headers=user_headers,
            json={'content': 'Test Comment'}
        )

        client.post(
            f'/api/v1/posts/{test_post.id}/like',
            headers=user_headers,
            json={'reaction_type': 'like'}
        )

        response = client.delete(
            f'/api/v1/posts/{test_post.id}',
            headers=user_headers,
        )       
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert db.query(Comment).filter(Comment.post_id == test_post.id).count() == 0
        assert db.query(Like).filter(Like.post_id == test_post.id).count() == 0

    def test_unfollow_removes_posts_from_feed(self, client, user2_headers,test_user, test_post, db):
        """Test that deleting post removes comments and likes"""
        from app.models.comment import Comment
        from app.models.like import Like

        response = client.post(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user2_headers
        )

        response = client.get(f'/api/v1/posts/feed', headers=user2_headers)
        post_ids = [p['id'] for p in response.json()]
        assert test_post.id in post_ids
        

        response = client.delete(
            f'/api/v1/users/{test_user.username}/follow',
            headers=user2_headers
        )


        response = client.get(f'/api/v1/posts/feed', headers=user2_headers)
        post_ids = [p['id'] for p in response.json()]
        assert test_post.id not in post_ids