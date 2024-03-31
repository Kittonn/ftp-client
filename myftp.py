import socket

class MyFTP:
  def __init__(self):
    self.client_socket = None

  def open(self, host = None, port = 21, *args):
    # check if already connected
    if self.client_socket:
      print(f'Already connected to {host}, use disconnect first.')
      return

    if args:
      print('Usage: open host name [port]')
      return

    if not host:
      line = input('To: ').strip().split()

      if len(line) > 2 or len(line) == 0:
        print('Usage: open host name [port]')
        return

      host = line[0]
      port = line[1] if len(line) == 2 else port
    
    try:
      # connect to host
      self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.client_socket.connect((host, int(port)))
      
      print(f'Connected to {host}.')
      print(self.get_response(), end="")

      # set utf8 encoding 
      self.send_cmd('OPTS UTF8 ON')
      print(self.get_response(), end="")

    # TODO: Handle exceptions for error cases
    except socket.timeout as e:
      print('> ftp: connect :Connection timed out')

    except Exception as e:
      print(e)
      return
    
    user = input(f'User ({host}:(none)): ')
    self.send_cmd(f'USER {user}')
    resp = self.get_response()
    print(resp, end="")

    resp_code = resp.split()[0]

    # username is null
    if resp.startswith('501'):
      print('Login failed.')
      return
    
    # request password
    if resp.startswith('331'):
      password = input('Password: ')
      self.send_cmd(f'PASS {password}')
      resp = self.get_response()
      
      print(resp, end="") 

      # password is null or invalid
      if resp.startswith('530'):
        print('Login failed.')
        return
      
      # login successful
      elif resp.startswith('230'):
        return

  def disconnect(self):
    if not self.socket_is_connected():
      print('Not connected.')
      return
    
    self.send_cmd('QUIT')
    print(self.get_response(), end="")
    self.close_socket()
      
  def quit(self):
    if self.socket_is_connected():
      self.send_cmd('QUIT')
      print(self.get_response(), end="")
      self.close_socket()
    
    exit()

  def pwd(self):
    if not self.socket_is_connected():
      print('Not connected.')
      return
    
    self.send_cmd('XPWD')
    print(self.get_response(), end="")
    
  def ascii(self):
    if not self.socket_is_connected():
      print('Not connected.')
      return
    
    self.send_cmd('TYPE A')
    print(self.get_response(), end="")

  def binary(self):
    if not self.socket_is_connected():
      print('Not connected.')
      return
    
    self.send_cmd('TYPE I')
    print(self.get_response(), end="")

  def cd(self, path = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return

    path = path if path else input('Remote directory ').strip()

    self.send_cmd(f'CWD {path}')
    print(self.get_response(), end="")

  def rename(self, filename = None, new_filename = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return

    if not filename:
      filename = input('From name ').strip()

    if not new_filename:
      new_filename = input('To name ').strip()

    # check for valid filenames
    self.send_cmd(f'RNFR {filename}')
    resp = self.get_response()

    print(resp, end="")

    # check if file exists
    if resp.startswith('350'):
      # rename file
      self.send_cmd(f'RNTO {new_filename}')
      print(self.get_response(), end="")

    return

  def user(self, username = None, password = None):
    if not self.socket_is_connected():
      print('Not connected.')
      return
    
    # request username
    if not username:
      username = input('Username ')

    # username is null
    if not username:
      print('Usage: user username [password] [account]')
      return

    self.send_cmd(f'USER {username}')
    resp = self.get_response()

    print(resp, end="")

    if resp.startswith('331'):
      # request password
      if not password:
        password = input('Password: ')

      self.send_cmd(f'PASS {password}')
      resp = self.get_response()

      print(resp, end="")

      # login successful
      if resp.startswith('230'):
        return
      
      # password is null or invalid
      elif resp.startswith('530'):
        print('Login failed.')
        return

  def socket_is_connected(self):
    return self.client_socket is not None and self.client_socket.fileno() != -1

  def send_cmd(self, cmd):
    self.client_socket.send(f'{cmd}\r\n'.encode())
    
  def get_response(self):
    return self.client_socket.recv(1024).decode()
  
  def close_socket(self):
    self.client_socket.close()
    self.client_socket = None

def main():
  my_ftp = MyFTP()

  while True:
    line = input('ftp> ')

    if not line:
      continue

    args = line.strip().split()

    if len(args) == 0:
      print('Invalid command.')
      continue

    command = args[0]
    arguments = args[1:]

    # command can be lower case or upper case or mixed case
    if command in ['quit', 'bye']:
      my_ftp.quit()
    elif command == 'open':
      my_ftp.open(*arguments)
    elif command in ['disconnect', 'close']:
      my_ftp.disconnect()
    elif command == 'pwd':
      my_ftp.pwd()
    elif command == 'ascii':
      my_ftp.ascii()
    elif command == 'binary':
      my_ftp.binary()
    elif command == 'cd':
      my_ftp.cd(*arguments)
    elif command == 'rename':
      my_ftp.rename(*arguments)
    elif command == 'user':
      my_ftp.user(*arguments)
    else:
      print('Invalid command.')
      continue


if __name__ == '__main__':
  main()