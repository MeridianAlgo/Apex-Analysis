"""
Authentication and Authorization Module

Provides JWT-based authentication with user management,
token generation, and role-based access control.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import hashlib
import secrets
import json
from pathlib import Path


class User:
    """User model"""
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        password_hash: str,
        roles: List[str] = None,
        api_key: str = None,
        created_at: datetime = None,
        is_active: bool = True
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.roles = roles or ['user']
        self.api_key = api_key or secrets.token_urlsafe(32)
        self.created_at = created_at or datetime.utcnow()
        self.is_active = is_active

    def to_dict(self) -> Dict:
        """Convert user to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'roles': self.roles,
            'api_key': self.api_key,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary"""
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles

    def check_password(self, password: str) -> bool:
        """Verify password"""
        return self.password_hash == AuthManager.hash_password(password)


class AuthManager:
    """Authentication manager with JWT and API key support"""

    def __init__(self, users_file: str = 'data/users.json'):
        self.users_file = Path(users_file)
        self.users: Dict[str, User] = {}
        self._load_users()

    def _load_users(self):
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                    self.users = {
                        uid: User.from_dict(data)
                        for uid, data in users_data.items()
                    }
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
        else:
            # Create default admin user
            self.users = {}
            self.create_default_users()

    def _save_users(self):
        """Save users to file"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            users_data = {
                uid: user.to_dict()
                for uid, user in self.users.items()
            }
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")

    def create_default_users(self):
        """Create default users for development"""
        # Admin user
        admin = self.create_user(
            username='admin',
            email='admin@apexanalysis.com',
            password='admin123',
            roles=['admin', 'user']
        )

        # Regular user
        user = self.create_user(
            username='demo',
            email='demo@apexanalysis.com',
            password='demo123',
            roles=['user']
        )

        print(f"Created default users:")
        print(f"  Admin: username='admin', password='admin123', API Key: {admin.api_key}")
        print(f"  Demo: username='demo', password='demo123', API Key: {user.api_key}")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: List[str] = None
    ) -> User:
        """Create a new user"""
        user_id = secrets.token_urlsafe(16)
        password_hash = self.hash_password(password)

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles or ['user']
        )

        self.users[user_id] = user
        self._save_users()

        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        for user in self.users.values():
            if user.username == username and user.is_active:
                if user.check_password(password):
                    return user
        return None

    def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """Authenticate user with API key"""
        for user in self.users.values():
            if user.api_key == api_key and user.is_active:
                return user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user attributes"""
        user = self.users.get(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and key != 'user_id':
                setattr(user, key, value)

        self._save_users()
        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        if user_id in self.users:
            del self.users[user_id]
            self._save_users()
            return True
        return False

    def regenerate_api_key(self, user_id: str) -> Optional[str]:
        """Regenerate API key for user"""
        user = self.users.get(user_id)
        if not user:
            return None

        user.api_key = secrets.token_urlsafe(32)
        self._save_users()
        return user.api_key

    def list_users(self) -> List[Dict]:
        """List all users (excluding sensitive data)"""
        return [
            {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if isinstance(user.created_at, datetime) else user.created_at
            }
            for user in self.users.values()
        ]


def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # This will be implemented in the Flask route
            return f(*args, **kwargs)
        wrapper._required_role = role
        return wrapper
    return decorator


def create_token_payload(user: User) -> Dict:
    """Create JWT token payload"""
    return {
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,
        'roles': user.roles
    }


# Global auth manager instance
auth_manager = AuthManager()


if __name__ == '__main__':
    """Demo and testing"""
    print("Authentication Module Demo")
    print("=" * 60)

    # Create auth manager
    manager = AuthManager('data/test_users.json')

    print("\n1. Testing User Creation")
    user = manager.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        roles=['user']
    )
    print(f"Created user: {user.username}")
    print(f"API Key: {user.api_key}")

    print("\n2. Testing Password Authentication")
    auth_user = manager.authenticate_user('testuser', 'testpass123')
    if auth_user:
        print(f"✓ Authentication successful: {auth_user.username}")
    else:
        print("✗ Authentication failed")

    print("\n3. Testing API Key Authentication")
    auth_user = manager.authenticate_api_key(user.api_key)
    if auth_user:
        print(f"✓ API Key authentication successful: {auth_user.username}")
    else:
        print("✗ API Key authentication failed")

    print("\n4. Testing Role-Based Access")
    print(f"User has 'user' role: {user.has_role('user')}")
    print(f"User has 'admin' role: {user.has_role('admin')}")

    print("\n5. Regenerating API Key")
    old_key = user.api_key
    new_key = manager.regenerate_api_key(user.user_id)
    print(f"Old key: {old_key[:20]}...")
    print(f"New key: {new_key[:20]}...")

    print("\n6. Listing All Users")
    users = manager.list_users()
    for u in users:
        print(f"  - {u['username']} ({u['email']}) - Roles: {u['roles']}")

    print("\n✅ Authentication module demo complete!")
