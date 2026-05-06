import pytest
from fastapi import status

class TestPosts:
    """Test post endpoints"""

    def test_list_posts(self, client, test_post):
        """Test listing posts"""
        response = client.get('/api/v1/posts')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_post(self, client, test_post):
        """Test getting single post"""
        response = client.get(f'/api/v1/posts/{test_post.id}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['id'] == test_post.id
        assert data['content'] == test_post.content
        assert 'user' in data
        assert 'likes_count' in data
        assert 'comments_count' in data

    def test_get_post_increments_view_count(self, client, test_post, db):
        """Test that viewing post increments view count"""
        initial_views = test_post.view_count

        response = client.get(f'/api/v1/posts/{test_post.id}')

        db.refresh(test_post)
        assert test_post.view_count == initial_views + 1

    def test_get_nonexistent_post(self, client):
        """Test getting non-existent post"""
        response = client.get('/api/v1/posts/99999')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_post(self, client, user_headers):
        """Test creating post"""
        response = client.post(
            '/api/v1/posts',
            headers=user_headers,
            json={
                'content': 'New test post',
                'tag_names': ['test', 'python']
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['content'] == 'New test post'
        assert len(data['tags']) == 2

    def test_create_post_unauthorized(self, client):
        """Test creating post without auth"""
        response = client.post(
            '/api/v1/posts',
            json={'content': 'New test post'}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
  
    def test_create_post_empty_content(self, client, user_headers):
        """Test creating post with empty content"""
        response = client.post(
            '/api/v1/posts',
            headers=user_headers,
            json={'content': ''}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_update_own_post(self, client, test_post, user_headers):
        """Test updating own post"""
        response = client.put(
            f'/api/v1/posts/{test_post.id}',
            headers=user_headers,
            json={'content': 'updated content'}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['content'] == 'updated content'

    def test_update_other_user_post_forbidden(self, client, test_post, user2_headers): 
        """Test updating another user's post (should fail)"""
        response = client.put(
            f'/api/v1/posts/{test_post.id}',
            headers=user2_headers,
            json={'content': 'Hacked'}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_own_post(self, client, test_post, user_headers): 
        """Test deleting own post"""
        response = client.delete(
            f'/api/v1/posts/{test_post.id}',
            headers=user_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        response = client.get(f'/api/v1/posts/{test_post.id}')        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_other_user_post_forbidden(self, client, test_post, user2_headers): 
        """Test deleting another user's post (should fail)"""
        response = client.delete(
            f'/api/v1/posts/{test_post.id}',
            headers=user2_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_posts(self, client, test_user, test_post):
        """Test getting posts by specific user"""
        response = client.get(f'/api/v1/posts/user/{test_user.username}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert all(post['user']['username'] == test_user.username for post in data)

    def test_search_posts(self, client, test_post):
        """Test searching posts"""
        response = client.get('/api/v1/posts?search=Test')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

    def test_filter_posts_by_tag(self, client, test_post, test_tag, db):
        """Test filtering posts by tag"""
        test_post.tags.append(test_tag)
        db.commit()

        response = client.get(f'/api/v1/posts?tag={test_tag.slug}')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

    def test_get_feed_authenticated(self, client, test_user, test_user2, user_headers, db):
        """Test personalized feed"""
        from app.models.follow import Follow
        follow = Follow(follower_id=test_user.id, following_id=test_user2.id)
        db.add(follow)
        db.commit()

        from app.models.post import Post
        post = Post(user_id=test_user2.id, content='post by user2')
        db.add(post)
        db.commit() 

        response = client.get(f'/api/v1/posts/feed', headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0


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