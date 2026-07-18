# Scholarius

Scholarius is a lightweight web-based quiz and testing platform suitable for classrooms, self-study, certification preparation, and technical training.

The goal of Scholarius is to provide a simple easy to use system that can stood up on demand. 

It is my opinion that I shouldn't have had to create this.  Commercial systems abound and across a decade I really don't like the price creap of products. 

---

# Features

- Web-based interface
- Multiple quiz support
- User profiles
- Question randomization
- Docker deployment
- Simple Python backend
- HTML/Jinja templates
- Easy backup of quiz content

---

# Requirements

- Docker
- Docker Compose (recommended)

or

- Python 3.11+

---

## Getting

```bash
git clone https://github.com/tlh45342/scholarius.git
```

---

## Easy Start

```bash
docker compose up -d --build
```

---

## Default credentials

Default username: admin
Default password: password

As these are defaults please change promptly.

---

# Directory Layout

```
scholarius/
│
├── app/
│   ├── templates/
│   ├── static/
│   └── ...
│
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── start.sh
└── README.md
```

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

---

# Running

Create and start the container:

```bash
docker run -d \
    --name scholarius \
    -p 8000:8000 \
    scholarius
```

Open:

```
http://localhost:8000
```

or

```
http://<server-ip>:8000
```

---

# Using Docker Compose

A typical compose file looks like:

```yaml
services:
  scholarius:
    build: .
    container_name: scholarius

    ports:
      - "8000:8000"

    restart: unless-stopped
```

Start:

```bash
docker compose up -d
```

Stop:

```bash
docker compose down
```

Rebuild after changes:

```bash
docker compose up -d --build
```

---

# Existing Containers

View running containers:

```bash
docker ps
```

View all containers:

```bash
docker ps -a
```

Start an existing container:

```bash
docker start scholarius
```

Stop:

```bash
docker stop scholarius
```

View logs:

```bash
docker logs -f scholarius
```

---

# Development

If developing outside Docker:

Install requirements:

```bash
pip install -r requirements.txt
```

Run:

```bash
./start.sh
```

or execute the Python entry point directly.

---

# Future Features

The project roadmap includes:

- User administration
- Quiz editor
- Question editor
- Categories
- Difficulty levels
- Images in questions
- Timed quizzes
- Statistics
- Score history
- Import/export
- REST API
- Docker Hub publishing

---

# License

Private project.

---

# Author

Thomas Hamilton
