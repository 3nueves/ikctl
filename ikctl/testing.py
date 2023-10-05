# 1.- Cargar archivo desde la $HOME/.ikctl
# 2.- Comprobar que existe el directorio $HOME/.ikctl
# 3.- Si no existe crearlo y añadir el fichero "$HOME/.ikctl/config"
# 4.- Avisar que no hay ninguna ruta para cargar kits y servers
# 5.- Si existe el fichero cargarlo

from os import path


p = "/home/dml/git"

# Devuelve la segunda parte de la ruta
print(path.basename(p))
print(path.dirname(p))

print()

print(path.basename(p).split())
# Devuelve la primera parte de la ruta
print(path.dirname(p).split())

print()

PATHS = [
    ('one', 'two', 'three'),
    ('/', 'one', 'two', 'three'),
    ('/one', '/two', '/three'),
]

for parts in PATHS:
    print('{} : {!r}'.format(parts, path.join(*parts)))

print('\npathlib\n')

import pathlib

usr = pathlib.PurePosixPath('/usr')
print(usr)

usr_local = usr / 'local'
print(usr_local)

usr_share = usr / pathlib.PurePosixPath('share')
print(usr_share)

root = usr / '..'
print(root)

etc = root / '/etc/'
print(etc,'\n')

usr_local = pathlib.Path('/usr/local')
share = usr_local / '..' / 'share'
print(share.resolve())

print()

root = pathlib.PurePosixPath('/')
subdirs = ['usr', 'local']
usr_local = root.joinpath(*subdirs)
print(usr_local)

print()

home = pathlib.Path.home()
print('home: ', home)

cwd = pathlib.Path.cwd()
print('cwd : ', cwd)

config = home.joinpath('.kube')
p = config.joinpath('config')

if p:
    print("file exist")
else:
    raise("Config File Not Found")

print(p)


p = pathlib.Path(config)

for f in config.iterdir():
    print(f)

p = pathlib.Path(config)

for f in p.glob('config_dani'):
    print(f)

pathh = path.realpath(path.join(path.dirname(__file__)))

patth = pathlib.Path.cwd()

print(path.basename((__file__)))

print(pathh)
print(patth)