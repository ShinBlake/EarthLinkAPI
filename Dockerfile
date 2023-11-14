FROM python:3.11

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 5000
EXPOSE 8080
EXPOSE 80
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80" ]