Scholarius 0.0.4 Account UX Patch
==================================

Replace these four files:

    app/templates/home.html
    app/templates/login.html
    app/templates/_corner_nav.html
    app/static/style.css

Changes:
- Removes "Signed in as ..." from the home card.
- Makes Create Account a full secondary button on the login card.
- Adds the text:
  "Create a user account to save quiz history, marked questions,
   and preferences."
- Removes version text from both the home and login cards.
- Places Home, Profile, authorized Admin, and a faint version label
  together in a fixed lower-left utility strip.
- On the login page, only the faint version label appears lower-left.

No Python, authentication, or database files are changed.

After replacing the files:
    git add app/templates/home.html app/templates/login.html \
            app/templates/_corner_nav.html app/static/style.css
    git commit -m "Refine account creation and utility navigation"
    git push

Then rebuild and force-refresh the browser.
