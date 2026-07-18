# Scholarius 0.0.8

## Theme preference

- Adds Light, Dark, and Follow System choices.
- Stores the preference with the user account.
- Applies the selected theme across rendered pages.
- Uses shared CSS variables so future pages can inherit theme behavior.

## UX cleanup

- Home-screen actions now use consistent blue primary buttons.
- Question Bank Management actions now use consistent blue buttons.
- Removes textual Home links from quiz cards.
- Retains explicit question-marking behavior.
- Repairs the Question Bank List route by reading installed banks from SQLite.

## Accessibility foundation

- Adds keyboard-visible focus indicators.
- Respects reduced-motion preferences.
- Uses theme-aware contrast variables.
- Keeps accessible labels on icon controls.
- Documents accessibility intent and work-in-progress status in README.md.

Scholarius remains under active development and is not production-ready.
