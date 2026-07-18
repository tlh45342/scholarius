# Scholarius 0.0.4 — Profiles and Authentication

This test installment adds:

- first-run administrator creation at `/setup`;
- PBKDF2-SHA256 password hashing using the Python standard library;
- real username/password verification;
- normal self-service profile creation at `/register`;
- `admin` and `user` roles;
- admin-only Question Bank Management and Administration pages;
- editable display name, light/dark preference, and password on `/profile`;
- logout support;
- automatic upgrade of old plaintext development passwords after a successful login.

## Important migration behavior

An existing `users` table is upgraded in place. Existing development accounts with plaintext passwords can log in once using their current password; Scholarius then replaces that value with a secure hash.

If there are no users, opening `/` redirects to `/setup` to create the first administrator.
