# Scholarius

Scholarius is a lightweight web-based quiz and study system written in Python and packaged as a Docker application.

The goal of Scholarius is to provide an easy-to-deploy quiz platform suitable for classrooms, self-study, certification preparation, and technical training.

---

# Building

Build the image:

```bash
docker build -t scholarius .
```

Verify:

```bash
docker image ls
```

Launch:

```bash
docker compose up -d
```

---

## Accessibility and project status

Scholarius is a work in progress and is **not considered production-ready**.

Accessibility has been considered during the current design work. The project
aims to build practical WCAG 2.2 Level AA fundamentals into the normal
interface rather than requiring users to enable a separate “accessible mode.”

Current considerations include:

- readable light, dark, and system-following themes;
- visible keyboard focus indicators;
- labeled form controls and icon actions;
- keyboard-accessible controls;
- reduced-motion support;
- layouts that tolerate zoom and larger text;
- avoiding reliance on color alone for meaning;
- keeping essential instructions visible rather than hiding them only in
  tooltips.

These measures are a foundation, not a certification or guarantee of full
WCAG conformance. Scholarius has not yet undergone a formal accessibility
audit, assistive-technology test program, or production security review.
Please be patient as the application and its user experience continue to
develop.

---

# License

Private project.

---

# Author

Thomas Hamilton
