FROM python:bullseye



WORKDIR /service
COPY . ./
RUN pip3 install -r requirements.txt
CMD ["python", "main.py"]