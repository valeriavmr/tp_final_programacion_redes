import socket
import threading
import mysql.connector
import requests
from datetime import datetime

# Diccionario global para rastrear clientes activos: { usuario: cliente_socket }
clientes_conectados = {}
# Candado (Lock) para evitar fallos de concurrencia al modificar el diccionario global
clientes_lock = threading.Lock()

# FUNCIÓN PARA VALIDAR CREDENCIALES EN MYSQL
# Cada hilo abre su propia conexión para garantizar la concurrencia segura
def validar_credenciales(usuario, password):
    try:
        # Usamos los datos de conexión que proporcionaste
        conexion = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            password = '',
            database = 'sockets'
        )
        cursor = conexion.cursor()
        
        # Query para revisar si existe un usuario con esas credenciales
        query = "SELECT * FROM usuarios WHERE usuario = %s AND password = %s"
        cursor.execute(query, (usuario, password))
        usuario_encontrado = cursor.fetchone()
        
        cursor.close()
        conexion.close()
        
        return usuario_encontrado is not None
        
    except mysql.connector.Error as error:
        print(f"[ERROR BD] Error al conectar o consultar MySQL: {error}")
        return False
    
#FUNCION PARA GUARDAR REPOSITORIOS DE GITHUB
def guardar_repositorios(usuario_github, lista_repos):
    try:
        conexion = mysql.connector.connect(
            host='localhost', user='root', password='', database='sockets'
        )
        cursor = conexion.cursor()
        
        # 1. Preparamos una lista de tuplas con todos los datos juntos
        datos_a_insertar = []
        for repo in lista_repos:
            nombre_repo = repo['name']
            datos_a_insertar.append((usuario_github, nombre_repo))
        
        # 2. Hacemos una única operación masiva en la base de datos
        if datos_a_insertar:
            query = "INSERT INTO repositorios (usuario_github, nombre_repo) VALUES (%s, %s)"
            cursor.executemany(query, datos_a_insertar)
            conexion.commit()
            print(f"[BD SUCCESS] Insertados {len(datos_a_insertar)} repositorios para {usuario_github}")
        
        cursor.close()
        conexion.close()
    except mysql.connector.Error as e:
        print(f"[ERROR BD] No se guardaron los repos: {e}")


#FUNCION PARA GUARDAR SEGUIDORES DE GITHUB
def guardar_followers(usuario_github, lista_followers):
    try:
        conexion = mysql.connector.connect(
            host='localhost', user='root', password='', database='sockets'
        )
        cursor = conexion.cursor()
        
        datos_a_insertar = []
        for follower in lista_followers:
            follower_login = follower['login']
            datos_a_insertar.append((usuario_github, follower_login))
            
        if datos_a_insertar:
            query = "INSERT INTO followers (usuario_github, follower_login) VALUES (%s, %s)"
            cursor.executemany(query, datos_a_insertar)
            conexion.commit()
            print(f"[BD SUCCESS] Insertados {len(datos_a_insertar)} seguidores para {usuario_github}")
            
        cursor.close()
        conexion.close()
    except mysql.connector.Error as e:
        print(f"[ERROR BD] No se guardaron los followers: {e}")

# MANEJO DEL CLIENTE (Hilos secundarios)
def manejar_cliente(cliente_socket, direccion):
    usuario = None
    try:
        # FASE DE AUTENTICACIÓN
        credenciales = cliente_socket.recv(1024).decode('utf-8')
        if not credenciales or "," not in credenciales:
            cliente_socket.send("ERROR: Formato incorrecto".encode('utf-8'))
            cliente_socket.close()
            return

        usuario, contrasena = credenciales.split(",")
        
        if not validar_credenciales(usuario, contrasena):
            cliente_socket.send("RECHAZADO: Credenciales inválidas".encode('utf-8'))
            cliente_socket.close()
            return
        
        # Guardar al usuario en el registro global de conectados de forma segura
        with clientes_lock:
            if usuario in clientes_conectados:
                cliente_socket.send("RECHAZADO: Usuario ya tiene una sesión activa".encode('utf-8'))
                cliente_socket.close()
                return
            clientes_conectados[usuario] = cliente_socket
            
        cliente_socket.send("OK: Autenticación exitosa".encode('utf-8'))
        print(f"[CONECTADO] {usuario} inició sesión.")

        # FASE DE COMUNICACIÓN Y PROCESAMIENTO DE COMANDOS
        while True:
            mensaje = cliente_socket.recv(1024).decode('utf-8')
            if not mensaje:
                break
            
            # Comando a) /repos usuario
            if mensaje.startswith("/repos "):
                # Cortamos el texto quitando la palabra "/repos" y limpiamos espacios
                usuario_github = mensaje[6:].strip() 
                
                if not usuario_github:
                    cliente_socket.send("ERROR: Falta el usuario. Ej: /repos valeriavmr".encode('utf-8'))
                    continue
                
                url = f"https://api.github.com/users/{usuario_github}/repos"
                print(f"Hola! La URL es: {url}")
                
                try:
                    respuesta_api = requests.get(url, headers={'User-Agent': 'Python-Socket-App'}, timeout=5)
                    
                    if respuesta_api.status_code == 200:
                        repos = respuesta_api.json()
                        guardar_repositorios(usuario_github, repos)
                        cliente_socket.send(f"OK: Se guardaron {len(repos)} repositorios de {usuario_github}.".encode('utf-8'))
                    elif respuesta_api.status_code == 403:
                        cliente_socket.send("ERROR: Límite de peticiones de GitHub excedido (Rate Limit). Intenta más tarde.".encode('utf-8'))
                    else:
                        cliente_socket.send(f"ERROR: GitHub respondió código {respuesta_api.status_code}. ¿El usuario existe?".encode('utf-8'))
                
                except requests.exceptions.Timeout:
                    cliente_socket.send("ERROR: La API de GitHub tardó demasiado en responder (Timeout).".encode('utf-8'))
                except Exception as e:
                    cliente_socket.send(f"ERROR interno al procesar la API: {str(e)}".encode('utf-8'))

            # Comando b) /followers usuario
            elif mensaje.startswith("/followers "):
                #Cortamos el texto quitando la palabra "/followers" y limpiamos espacios
                usuario_github = mensaje[10:].strip()
                
                if not usuario_github:
                    cliente_socket.send("ERROR: Falta el usuario. Ej: /followers valeriavmr".encode('utf-8'))
                    continue
                
                #url para consultar la API
                url = f"https://api.github.com/users/{usuario_github}/followers"
                
                try:
                    respuesta_api = requests.get(url, headers={'User-Agent': 'Python-Socket-App'}, timeout=5)
                    
                    if respuesta_api.status_code == 200:
                        followers = respuesta_api.json()
                        guardar_followers(usuario_github, followers)
                        cliente_socket.send(f"OK: Se guardaron {len(followers)} followers de {usuario_github}.".encode('utf-8'))
                    elif respuesta_api.status_code == 403:
                        cliente_socket.send("ERROR: Límite de peticiones de GitHub excedido.".encode('utf-8'))
                    else:
                        cliente_socket.send(f"ERROR: GitHub respondió código {respuesta_api.status_code}.".encode('utf-8'))
                        
                except requests.exceptions.Timeout:
                    cliente_socket.send("ERROR: Tiempo de espera agotado con GitHub.".encode('utf-8'))
                except Exception as e:
                    cliente_socket.send(f"ERROR interno: {str(e)}".encode('utf-8'))

            # Comando c) /hora
            elif mensaje.strip() == "/hora":
                hora_actual = datetime.now().strftime("%H:%M:%S")
                cliente_socket.send(f"Hora del servidor: {hora_actual}".encode('utf-8'))

            # Comando d) /todos "mensaje"
            elif mensaje.startswith("/todos "):
                texto_difusion = mensaje[7:] # Cortamos el "/todos " del inicio
                mensaje_formateado = f"[DIFUSIÓN de {usuario}]: {texto_difusion}"
                
                # Enviamos el mensaje a absolutamente todos los sockets guardados, excepto a nosotros mismos si se prefiere
                with clientes_lock:
                    for u, sock in clientes_conectados.items():
                        try:
                            sock.send(mensaje_formateado.encode('utf-8'))
                        except Exception:
                            pass # Manejo de sockets caídos
                cliente_socket.send("Mensaje de difusión enviado con éxito.".encode('utf-8'))
            
            # Comando e) /usuarios
            elif mensaje.strip() == "/usuarios":
                with clientes_lock:
                    lista_usuarios = ", ".join(clientes_conectados.keys())
                cliente_socket.send(f"Usuarios conectados: {lista_usuarios}".encode('utf-8'))

            # Comando f) /adios o comando de desconexión
            elif mensaje.strip() == "/adios":
                cliente_socket.send("Hasta luego: Desconexión exitosa.".encode('utf-8'))
                break # Rompe el bucle 'while', saltando directo al bloque 'finally' para limpiar todo

            else:
                cliente_socket.send("Comando no reconocido.".encode('utf-8'))

    except Exception as e:
        print(f"[ERROR] Conexión interrumpida con {usuario}: {e}")
    finally:
        # Remover al cliente del registro al desconectarse
        if usuario:
            with clientes_lock:
                if usuario in clientes_conectados:
                    del clientes_conectados[usuario]
        print(f"[DESCONECTADO] Conexión cerrada con {usuario}")
        cliente_socket.close()

# FUNCIÓN PRINCIPAL DEL SERVIDOR
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOST = '127.0.0.1'
    PUERTO = 10000
    
    servidor.bind((HOST, PUERTO))
    servidor.listen()
    print(f"[SERVIDOR ESCUCHANDO] Esperando conexiones en {HOST}:{PUERTO}")
    
    try:
        while True:
            cliente_socket, direccion = servidor.accept()
            hilo = threading.Thread(target=manejar_cliente, args=(cliente_socket, direccion))
            hilo.start()
    except KeyboardInterrupt:
        print("[SERVIDOR DETENIDO]")
    finally:
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()