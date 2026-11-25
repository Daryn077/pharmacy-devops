# pharmacy-devops — Дәріхана, 5-нұсқа

Учебный DevOps-проект аптеки: Ansible, FastAPI (API → BLL → DAL), pytest, Docker, GitHub Actions, Kubernetes (Minikube), Nginx Gateway, React + Vite, микросервис доставки.

Обозначения: **[CMD]** — командная строка Windows, **[WSL]** — Ubuntu (`wsl -d Ubuntu`), **[Браузер]** — браузер Windows.

---

## Этап 0. Распаковка архива

**[CMD]** (если архив скачан в «Загрузки»):

```cmd
tar -xf "%USERPROFILE%\Downloads\pharmacy-devops.zip" -C C:\
dir C:\pharmacy-devops
```

Должны появиться папки `ansible`, `backend`, `frontend`, `delivery-service`, `gateway`, `k8s`, `.github`.

---

## Этап 1. Ansible (vm1 — web, vm2 — storage)

Вместо двух VM используются два Docker-контейнера Ubuntu 22.04 с SSH (только с разрешения преподавателя). Ansible работает в WSL Ubuntu и подключается к ним по SSH.

### 1.1 SSH-ключ — [WSL]

```cmd
wsl -d Ubuntu
```

```bash
ssh-keygen -t ed25519 -f ~/.ssh/pharmacy_key -N ""
cp ~/.ssh/pharmacy_key.pub /mnt/c/pharmacy-devops/ansible/authorized_keys
```

Приватный ключ остаётся в `~/.ssh` внутри WSL. В проект копируется только публичный, и он тоже исключён в `.gitignore`.

### 1.2 Сборка и запуск «VM» — [CMD]

```cmd
cd C:\pharmacy-devops\ansible
docker build -t pharmacy-ubuntu .
docker run -d --name vm1 --hostname vm1 -p 2221:22 -p 8081:80 pharmacy-ubuntu
docker run -d --name vm2 --hostname vm2 -p 2222:22 pharmacy-ubuntu
docker ps
```

### 1.3 Проверка SSH — [WSL]

```bash
cd /mnt/c/pharmacy-devops/ansible
ssh -i ~/.ssh/pharmacy_key -p 2221 -o StrictHostKeyChecking=no root@127.0.0.1 hostname
```

Должно вывести `vm1`. Если `Connection refused` или зависание, значит, localhost из WSL не видит порты Docker. Тогда используйте IP Windows-хоста:

```bash
WINIP=$(ip route show default | awk '{print $3}')
echo $WINIP
ssh -i ~/.ssh/pharmacy_key -p 2221 -o StrictHostKeyChecking=no root@$WINIP hostname
sed -i "s/127.0.0.1/$WINIP/" hosts.ini
```

### 1.4 Ping и playbook — [WSL]

```bash
ansible all -i hosts.ini -m ping
ansible-playbook -i hosts.ini site.yml
ansible-playbook -i hosts.ini site.yml
```

Во втором запуске в PLAY RECAP должно быть `changed=0` для vm1 и vm2.

### 1.5 Демонстрация

- **[Браузер]** `http://localhost:8081` — страница «Дәріхана — 5-нұсқа», hostname `vm1`, IP контейнера (172.17.0.x).
- **[WSL]** файлы на vm2:

```bash
ansible storage -i hosts.ini -m shell -a "ls -l /opt/pharmacy && cat /opt/pharmacy/*.txt"
```

Пояснение для преподавателя: порт 80 «VM» vm1 проброшен на порт 8081 Windows (`-p 8081:80`), а SSH — на 2221/2222. IP на странице — внутренний адрес контейнера в сети Docker (`ansible_default_ipv4.address`). systemd в контейнере нет, поэтому nginx запускается командой `nginx` только если процесс ещё не запущен (проверка `pgrep`), и это сохраняет идемпотентность.

После перезагрузки ПК: `docker start vm1 vm2` [CMD], затем снова запустить playbook.

Если Ansible сообщит, что Python 3.10 на хосте не поддерживается: добавьте `python3.11` в `apt-get install` в `ansible/Dockerfile`, в `hosts.ini` укажите `ansible_python_interpreter=/usr/bin/python3.11`, затем пересоздайте контейнеры (`docker rm -f vm1 vm2` и шаг 1.2).

---

## Этап 2. Backend FastAPI, тесты, Docker, GitHub Actions

Структура: `app/api` (роутеры, Pydantic-схемы, перевод ошибок в HTTP) → `app/bll` (PharmacyService, бизнес-правила) → `app/dal` (in-memory репозитории). API не импортирует DAL.

| Ошибка BLL | HTTP |
|---|---|
| Отрицательный остаток / некорректные данные | 400 |
| Нет рецепта | 403 |
| Лекарство/заказ не найдены | 404 |
| Недостаточно товара | 409 |

### 2.1 Тесты — [CMD]

```cmd
cd C:\pharmacy-devops\backend
python -m pip install -r requirements.txt
python -m pytest -v
```

Ожидается 23 теста: 11 BLL unit-тестов с подменой репозитория (`tests/test_bll.py`) и 12 API-тестов через TestClient (`tests/test_api.py`).

### 2.2 Docker и Swagger — [CMD]

```cmd
cd C:\pharmacy-devops\backend
docker build -t pharmacy-api:1.0 .
docker run -d --name pharmacy-api-local -p 8000:8000 pharmacy-api:1.0
```

**[Браузер]** `http://localhost:8000/docs`. После проверки: `docker rm -f pharmacy-api-local`.

### 2.3 GitHub и Actions — [CMD]

Создайте на github.com пустой репозиторий `pharmacy-devops` (без README). Затем:

```cmd
cd C:\pharmacy-devops
git init
git add .
git status
git commit -m "Pharmacy DevOps: Ansible, FastAPI, CI, Kubernetes"
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/pharmacy-devops.git
git push -u origin main
```

В `git status` не должно быть `ansible/authorized_keys`. Если git просит имя: `git config --global user.name "Имя"` и `git config --global user.email "почта"`.

На вкладке **Actions** должны появиться задачи `Python 3.11` и `Python 3.12`.

---

## Этап 3. Kubernetes (Minikube)

### 3.1 Запуск — [CMD]

```cmd
minikube start --driver=docker
minikube addons enable metrics-server
```

### 3.2 Сборка образов и загрузка в Minikube — [CMD]

```cmd
cd C:\pharmacy-devops
docker build -t pharmacy-api:1.0 backend
docker build -t delivery-service:1.0 delivery-service
docker build -t pharmacy-frontend:1.0 frontend
docker pull nginx:1.27-alpine
minikube image load pharmacy-api:1.0
minikube image load delivery-service:1.0
minikube image load pharmacy-frontend:1.0
minikube image load nginx:1.27-alpine
minikube image ls
```

### 3.3 Развёртывание — [CMD]

```cmd
kubectl apply -f k8s\
kubectl get pods -n v5-pharmacy -w
```

Дождитесь, пока 8 Pod будут `1/1 Running`, затем остановите наблюдение `Ctrl+C`.

### 3.4 Проверки для преподавателя — [CMD]

```cmd
kubectl get namespaces
kubectl get deployments -n v5-pharmacy
kubectl get pods -n v5-pharmacy
kubectl get services -n v5-pharmacy
kubectl get configmap -n v5-pharmacy
kubectl get hpa -n v5-pharmacy
```

Если в TARGETS у HPA показано `<unknown>/60%`, подождите 1–2 минуты (metrics-server собирает метрики).

### 3.5 Открыть сайт

NodePort 30085 задан в `k8s/05-gateway.yaml`. На Windows с Docker driver адрес `http://<minikube ip>:30085` напрямую обычно не открывается, поэтому используйте один из вариантов (окно CMD оставьте открытым):

```cmd
minikube service gateway -n v5-pharmacy --url
```

или

```cmd
kubectl port-forward -n v5-pharmacy svc/gateway 30085:80
```

Второй вариант откроет сайт по адресу **[Браузер]** `http://localhost:30085`.

Проверка маршрутов в другом окне CMD (для port-forward):

```cmd
curl http://localhost:30085/api/pharmacy/health
curl http://localhost:30085/api/pharmacy/medicines?in_stock=true
curl http://localhost:30085/api/delivery/health
curl http://localhost:30085/api/delivery/delivery/districts
```

### 3.6 Самовосстановление — [CMD]

```cmd
kubectl get pods -n v5-pharmacy -l app=pharmacy-api
kubectl delete pod ИМЯ_POD -n v5-pharmacy
kubectl get pods -n v5-pharmacy -l app=pharmacy-api -w
```

### 3.7 (Необязательно) нагрузка для HPA — [CMD]

```cmd
kubectl run load -n v5-pharmacy --image=busybox:1.36 --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://pharmacy-api:8000/medicines >/dev/null; done"
kubectl get hpa -n v5-pharmacy -w
kubectl delete pod load -n v5-pharmacy
```

### Маршрутизация Gateway (ConfigMap `gateway-config`)

| Внешний путь | Куда |
|---|---|
| `/` | `pharmacy-frontend:80` |
| `/api/pharmacy/medicines` | `pharmacy-api:8000/medicines` |
| `/api/delivery/delivery/estimate?district=…` | `delivery-service:8000/delivery/estimate` |

### Ограничение in-memory

Каждая реплика `pharmacy-api` хранит данные в своей памяти. Начальный список лекарств одинаков во всех репликах, но добавленные лекарства и заказы есть только в той реплике, которая обработала запрос, и теряются при удалении Pod. Для стабильной демонстрации у Service стоит `sessionAffinity: ClientIP`: клиент закрепляется за одним Pod. Это не синхронизация данных. Для настоящей системы нужна общая БД, но по условию требуется in-memory.
