# initializes a new build stage and sets the Base Image
FROM python:3

# labels choosing just from Docker tutorial
LABEL version="0.2"
LABEL description="Telegram bot Green Grass Bot"

# set the working directory for COPY, RUN, CMD commands
WORKDIR /usr/src/app

# copy files and directories to the filesystem of the container
COPY . .

# install packages listed in requirements with disabled cache
RUN pip install --no-cache-dir -r requirements.txt

# execute container
CMD [ "python", "./main.py" ]

# CLI run snippet V1: docker run --env-file <<path_to_'.env'_file>> baidakovil/greengrassbot:main
# CLI run snippet V2: docker run --env API_KEY=<<lastfm_api_key>> --env BOT_TOKEN=<<telegram_bot_token>> baidakovil/greengrassbot:main
