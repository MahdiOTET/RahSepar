from pwdlib import PasswordHash

pass_hasher = PasswordHash.recommended()


def hash_password(pwd: str) -> str:
    return pass_hasher.hash(pwd)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return pass_hasher.verify(password, hashed_password)
