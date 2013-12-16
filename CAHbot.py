import sys
import socket
import string
import os
import pickle
import random

HOST = 'asimov.freenode.net'
PORT = 6667
NICK = 'CAHbot1'
IDENT= 'CAHbot'
REALNAME = 'CAHbot'
OWNER = 'lane'
CHANNELINIT = '#testedCAH'
readbuffer = ''
s = socket.socket()
s.connect((HOST, PORT))
s.send("NICK %s\r\n" %NICK)
s.send("USER %s %s bla :%s\r\n" %(IDENT, HOST, REALNAME))
s.send('JOIN %s\r\n' %CHANNELINIT)

def parsemsg(msg):
    #useful variables:#
    #info[2]=channel user types command in#
    #sender[0]=user's name#
    #if a user types "@hello" it originally looks like this:#
    #:lane!~lane@dsl.lgvwtx.sbcglobal.net PRIVMSG #testedCAH :`hello#
    complete = msg[1:].split(':', 1)
    #['lane!~lane@dsl.lgvwtx.sbcglobal.net PRIVMSG #testedCAH ', '`hello\r\n']#
    info = complete[0].split(' ')
    #['lane!~lane@dsl.lgvwtx.sbcglobal.net', 'PRIVMSG', '#testedCAH', '']#
    msgpart = complete[1]
    #'`hello#
    sender=info[0].split('!')
    #['lane', '~lane@dsl.lgvwtx.sbcglobal.net']#
    if msgpart[0]=='@':
        cmd = msgpart[1:].split(' ')
        #['hello']#
        cmd[0] = cmd[0].rstrip()
        if cmd[0]=='hello':
            s.send('PRIVMSG %s :hi %s!\r\n' %(CHANNELINIT, sender[0]))


while 1:
    line=s.recv(500)
    print line
    if line.find('#testedCAH :End')!=-1:
        s.send('PRIVMSG %s :Here I am!\r\n' %CHANNELINIT)
    if line.find('PRIVMSG')!=-1:
        parsemsg(line)
        line=line.rstrip()
        line=line.split(':')
        if(line[0]=='PING'):
            s.send('PONG %s\r\n'%line[1])
    
