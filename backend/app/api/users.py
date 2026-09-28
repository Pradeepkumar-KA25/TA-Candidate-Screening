from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_activity_log_repository, get_auth_repository, require_roles
from app.core.security import hash_password
from app.models.user import User
from app.repositories.activity_log_repository import ActivityLogRepository
from app.repositories.auth_repository import AuthRepository
from app.schemas.users import CreateUserRequest, ResetPasswordRequest, UpdateUserRequest, UserResponse

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("", response_model=list[UserResponse])
async def list_users(_: User = Depends(require_roles("Admin")), repository: AuthRepository = Depends(get_auth_repository)):
    return repository.list_users()


@users_router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_roles("Admin")),
    repository: AuthRepository = Depends(get_auth_repository),
    activity: ActivityLogRepository = Depends(get_activity_log_repository),
):
    if repository.get_user_by_email(request.email) is not None:
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    user = repository.create_user(full_name=request.full_name, email=request.email, password_hash=hash_password(request.password), role=request.role)
    activity.create(actor_id=current_user.id, action_type="user_created", description=f"Created user {user.email}", entity_type="user", entity_id=user.id, metadata={"role": user.role})
    return user


@users_router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    current_user: User = Depends(require_roles("Admin")),
    repository: AuthRepository = Depends(get_auth_repository),
    activity: ActivityLogRepository = Depends(get_activity_log_repository),
):
    user = repository.update_user(user_id, full_name=request.full_name, role=request.role, is_active=request.is_active)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    activity.create(actor_id=current_user.id, action_type="user_updated", description=f"Updated user {user.email}", entity_type="user", entity_id=user.id, metadata=request.model_dump(exclude_none=True))
    return user


@users_router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    user_id: UUID,
    request: ResetPasswordRequest,
    current_user: User = Depends(require_roles("Admin")),
    repository: AuthRepository = Depends(get_auth_repository),
    activity: ActivityLogRepository = Depends(get_activity_log_repository),
):
    user = repository.update_password(user_id, hash_password(request.password))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    activity.create(
        actor_id=current_user.id,
        action_type="user_password_reset",
        description=f"Reset password for user {user.email}",
        entity_type="user",
        entity_id=user.id,
    )