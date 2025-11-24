"""
用户服务
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.utils.exceptions import NotFoundException, ConflictException, UnauthorizedException


class UserService:
    """用户服务"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查邮箱是否已存在
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise ConflictException("邮箱已被注册")
        
        # 检查用户名是否已存在
        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise ConflictException("用户名已被使用")
        
        # 创建用户
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password)
        )
        db.add(db_user)
        await db.flush()
        await db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """通过ID获取用户"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = await UserService.get_user_by_username(db, username)
        if not user:
            user = await UserService.get_user_by_email(db, username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise UnauthorizedException("用户已被禁用")
        
        return user
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> User:
        """更新用户"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        
        update_data = user_data.dict(exclude_unset=True)
        
        # 如果更新密码，需要哈希
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # 检查邮箱冲突
        if "email" in update_data and update_data["email"] != user.email:
            result = await db.execute(select(User).where(User.email == update_data["email"]))
            if result.scalar_one_or_none():
                raise ConflictException("邮箱已被使用")
        
        # 检查用户名冲突
        if "username" in update_data and update_data["username"] != user.username:
            result = await db.execute(select(User).where(User.username == update_data["username"]))
            if result.scalar_one_or_none():
                raise ConflictException("用户名已被使用")
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[User], int]:
        """获取用户列表"""
        # 获取总数
        count_result = await db.execute(select(func.count()).select_from(User))
        total = count_result.scalar()
        
        # 分页查询
        query = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: UUID) -> User:
        """禁用用户（软删除）"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        
        user.is_active = False
        await db.flush()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def activate_user(db: AsyncSession, user_id: UUID) -> User:
        """激活用户"""
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("用户不存在")
        
        user.is_active = True
        await db.flush()
        await db.refresh(user)
        
        return user

