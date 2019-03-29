FROM ubuntu:xenial

# Install necessary binary
RUN apt-get update && apt-get -y install bash unzip curl git python-pip python-dev rubygems ruby-dev sshpass openssh-client curl wget && gem install cf-uaac 
COPY p-automator /usr/bin
COPY om /usr/bin
COPY govc /usr/bin
COPY cf-mgmt /usr/bin
COPY pipeline-utilities-linux /usr/bin/pipeline-utilities
COPY tile-config-generator-linux /usr/bin/tile-config-generator
COPY bosh /usr/bin
# environment-to-yaml binary and source are from pipeline-utilities/commands
COPY environment-to-yaml /usr/bin
RUN chmod +x /usr/bin/tile-config-generator
RUN chmod +x /usr/bin/environment-to-yaml