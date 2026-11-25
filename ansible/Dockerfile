# Учебная "VM" для Ansible: Ubuntu 22.04 + SSH.
# Nginx здесь НЕ устанавливается — его устанавливает Ansible (site.yml).
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server \
        python3 \
        python3-apt \
        iproute2 \
        procps \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd /root/.ssh \
    && chmod 700 /root/.ssh \
    && ssh-keygen -A

# Публичный ключ из WSL (файл authorized_keys создаётся на шаге 1.2, в git не попадает)
COPY authorized_keys /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys && chown root:root /root/.ssh/authorized_keys

EXPOSE 22 80

CMD ["/usr/sbin/sshd", "-D", "-e"]
