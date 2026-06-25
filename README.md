# Sistema Cliente-Servidor en Python

Aplicación cliente-servidor desarrollada en Python utilizando sockets TCP.

Permite:

- Autenticación de usuarios contra MySQL.
- Consulta de repositorios de GitHub.
- Consulta de seguidores de GitHub.
- Listado de usuarios conectados.
- Desconexión de clientes.

## Requisitos

- Python 3.x
- MySQL
- Librerías indicadas en requirements.txt

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

Servidor:

```bash
python servidor.py
```

Cliente:

```bash
python cliente.py
```

## Comandos disponibles

/repos usuarioGithub

/followers usuarioGithub

/usuarios

/adios

## Mensajes sin comando:
Cualquier mensaje que no esté precedido por / se interpreta como un mensaje de chat. 
El servidor lo recibe, lo muestra en consola y permite al operador responder directamente al cliente.

## Hecho por: Valeria Moreno - @valeriavmr