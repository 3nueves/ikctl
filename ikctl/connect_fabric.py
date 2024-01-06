from fabric import Connection
from invoke import Responder

c = Connection('kub@10.10.0.101')

# c.run('pwd', pty=True)

sudopass = Responder(pattern=r'\[sudo\] password:',response='changeme01\n',)

c.run('sudo whoami', pty=True, watchers=[sudopass])

