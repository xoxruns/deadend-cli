FROM kalilinux/kali-rolling

RUN apt update && apt -y install kali-linux-large inetutils-*

RUN ["/bin/bash"]