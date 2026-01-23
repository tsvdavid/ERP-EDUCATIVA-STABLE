# Guía de Despliegue en VPS (Ubuntu 22.04/24.04) - ERP EDUCATIVA

Esta guía detalla los pasos para migrar y desplegar el sistema ERP EDUCATIVA (Django + React) en un servidor VPS de producción.

## 1. Prerrequisitos
- **Servidor VPS** con Ubuntu 22.04 o superior.
- **Acceso Root** o usuario con privilegios `sudo`.
- **Dominio** apuntando a la IP del servidor (ej: `erp.tudominio.com`).
- **Repositorio Git** con el código actualizado (GitHub/GitLab) O una forma de subir los archivos (SCP/SFTP).

## 2. Preparación del Servidor
Conéctate por SSH y actualiza el sistema:
```bash
sudo apt update && sudo apt upgrade -y
```

Instala las dependencias necesarias:
```bash
# Sistema y herramientas
sudo apt install -y git curl ufw build-essential libmysqlclient-dev pkg-config

# Python (Backend)
sudo apt install -y python3-pip python3-venv python3-dev

# Node.js (Frontend) - Usando NodeSource para versión reciente (20.x)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Base de Datos y Redis
sudo apt install -y mysql-server redis-server

# Servidor Web
sudo apt install -y nginx
```

## 3. Configuración de Base de Datos (MySQL)
Configura MySQL y crea la base de datos:
```bash
sudo mysql_secure_installation
# Sigue los pasos para asegurar la instalación

sudo mysql -u root -p
```
Dentro de la consola MySQL:
```sql
CREATE DATABASE erp_educativa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'erp_user'@'localhost' IDENTIFIED BY 'Tu_Contraseña_Segura_Aqui';
GRANT ALL PRIVILEGES ON erp_educativa.* TO 'erp_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 4. Configuración del Backend (Django)

### 4.1 Clonar el Código
```bash
cd /var/www
sudo mkdir erp_educativa
sudo chown -R $USER:$USER erp_educativa
git clone <URL_TU_REPOSITORIO> erp_educativa
# O sube tus archivos aquí. Estructura esperada: /var/www/erp_educativa/backend
```

### 4.2 Entorno Virtual e Instalación
```bash
cd /var/www/erp_educativa/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn daphne mysqlclient
```

### 4.3 Variables de Entorno
Crea un archivo `.env` en `backend/` para producción:
```env
DEBUG=False
SECRET_KEY=Genera_Una_Nueva_Key_Larga_Y_Segura
ALLOWED_HOSTS=tudominio.com,www.tudominio.com,IP_DEL_SERVIDOR
DB_NAME=erp_educativa
DB_USER=erp_user
DB_PASSWORD=Tu_Contraseña_Segura_Aqui
DB_HOST=localhost
DB_PORT=3306
```

### 4.4 Migraciones y Static
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4.5 Configurar Systemd (Gunicorn y Daphne)
Necesitamos dos servicios: Gunicorn para HTTP y Daphne para WebSockets.

**Archivo: `/etc/systemd/system/erp_gunicorn.service`**
```ini
[Unit]
Description=gunicorn daemon for ERP Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/erp_educativa/backend
ExecStart=/var/www/erp_educativa/backend/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/erp_gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Archivo: `/etc/systemd/system/erp_daphne.service`**
```ini
[Unit]
Description=daphne daemon for ERP WebSockets
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/erp_educativa/backend
ExecStart=/var/www/erp_educativa/backend/venv/bin/daphne -b 0.0.0.0 -p 8001 config.asgi:application

[Install]
WantedBy=multi-user.target
```

Inicia los servicios:
```bash
sudo systemctl start erp_gunicorn
sudo systemctl enable erp_gunicorn
sudo systemctl start erp_daphne
sudo systemctl enable erp_daphne
```

## 5. Configuración del Frontend (React)

### 5.1 Construir la Aplicación
En tu máquina local (o en el servidor si tiene recursos):
1. Configura la URL de producción en `.env.production` (o `.env`):
   ```
   VITE_API_URL=https://tudominio.com/api
   ```
2. Construye:
   ```bash
   npm install
   npm run build
   ```
Esto generará una carpeta `dist`.

### 5.2 Desplegar Archivos
Sube el contenido de la carpeta `dist` al servidor en `/var/www/erp_educativa/frontend_build`.

```bash
sudo mkdir -p /var/www/erp_educativa/frontend_build
# Copia los archivos del build aquí
```

## 6. Configuración de Nginx (Reverse Proxy)

Crea el archivo `/etc/nginx/sites-available/erp_educativa`:

```nginx
server {
    server_name tudominio.com www.tudominio.com;

    # Frontend (React)
    location / {
        root /var/www/erp_educativa/frontend_build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Backend API (Gunicorn)
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/run/erp_gunicorn.sock;
    }

    # Django Admin (Gunicorn)
    location /admin/ {
        include proxy_params;
        proxy_pass http://unix:/run/erp_gunicorn.sock;
    }

    # Archivos Estáticos de Django (Admin panel, etc)
    location /static/ {
        alias /var/www/erp_educativa/backend/static/;
    }
    
    # Archivos Media (Subidos por usuarios)
    location /media/ {
        alias /var/www/erp_educativa/backend/media/;
    }

    # WebSockets (Daphne)
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_redirect off;
    }
}
```

Activa el sitio:
```bash
sudo ln -s /etc/nginx/sites-available/erp_educativa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Seguridad final (SSL)
Usa Certbot para HTTPS gratuito:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tudominio.com
```

¡Listo! Tu aplicación debería estar accesible en `https://tudominio.com`.
