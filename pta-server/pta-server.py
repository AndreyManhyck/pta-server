"""Servidor do Protocolo de Transferencia de Arquivos (PTA).

Uso: python pta-server.py [porta]
"""
import os
import socket
import sys
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.txt")
FILES_DIR = os.path.join(BASE_DIR, "files")

HOST = "0.0.0.0"
DEFAULT_PORT = 11550
BUFFER_SIZE = 4096


def load_users():
    # strip() tambem remove o \r de arquivos salvos com quebra de linha CRLF
    with open(USERS_FILE, encoding="ascii") as users:
        return {line.strip() for line in users if line.strip()}


def list_files():
    return sorted(
        name for name in os.listdir(FILES_DIR)
        if os.path.isfile(os.path.join(FILES_DIR, name))
    )


def reply(seq, text):
    return f"{seq} {text}".encode("ascii", "replace")


def handle_cump(seq, args):
    """Estado Esperando. Retorna (resposta, usuario_aceito)."""
    try:
        accepted = len(args) == 1 and args[0] in load_users()
    except (OSError, UnicodeDecodeError):
        accepted = False
    return reply(seq, "OK" if accepted else "NOK"), accepted


def handle_list(seq, args):
    if args:
        return reply(seq, "NOK")
    try:
        names = list_files()
    except OSError:
        return reply(seq, "NOK")
    return reply(seq, f"ARQS {len(names)} {','.join(names)}")


def handle_pega(seq, args):
    # A especificacao permite um arquivo por vez: os pedidos a mais sao ignorados
    if not args:
        return reply(seq, "NOK")
    name = args[0]
    try:
        # So aceitar nomes da listagem impede caminhos como ../users.txt
        if name not in list_files():
            return reply(seq, "NOK")
        with open(os.path.join(FILES_DIR, name), "rb") as requested:
            data = requested.read()
    except OSError:
        return reply(seq, "NOK")
    # O espaco antes dos dados e mantido mesmo quando o arquivo esta vazio
    return reply(seq, f"ARQ {len(data)} ") + data


def process_message(message, ready):
    """Aplica a maquina de estados.

    Retorna (resposta, novo_estado_pronto, fechar_conexao).
    """
    fields = message.split(" ")
    seq = fields[0] or "0"
    valid = len(fields) >= 2 and seq.isascii() and seq.isdigit()
    command = fields[1] if valid else None
    args = fields[2:]

    if not ready:
        if command == "CUMP":
            response, accepted = handle_cump(seq, args)
            return response, accepted, not accepted
        return reply(seq, "NOK"), False, True

    if command == "LIST":
        return handle_list(seq, args), True, False
    if command == "PEGA":
        return handle_pega(seq, args), True, False
    if command == "TERM" and not args:
        return reply(seq, "OK"), True, True
    return reply(seq, "NOK"), True, False


def split_messages(data):
    # O cliente de teste nao usa terminador, mas outros clientes podem usar \n ou \r\n
    text = data.decode("ascii", "replace")
    messages = [line.rstrip("\r") for line in text.split("\n")]
    return [message for message in messages if message] or [""]


def handle_client(conn, addr):
    print(f"[{addr[0]}:{addr[1]}] conexao aberta")
    ready = False
    closing = False
    try:
        while not closing:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            # Cada mensagem e respondida por inteiro antes da proxima (atomicidade)
            for message in split_messages(data):
                response, ready, closing = process_message(message, ready)
                conn.sendall(response)
                print(f"[{addr[0]}:{addr[1]}] {message!r} -> {response[:40]!r}")
                if closing:
                    break
    except OSError as error:
        print(f"[{addr[0]}:{addr[1]}] erro de conexao: {error}")
    finally:
        conn.close()
        print(f"[{addr[0]}:{addr[1]}] conexao fechada")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # No Windows, SO_REUSEADDR deixaria dois servidores usarem a mesma porta
        if os.name != "nt":
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, port))
        server.listen()
        # O timeout permite interromper o accept com Ctrl+C tambem no Windows
        server.settimeout(1.0)
        print(f"Servidor PTA ouvindo em {HOST}:{port} (Ctrl+C para encerrar)")
        try:
            while True:
                try:
                    conn, addr = server.accept()
                except socket.timeout:
                    continue
                threading.Thread(
                    target=handle_client, args=(conn, addr), daemon=True
                ).start()
        except KeyboardInterrupt:
            print("Servidor encerrado")


if __name__ == "__main__":
    main()
