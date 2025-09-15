FROM kalilinux/kali-rolling

RUN apt update && apt -y install kali-linux-large

RUN ["/bin/bash"]