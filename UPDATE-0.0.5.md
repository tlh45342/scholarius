# Scholarius 0.0.5

## First-run experience

- Adds a Welcome to Scholarius card before administrator creation.
- Explains what Scholarius is and what the setup process will do.
- Moves administrator creation to `/setup/admin`.
- The welcome card appears only while no user accounts exist.

## Card navigation

- Adds a discreet Home or Back icon in the lower-left of focused task cards.
- Keeps the global lower-left utility navigation for Home, Profile, and Admin.
- Retains the quiet version indicator outside the cards.

## Question bank management

- Simplifies `/qb-manage` into an installed-question-bank list.
- Moves QTI upload and validation controls to `/qb-manage/import`.
- Adds an Import Question Bank button to the management card.
- Import errors return to the dedicated import page.
- Successful imports return to the installed-bank list.

## Account UX retained

- Create Account remains a full secondary button on the login card.
- The login card explains that user accounts preserve history,
  marked questions, and preferences.
- The home card does not display the signed-in username.
