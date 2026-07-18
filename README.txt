Scholarius 0.0.4 Navigation Correction
========================================

This patch changes only two application files:

    app/templates/_corner_nav.html
    app/static/style.css

Changes:
- Removes the visible version label from all pages.
- Keeps version reporting available through /version and /v1/version.
- Forces Home, Profile, and authorized Admin controls into a horizontal
  group in the lower-left corner.
- Hides the Home control while already on the home page, as controlled by
  the existing show_home template variable.

Install:
1. Replace the two files at their matching repository locations.
2. Commit them to GitHub.
3. Pull and rebuild the container.
4. Force-refresh the browser with Ctrl+F5.
