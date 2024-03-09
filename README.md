# how to run the project

## start off by install the requirements using:
  `pip install requirements.txt`
  
## start the docker services using:
  `docker compose up -d`

## start the celery worker using:
  `celery -A tasks worker --loglevel=INFO`

## start the flask server using:
  `uvicorn main:app --reload`
