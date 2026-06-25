import socket
import threading

# Función que escucha constantemente mensajes del servidor
def recibir_mensajes(cliente):
    while True:
        try:
            mensaje = cliente.recv(1024).decode('utf-8')

            # Si el servidor cerró la conexión
            if not mensaje:
                print("\n[INFO] El servidor cerró la conexión.")
                break

            print(f"\n{mensaje}")

        except:
            print("\n[ERROR] Se perdió la conexión con el servidor.")
            break

def iniciar_cliente():
    HOST = '127.0.0.1'
    PUERTO = 10000

    #Inicializo el socket
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente.connect((HOST, PUERTO))
    except Exception as e:
        print(f"[ERROR] No se pudo conectar al servidor: {e}")
        return

    # =========================
    # FASE DE AUTENTICACIÓN
    # =========================

    print("--- INICIO DE SESIÓN ---")

    #Pido el usuario y contraseña
    usuario = input("Usuario: ")
    contrasena = input("Contraseña: ")

    #Los envío al servidor para ser validados
    datos_login = f"{usuario},{contrasena}"
    cliente.send(datos_login.encode('utf-8'))

    #Recibo la respuesta de la validación y si es un rechazo, cierro la conexión
    respuesta_auth = cliente.recv(1024).decode('utf-8')
    print(f"[SERVIDOR] {respuesta_auth}")

    if respuesta_auth.startswith("RECHAZADO") or respuesta_auth.startswith("ERROR"):
        cliente.close()
        return

    # =========================
    # HILO RECEPTOR
    # =========================

    #Creo un hilo para que el cliente también pueda recibir mensajes
    hilo_receptor = threading.Thread(target=recibir_mensajes,args=(cliente,),daemon=True)
    hilo_receptor.start()

    # =========================
    # FASE DE COMANDOS
    # =========================

    print("\n--- BIENVENIDO AL SISTEMA DE COMANDOS ---")
    print("Comandos disponibles:")
    print("/repos [usuario]")
    print("/followers [usuario]")
    print("/hora")
    print("/todos [mensaje]")
    print("/usuarios")
    print("/adios")

    try:
        while True:
            mensaje = input(f"\n[{usuario}]: ")

            if not mensaje.strip():
                continue
            
            cliente.send(mensaje.encode('utf-8'))

            if mensaje.strip() == "/adios":
                print("Desconectando del servidor...")
                break

    except KeyboardInterrupt:
        print("\nDesconectando...")

    except Exception as e:
        print(f"\n[ERROR] {e}")

    finally:
        cliente.close()
        print("Programa cliente finalizado.")

if __name__ == "__main__":
    iniciar_cliente()