import socket

def iniciar_cliente():
    HOST = '127.0.0.1'
    PUERTO = 10000
    
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect((HOST, PUERTO))
    
    # FASE DE AUTENTICACIÓN
    print("--- INICIO DE SESIÓN ---")
    usuario = input("Usuario: ")
    contrasena = input("Contraseña: ")
    
    datos_login = f"{usuario},{contrasena}"
    cliente.send(datos_login.encode('utf-8'))
    
    respuesta_auth = cliente.recv(1024).decode('utf-8')
    print(f"[SERVIDOR] {respuesta_auth}")
    
    if respuesta_auth.startswith("RECHAZADO") or respuesta_auth.startswith("ERROR"):
        cliente.close()
        return

    # FASE DE COMANDOS
    print("\n--- BIENVENIDO AL SISTEMA DE COMANDOS ---")
    print("Comandos: /repos [user], /followers [user], /hora, /todos [msg], /usuarios, /adios")
    
    try:
        while True:
            mensaje = input(f"\n[{usuario}]> ")
            if not mensaje.strip():
                continue
                
            # Enviamos el comando al servidor
            cliente.send(mensaje.encode('utf-8'))
            
            # Recibimos la respuesta del servidor
            respuesta = cliente.recv(1024).decode('utf-8')
            print(f"[SERVIDOR]: {respuesta}")
            
            # Si enviamos la opción f) y el servidor confirma, cerramos el programa cliente
            if mensaje.strip() == "/adios":
                print("Desconectando del servidor de forma segura...")
                break
                
    except ConnectionResetError:
        print("\n[ERROR] Se perdió la conexión abruptamente con el servidor.")
    finally:
        cliente.close()
        print("Programa cliente finalizado.")

if __name__ == "__main__":
    iniciar_cliente()