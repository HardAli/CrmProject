from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.common.enums import UserRole
from app.database.models.role_pass import RolePass
from app.database.models.user import User
from app.repositories.role_pass_repository import RolePassRepository


@dataclass(slots=True)
class PassValidationResult:
    is_valid: bool
    reason: str | None = None
    role_pass: RolePass | None = None


class RolePassService:
    def __init__(self, role_pass_repository: RolePassRepository, *, expire_minutes: int = 60) -> None:
        self._role_pass_repository = role_pass_repository
        self._expire_minutes = expire_minutes

    async def generate_manager_pass(self, current_user: User) -> RolePass:
        return await self._generate_pass(current_user=current_user, target_role=UserRole.MANAGER)

    async def generate_admin_pass(self, current_user: User) -> RolePass:
        return await self._generate_pass(current_user=current_user, target_role=UserRole.ADMIN)

    async def _generate_pass(self, *, current_user: User, target_role: UserRole) -> RolePass:
        code = self._generate_code()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        return await self._role_pass_repository.create_pass(
            code=code,
            target_role=target_role,
            created_by=current_user.id,
            expires_at=expires_at,
        )

    async def validate_passcode(self, code: str) -> PassValidationResult:
        role_pass = await self._role_pass_repository.get_by_code(code)
        if role_pass is None:
            return PassValidationResult(is_valid=False, reason="invalid")
        if role_pass.is_used:
            return PassValidationResult(is_valid=False, reason="used", role_pass=role_pass)
        if role_pass.expires_at <= datetime.now(timezone.utc):
            return PassValidationResult(is_valid=False, reason="expired", role_pass=role_pass)
        return PassValidationResult(is_valid=True, role_pass=role_pass)

    async def consume_passcode(self, *, user: User, code: str) -> PassValidationResult:
        validation = await self.validate_passcode(code)
        if not validation.is_valid or validation.role_pass is None:
            return validation
        await self._role_pass_repository.mark_as_used(
            pass_id=validation.role_pass.id,
            used_by=user.id,
            used_at=datetime.now(timezone.utc),
        )
        return validation

    @staticmethod
    def _generate_code(length: int = 10) -> str:
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))