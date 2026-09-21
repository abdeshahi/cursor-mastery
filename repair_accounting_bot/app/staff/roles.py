from __future__ import annotations

ROLE_ADMIN = 'admin'
ROLE_FULL = 'full'
ROLE_ACCOUNTANT = 'accountant'
ROLE_RECEPTION = 'reception'

ROLE_LABELS: dict[str, str] = {
    ROLE_ADMIN: 'مدیر',
    ROLE_FULL: 'پذیرش + حسابداری',
    ROLE_ACCOUNTANT: 'حسابدار',
    ROLE_RECEPTION: 'پذیرش',
}

MANAGEABLE_ROLES = (ROLE_RECEPTION, ROLE_ACCOUNTANT, ROLE_FULL)


def normalize_role(role: str | None, *, is_admin: bool = False) -> str:
    if is_admin or role == ROLE_ADMIN:
        return ROLE_ADMIN
    if role in ROLE_LABELS:
        return role
    return ROLE_FULL


def role_permissions(role: str) -> dict[str, bool]:
    role = normalize_role(role)
    return {
        'manage': role == ROLE_ADMIN,
        'reception': role in {ROLE_ADMIN, ROLE_FULL, ROLE_RECEPTION},
        'accounting': role in {ROLE_ADMIN, ROLE_FULL, ROLE_ACCOUNTANT},
    }
