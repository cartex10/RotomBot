FROM python:3.11

RUN pip install -U discord.py
RUN pip install python-dotenv
RUN pip install requests

COPY *.py /
COPY .env /
VOLUME /db

CMD python rotomBot.py