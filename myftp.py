import socket
import time
import os

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

    if not path:
      line = input('Remote directory ').split()

      if not line:
        print('cd remote directory.')
        return
      
      path = line[0]

    self.send_cmd(f'CWD {path}')
    print(self.get_response(), end="")

  def rename(self, filename = None, new_filename = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return

    if not filename:
      user_input = input('From name ').split()
      if len(user_input) == 0:
        print('Usage: rename from-name to-name')
        return

      filename = user_input[0]

      if len(user_input) >= 2:
        new_filename = user_input[1]


    if not new_filename:
      new_filename = input('To name ').split()[0]

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

  def delete(self, filename = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return

    if not filename:
      line = input('Remote file ').split()
      
      if not line:
        print('delete remote file.')
        return
    
      filename = line[0]

    self.send_cmd(f'DELE {filename}')
    print(self.get_response(), end="")

  def ls(self, remote_dir = None, local_file = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return

    data_socket, resp = self.init_data_connection()
    print(resp, end="")

    if not resp.startswith('200'):
      return
    
    self.send_cmd(f'NLST {remote_dir}' if remote_dir else 'NLST')
    resp = self.get_response()

    print(resp, end="")

    if resp.startswith('550'):
      data_socket.close()
      return
    
    elif resp.startswith('150'):
      if local_file:
        local_path = os.path.join(os.getcwd(), local_file)
  
        try:
          with open(local_path, 'wb') as f:
            pass

        except PermissionError as e:
          data_socket.close()
          print(f"Error opening local file {local_file}.\n> {local_file[0]}: Permission denied")
          return
          
        except FileNotFoundError as e:
          data_socket.close()
          print(f"Error opening local file {local_file}.\n> {local_file[0]}:No Such file or directory")
          return

        
      data_conn, _ = data_socket.accept()
      start_time = time.time()
      size = 0
      
      while True:
        data = data_conn.recv(1024)
        if not data:
          break

        if local_file:
          with open(local_path, 'ab') as f:
            f.write(data)
        else:
          print(data.decode(), end="")

        size += len(data)

      end_time = time.time()

      data_conn.close()
      data_socket.close()

      print(self.get_response(), end="")
      self.print_performance(size, start_time, end_time)
    
    else:
      data_socket.close()
      return
    
  def get(self, remote_file = None, local_file = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return   
    
    mode = 0

    if not remote_file:
      line = input('Remote file ').split()
      
      if not line:
        print('Remote file get [ local-file ].')
        return
    
      remote_file = line[0]

      mode = 1

    if not local_file and mode == 1:
      local_file = input('Local file ').split()

      local_file = local_file[0] if local_file else None

    if not local_file: 
      local_file = remote_file

    data_socket, resp = self.init_data_connection()

    print(resp, end="")

    if not resp.startswith('200'):
      data_socket.close()
      return
    
    if resp.startswith('200'):
      self.send_cmd(f'RETR {remote_file}')
      resp = self.get_response()

      print(resp, end="")

      if resp.startswith('550'):
        data_socket.close()
        return
      
      elif resp.startswith('150'): 
        local_path = os.path.join(os.getcwd(), local_file)

        try:
          with open(local_path, 'wb') as f:
            pass

        except PermissionError as e:
          data_socket.close()
          print(f"Error opening local file {local_file}.\n> {local_file[0]}: Permission denied")
          return

        except FileNotFoundError as e:
          data_socket.close()
          print(f"Error opening local file {local_file}.\n> {local_file[0]}: No such file or directory")
          return
        
        data_conn, _ = data_socket.accept()
        start_time = time.time()
        size = 0
        
        while True:
          data = data_conn.recv(1024)
          if not data:
            break

          with open(local_path, 'ab') as f:
            f.write(data)

          size += len(data)

        end_time = time.time()

        data_conn.close()
        data_socket.close()

        print(self.get_response(), end="")

        self.print_performance(size, start_time, end_time)

      else:
        data_socket.close()
        return

  def put(self, local_file = None, remote_file = None, *args):
    if not self.socket_is_connected():
      print('Not connected.')
      return   

    if not local_file:
      line = input('Local file ').split()

      if not line:
        print('Local file put: remote file.')
        return
      
      local_file = line[0]
      
    if not remote_file:
      line = input('Remote file ').split()

      if not line:
        remote_file = local_file
      else:
        remote_file = line[0]

    data_socket, resp = self.init_data_connection()

    local_path = os.path.join(os.getcwd(), local_file)
    
    try:
      with open(local_path, 'rb') as f:
        pass

    except FileNotFoundError as e:
      data_socket.close()
      print(f"{local_file}: File not found")
      return

    print(resp, end="")

    if not resp.startswith('200'):
      data_socket.close()
      return
    
    if resp.startswith('200'):
      self.send_cmd(f'STOR {remote_file}')
      resp = self.get_response()

      print(resp, end="")

      if resp.startswith('550'):
        data_socket.close()
        return
      
      elif resp.startswith('150'): 
        try:
          with open(local_path, 'rb') as f:
            pass

        except FileNotFoundError as e:
          data_socket.close()
          print(f"{local_file}: File not found")
          return
        
        data_conn, _ = data_socket.accept()
        start_time = time.time()
        size = 0
        
        with open(local_path, 'rb') as f:
          while True:
            data = f.read(1024)
            if not data:
              break

            data_conn.send(data)
            size += len(data)

        end_time = time.time()

        data_conn.close()
        data_socket.close()

        print(self.get_response(), end="")

        self.print_performance(size, start_time, end_time)

      else:
        data_socket.close()
        return
    
  # TODO: handle case zero division error
  def print_performance(self, size, start_time, end_time):
    delta_time = end_time - start_time
    throughput = size / 1024 / (delta_time + 1e-10)

    print(f'ftp: {size} bytes sent in {delta_time:.2f}Seconds {throughput:.2f}Kbytes/sec.')

  def init_data_connection(self):
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = self.client_socket.getsockname()[0]
    formatted_host = host.replace('.', ',')

    data_socket.settimeout(10 )
    data_socket.bind((host, 0))
    data_socket.listen(1)

    port = data_socket.getsockname()[1]

    self.send_cmd(f'PORT {formatted_host},{port // 256},{port % 256}')

    resp = self.get_response()

    return data_socket, resp

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
    elif command == 'delete':
      my_ftp.delete(*arguments)
    elif command == 'ls':
      my_ftp.ls(*arguments)
    elif command == 'get':
      my_ftp.get(*arguments)
    elif command == 'put':
      my_ftp.put(*arguments)
    else:
      print('Invalid command.')
      continue


if __name__ == '__main__':
  main()