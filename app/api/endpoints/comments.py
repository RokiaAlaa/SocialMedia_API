from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from app.api.deps.database import get_db
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate, CommentWithUser
from app.services.notification import create_notification
from app.models.notification import NotificationType
from app.core.limiter import limiter

router = APIRouter()

@router.get("/posts/{post_id}/comments", response_model=List[CommentWithUser])
@limiter.limit('60/minute')
async def get_post_comments(
    request: Request,
    post_id: int,
    db: Session = Depends(get_db),
):
    """Get all comments for a post (with replies)"""

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )
    
    comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).all()

    return [build_comment_tree(comment, db) for comment in comments]


@router.post("/posts/{post_id}/comments", response_model=CommentWithUser, status_code=status.HTTP_201_CREATED)
@limiter.limit('60/minute')
async def create_comment(
    request: Request,
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create comment on post"""

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Post not found"
        )
    
    comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=comment_in.content
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    if post.user_id != current_user.id:
        await create_notification(
            db=db,
            user_id=post.user_id,
            sender_id=current_user.id,
            type=NotificationType.COMMENT,
            post_id=post_id,
            comment_id=comment.id
        )

    return build_comment_tree(comment, db)


@router.post("/comments/{comment_id}/reply", response_model=CommentWithUser, status_code=status.HTTP_201_CREATED)
@limiter.limit('60/minute')
async def reply_to_comment(
    request: Request,
    comment_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reply to a comment"""

    parent = db.query(Comment).filter(Comment.id == comment_id).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Comment not found"
        )
    
    reply = Comment(
        post_id=parent.post_id,
        user_id=current_user.id,
        parent_id=comment_id,
        content=comment_in.content
    )

    db.add(reply)
    db.commit()
    db.refresh(reply)

    if parent.user_id != current_user.id:
        await create_notification(
            db=db,
            user_id=parent.user_id,
            sender_id=current_user.id,
            type=NotificationType.REPLY,
            post_id=parent.post_id,
            comment_id=reply.id
        )
    return build_comment_tree(reply, db)


@router.put("/comments/{comment_id}", response_model=CommentWithUser)
@limiter.limit('60/minute')
async def update_comment(
    request: Request,
    comment_id: int,
    comment_update: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update comment (own only)"""

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Comment not found"
        )
    
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized"
        )

    comment.content = comment_update.content
    db.commit()
    db.refresh(comment)

    return build_comment_tree(comment, db)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit('60/minute')
async def delete_comment(
    request: Request,
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete comment (own only)"""

    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Comment not found"
        )
    
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not authorized"
        )

    db.delete(comment)
    db.commit()

    return None


def build_comment_tree(comment: Comment, db: Session) -> CommentWithUser:
    """Build comment with nested replies"""

    replies = db.query(Comment).filter(Comment.parent_id == comment.id).all()

    user = db.query(User).filter(User.id == comment.user_id).first()

    return CommentWithUser.model_validate(
        {
            **comment.__dict__, 
            'user': user,
            'replies':[build_comment_tree(reply, db) for reply in replies]
        }
    )