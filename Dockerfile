FROM dorowu/ubuntu-desktop-lxde-vnc

# Add the GPG key for the Google Chrome repository
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Update the package lists and install Python 3.10, Python3-pip, curl, and other necessary tools
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y python3.10 python3-pip python3.10-dev python3.10-distutils unzip nano curl libgraphviz-dev

# Update pip for Python 3.10
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Install the fuzzingbook package
RUN  pip install fuzzingbook jupyterlab gcovr matplotlib

# Create a directory where you want to store your data
RUN mkdir /app

# Set the working directory
WORKDIR /app

# Add the project1 folder to the root directory
ADD project1 /root/project1

# Execute the makefile
RUN cd /root/project1 && make clean && make

# Expose port 80
EXPOSE 80