from app.staff.roles import ROLE_ACCOUNTANT, ROLE_ADMIN, ROLE_FULL, ROLE_RECEPTION, role_permissions


def test_admin_has_all_permissions() -> None:
    perms = role_permissions(ROLE_ADMIN)
    assert perms['manage']
    assert perms['reception']
    assert perms['accounting']


def test_accountant_only_accounting() -> None:
    perms = role_permissions(ROLE_ACCOUNTANT)
    assert not perms['manage']
    assert not perms['reception']
    assert perms['accounting']


def test_reception_only_reception() -> None:
    perms = role_permissions(ROLE_RECEPTION)
    assert not perms['manage']
    assert perms['reception']
    assert not perms['accounting']


def test_full_has_both_menus() -> None:
    perms = role_permissions(ROLE_FULL)
    assert not perms['manage']
    assert perms['reception']
    assert perms['accounting']
