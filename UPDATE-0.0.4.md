# Scholarius 0.0.4 — Profiles, Authentication, and Quiet Navigation

This refined 0.0.4 package includes:

- first-run administrator creation;
- PBKDF2-HMAC-SHA256 password hashing and verification;
- normal personal-profile creation;
- `admin` and `user` roles;
- administrator-only question-bank and user-management routes;
- profile editing, password changes, and stored appearance preference;
- compact lower-left Home, Profile, and administrator-only Admin controls;
- a faint lower-right version label;
- preservation of role and profile information while a quiz is active.

The Home control is hidden on the home page itself. The Admin control is rendered only for administrator sessions.
