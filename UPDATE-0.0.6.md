# Scholarius 0.0.6

## Progressive account help

The login card keeps **Create Account** as a full secondary action, but no
longer carries its explanatory sentence all the time.

When the user hovers over the button or reaches it with the keyboard, a
tooltip explains:

> Create a user account to save quiz history, marked questions, and
> preferences.

This is an example of **progressive disclosure**: keep the primary interface
quiet, then reveal supporting information when the user shows interest in
the action.

## Accessibility details

- The button uses `aria-describedby` to associate it with the explanation.
- The explanation appears for both mouse hover and keyboard focus.
- The tooltip is supporting information rather than a requirement, so the
  Create Account action remains understandable even when hover is unavailable.
- Reduced-motion preferences are respected.

## Version

Scholarius is now version `0.0.6`.
