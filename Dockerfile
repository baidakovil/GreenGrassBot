# initializes a new build stage and sets the Base Image
# 'python:3' form taken from python Official Image sample Dockerfile
FROM python:3

# labels choosing just from Docker tutorial
LABEL version="0.2"
LABEL description="Telegram bot Great Gig Bot"

# set the working directory for COPY, RUN, CMD commands
WORKDIR /usr/src/app

# copy files and directories to the filesystem of the container
COPY . .

# install packages listed in requirements with disabled cache
RUN pip install --no-cache-dir -r requirements.txt

# execute container
CMD [ "python", "./main.py" ]
