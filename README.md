```bash
python -m venv venv
server\venv\Scripts\activate.bat
pip install "fastapi[all]" "motor[src]" beanie aiostream
pip freeze > requirements.txt
docker-compose up --build
```