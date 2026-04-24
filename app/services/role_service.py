from __future__ import annotations

from dataclasses import dataclass

from app.common.enums import UserRole
from app.database.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.role_pass_service import PassValidationResult, RolePassService


@dataclass(slots=True)
class RoleApplyResult:
    success: bool
    reason: str | None = None
    role: UserRole | None = None


class RoleService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_pass_service: RolePassService,
        *,
        supervisor_secret: str,
    ) -> None:
        self._user_repository = user_repository
        self._role_pass_service = role_pass_service
        self._supervisor_secret = supervisor_secret

    def can_open_supervisor_panel(self, current_user: User | None) -> bool:
        return bool(current_user and current_user.role == UserRole.SUPERVISOR and current_user.is_active)

    async def promote_to_supervisor_by_secret(self, *, telegram_id: int, full_name: str, message_text: str) -> User | None:
        if message_text != self._supervisor_secret:
            return None

        user = await self._user_repository.get_or_create_by_telegram_user(
            telegram_id=telegram_id,
            full_name=full_name,
            default_role=UserRole.MANAGER,
        )
        user.role = UserRole.SUPERVISOR
        user.is_active = True
        await self._user_repository.set_role(user, UserRole.SUPERVISOR)
        return user

    async def apply_role_passcode(self, *, user: User, code: str) -> RoleApplyResult:
        validation: PassValidationResult = await self._role_pass_service.consume_passcode(user=user, code=code)
        if not validation.is_valid:
            return RoleApplyResult(success=False, reason=validation.reason)

        role_pass = validation.role_pass
        if role_pass is None:
            return RoleApplyResult(success=False, reason="invalid")

        await self._user_repository.set_role(user, role_pass.target_role)
        user.is_active = True
        return RoleApplyResult(success=True, role=role_pass.target_role)