FROM python:bullseye

WORKDIR /service
COPY . ./
RUN pip3 install Flask
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]