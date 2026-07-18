Scholarius
Scholarius is a lightweight web-based quiz and study system.
The system is designed to be easy, and asimple.
You would think someone else would have done this by now. (without getting all commercial driven)

The goal of Scholarius is to provide an easy-to-deploy quiz platform suitable for classrooms, self-study, certification preparation, and technical training.

Features
Web-based interface
Multiple quiz support
User profiles
Question randomization
Docker deployment
Simple Python backend
HTML/Jinja templates
Easy backup of quiz content
Requirements
Docker
Docker Compose (recommended)
or

Python 3.11+
Directory Layout
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
Building
Build the image:

docker build -t scholarius .
Verify:

docker image ls
Running
Create and start the container:

docker run -d \
    --name scholarius \
    -p 8000:8000 \
    scholarius
Open:

http://localhost:8000
or

http://<server-ip>:8000
Using Docker Compose
A typical compose file looks like:

services:
  scholarius:
    build: .
    container_name: scholarius

    ports:
      - "8000:8000"

    restart: unless-stopped
Start:

docker compose up -d
Stop:

docker compose down
Rebuild after changes:

docker compose up -d --build
Existing Containers
View running containers:

docker ps
View all containers:

docker ps -a
Start an existing container:

docker start scholarius
Stop:

docker stop scholarius
View logs:

docker logs -f scholarius
Development
If developing outside Docker:

Install requirements:

pip install -r requirements.txt
Run:

./start.sh
or execute the Python entry point directly.

Future Features
The project roadmap includes:

User administration
Quiz editor
Question editor
Categories
Difficulty levels
Images in questions
Timed quizzes
Statistics
Score history
Import/export
REST API
Docker Hub publishing
License
Private project.

Author
Thomas Hamilton
