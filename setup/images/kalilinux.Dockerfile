FROM kalilinux/kali-rolling
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt update && apt -y install kali-linux-headless inetutils-*

RUN ["/bin/bash"]