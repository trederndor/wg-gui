#!/usr/bin/env python3
import os
import subprocess
import base64
import re
import qrcode
import io
from flask import Flask, render_template_string, request, redirect, url_for, send_file, flash, jsonify

app = Flask(__name__)
app.secret_key = 'cambia_questa_chiave_per_la_produzione' # cambia_questa_chiave_per_la_produzione
WG_CONFIG_DIR = f"/home/{user}/configs"                    # sostituire "{user}" con l'utente di installazione di pivpn/wireguard es. /home/root/configs or /home/john/configs solo se errato nativamente
WG_SERVICE_NAME = "wg-quick@wg0"                          #lasciare cosi se non si cambia il nome del processo

BASE_HTML = """
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WireGuard PiVPN</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    body { padding-top: 4rem; background: #f4f6f9; }
    .container { max-width: 1000px; }
    .card { border-radius: 1rem; }
    .navbar-brand { font-weight: bold; font-size: 1.3rem; }
    pre { background: #fff; padding: 1rem; border-radius: 0.75rem; border: 1px solid #dee2e6; }
    textarea { font-family: monospace; }
    .btn-action {
      min-width: unset !important;
      padding: 0.25rem 0.5rem !important;
      font-size: 0.85rem;
      border-width: 2px;
      transition: all 0.2s ease-in-out;
    }
    .btn-action:hover { transform: scale(1.05); opacity: 0.9; }
    .table-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.3rem; }
    .badge { font-size: 0.85rem; padding: 0.45em 0.7em; }
  </style>
</head>
<body>
<nav class="navbar navbar-expand-md navbar-dark bg-primary fixed-top shadow-sm">
  <div class="container-fluid">
    <a class="navbar-brand" href="{{ url_for('index') }}"><i class="bi bi-shield-lock"></i> WireGuard PiVPN</a>
  </div>
</nav>

<div class="container mt-4">
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="alert alert-info shadow-sm">{{ messages|join('<br>')|safe }}</div>
    {% endif %}
  {% endwith %}
  {{ content|safe }}
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
async function updateClientStatus(){
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    data.forEach(c=>{
      const b = document.querySelector('#status-'+c.name);
      if(b){
        b.className = 'badge';
        if(c.status==='ONLINE'){ b.classList.add('bg-success'); b.textContent='ONLINE'; }
        else if(c.status==='OFFLINE'){ b.classList.add('bg-danger'); b.textContent='OFFLINE'; }
        else { b.classList.add('bg-secondary'); b.textContent=c.status; }
      }
    });
  } catch(e){ console.error(e); }
}

async function updateWGStatus(){
  try {
    const res = await fetch('/api/wg_status');
    const data = await res.json();
    const pre = document.getElementById('wg-status');
    if(pre) pre.textContent = data.wg_named;
  } catch(e){ console.error(e); }
}

function startPolling(){
  updateClientStatus();
  updateWGStatus();
  setInterval(()=>{
    updateClientStatus();
    updateWGStatus();
  },2000);
}
document.addEventListener('DOMContentLoaded', startPolling);
</script>
</body>
</html>
"""

def generate_qr_code_base64(data):
  qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L); qr.add_data(data); qr.make(fit=True)
  img=qr.make_image(fill_color="black", back_color="white")
  buf=io.BytesIO(); img.save(buf, format="PNG")
  return base64.b64encode(buf.getvalue()).decode()

def safe_name(name):
  return re.sub(r'[^a-zA-Z0-9_\\-]', '', name)

def client_conf_path(name):
  return os.path.join(WG_CONFIG_DIR, f"{safe_name(name)}.conf")

def extract_pubkey(conf_path):
  try:
    with open(conf_path) as f: cont=f.read()
    m=re.search(r"PublicKey\\s*=\\s*(.+)",cont)
    if m: return m.group(1).strip()
    m2=re.search(r"PrivateKey\\s*=\\s*(.+)",cont)
    if m2:
      p=subprocess.run(['wg','pubkey'], input=m2.group(1).strip().encode(), capture_output=True)
      if p.returncode==0: return p.stdout.decode().strip()
  except: pass
  return None

def get_client_ip(conf_path):
  try:
    with open(conf_path) as f:
      for line in f:
        if line.strip().startswith("Address"):
          return line.split('=',1)[1].strip().split('/')[0]
  except: pass
  return None

def check_online(ip):
  if not ip: return "UNKNOWN"
  try:
    r=subprocess.run(["ping","-I","wg0","-c","1","-W","1",ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "ONLINE" if r.returncode==0 else "OFFLINE"
  except: return "ERROR"

def list_clients():
  if not os.path.isdir(WG_CONFIG_DIR): return []
  clients=[]
  for f in os.listdir(WG_CONFIG_DIR):
    if f.endswith(".conf"):
      name=f[:-5]; path=os.path.join(WG_CONFIG_DIR,f)
      pubkey=extract_pubkey(path); ip=get_client_ip(path); status = "UNKNOWN"
      clients.append({'name':name,'path':path,'pubkey':pubkey,'ip':ip,'status':status})
  return sorted(clients, key=lambda c:c['name'].lower())

def wg_status():
  try:
    out=subprocess.run(['sudo','wg'], capture_output=True, text=True, check=True)
    return out.stdout.strip()
  except Exception as e:
    return f"Errore esecuzione 'wg': {e}"

def wg_status_named(raw, clients):
  keys={c['pubkey']:c['name'] for c in clients if c['pubkey']}
  lines=[]
  for line in raw.splitlines():
    m=re.match(r'peer:\\s*(\\S+)', line)
    if m and m.group(1) in keys:
      lines.append(f"peer: {keys[m.group(1)]} ({m.group(1)})")
    else: lines.append(line)
  return "\n".join(lines)

def restart_wg():
  try:
    subprocess.run(['sudo','systemctl','restart',WG_SERVICE_NAME], check=True)
    return True,"Servizio WireGuard riavviato correttamente."
  except Exception as e:
    return False, f"Errore riavvio WireGuard: {e}"

@app.route("/")
def index():
  clients=list_clients()
  wg_named=wg_status_named(wg_status(), clients)
  for c in clients:
    try:
      c['conf_mod']=open(c['path']).read()
      c['qr_base64']=generate_qr_code_base64(c['conf_mod'])
    except:
      c['conf_mod']=""; c['qr_base64']=""
  content=render_template_string("""<div class="d-flex justify-content-between mb-4">
  <h1 class="h4 fw-bold">Utenti WireGuard</h1>
  <a href="{{ url_for('add_client') }}" class="btn btn-success"><i class="bi bi-plus-circle"></i> Nuovo client</a>
</div>
<div class="card shadow-sm mb-4"><div class="card-body p-3"><div class="table-responsive">
<table class="table table-striped align-middle text-center"><thead class="table-primary"><tr><th>Nome</th><th>Stato</th><th>Azioni</th></tr></thead><tbody>
{% for c in clients %}
<tr>
  <td class="text-start"><strong>{{ c.name }}</strong></td>
  <td><span class="badge {% if c.status=='ONLINE' %}bg-success{% elif c.status=='OFFLINE' %}bg-danger{% else %}bg-secondary{% endif %}" id="status-{{ c.name }}">{{ c.status }}</span></td>
  <td class="table-actions">
    <a href="{{ url_for('download_client', client_name=c.name) }}" class="btn btn-outline-primary btn-sm btn-action"><i class="bi bi-download"></i> Scarica</a>
    <a href="{{ url_for('edit_client', client_name=c.name) }}" class="btn btn-outline-warning btn-sm btn-action"><i class="bi bi-pencil"></i> Modifica</a>
    <button type="button" class="btn btn-outline-info btn-sm btn-action" data-bs-toggle="modal" data-bs-target="#qrModal{{ loop.index }}"><i class="bi bi-qr-code-scan"></i> QR</button>
    <a href="{{ url_for('delete_client_route', client_name=c.name) }}" class="btn btn-outline-danger btn-sm btn-action" onclick="return confirm('Sei sicuro di eliminare {{ c.name }}?')"><i class="bi bi-trash"></i> Elimina</a>
  </td>
</tr>
<div class="modal fade" id="qrModal{{ loop.index }}" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-centered"><div class="modal-content">
<div class="modal-header"><h5 class="modal-title">QR Code - {{ c.name }}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
<div class="modal-body text-center">{% if c.qr_base64 %}<img src="data:image/png;base64,{{ c.qr_base64 }}" style="max-width:250px;"><pre class="text-start">{{ c.conf_mod }}</pre>{% else %}<p class="text-danger">QR Code non disponibile.</p>{% endif %}</div>
</div></div></div>
{% endfor %}
</tbody></table></div></div></div>

<div class="card shadow-sm"><div class="card-body">
<h2 class="h5 mb-3"><i class="bi bi-terminal"></i> Stato WireGuard</h2>
<pre id="wg-status">{{ wg_named }}</pre>
<form method="post" action="{{ url_for('restart_wireguard_route') }}">
  <button type="submit" class="btn btn-danger"><i class="bi bi-arrow-clockwise"></i> Riavvia WireGuard</button>
</form>
</div></div>""", clients=clients, wg_named=wg_named)
  return render_template_string(BASE_HTML, content=content)

@app.route("/add", methods=["GET","POST"])
def add_client():
  if request.method=="POST":
    name=request.form.get("name","").strip()
    if not name:
      flash("Il nome client Ã¨ obbligatorio.")
      return redirect(url_for("add_client"))
    path=client_conf_path(name)
    if os.path.exists(path):
      flash("Client giÃ  esistente.")
      return redirect(url_for("add_client"))
    try:
      input_data=f"\n{name}\n"
      result=subprocess.run(["sudo","pivpn","-a"], input=input_data, capture_output=True, text=True, timeout=120)
      if result.returncode!=0:
        flash(f"Errore creazione client: {result.stderr.strip()}")
        return redirect(url_for("add_client"))
      flash(f"Client {name} creato correttamente.")
      return redirect(url_for("index"))
    except Exception as e:
      flash(f"Errore: {e}")
      return redirect(url_for("add_client"))

  form_html="""<h1 class="h4 fw-bold mb-4">Nuovo client</h1>
<form method="post"><div class="mb-3">
<label for="name">Nome client</label>
<input type="text" name="name" class="form-control" required>
</div><button type="submit" class="btn btn-success"><i class="bi bi-plus-circle"></i> Crea</button>

</form>"""
  return render_template_string(BASE_HTML, content=form_html)

@app.route("/edit/<client_name>", methods=["GET","POST"])
def edit_client(client_name):
  client_name=safe_name(client_name)
  path=client_conf_path(client_name)
  if not os.path.isfile(path):
    flash("Client non trovato.")
    return redirect(url_for("index"))
  if request.method=="POST":
    new_conf=request.form.get("config","")
    try:
      with open(path,"w") as f: f.write(new_conf)
      flash("Configurazione salvata.")
    except Exception as e:
      flash(f"Errore salvataggio: {e}")
    return redirect(url_for("index"))
  conf=open(path).read()
  content=f"""<h1 class="h4 mb-3 fw-bold">Modifica client: {client_name}</h1>
<form method="post"><div class="mb-3">
<textarea name="config" rows="15" class="form-control">{conf}</textarea>
</div><button type="submit" class="btn btn-primary">Salva</button>
<a href="{{ url_for('index') }}" class="btn btn-secondary ms-2">Annulla</a></form>"""
  return render_template_string(BASE_HTML, content=content)

@app.route("/download/<client_name>")
def download_client(client_name):
  client_name=safe_name(client_name); path=client_conf_path(client_name)
  if not os.path.isfile(path):
    flash("Client non trovato."); return redirect(url_for("index"))
  return send_file(path, as_attachment=True, download_name=f"{client_name}.conf")

@app.route("/delete/<client_name>")
def delete_client_route(client_name):
  try:
    result=subprocess.run(["sudo","pivpn","-r",client_name], input="y\n", capture_output=True, text=True)
    if result.returncode==0:
      flash(f"Client {client_name} eliminato da PiVPN.")
    else:
      flash(f"Errore durante l'eliminazione di {client_name}: {result.stderr or result.stdout}")
      return redirect(url_for("index"))
    cfg=client_conf_path(client_name)
    if os.path.exists(cfg):
      os.remove(cfg); flash(f"File {client_name}.conf eliminato.")
    else:
      flash(f"Nessun file di configurazione trovato.")
  except Exception as e:
    flash(f"Errore: {e}")
  return redirect(url_for("index"))

@app.route("/restart", methods=["POST"])
def restart_wireguard_route():
  success,msg=restart_wg()
  flash(msg)
  return redirect(url_for("index"))

@app.route("/api/status")
def api_status():
  clients = list_clients()
  for c in clients:
    c['status'] = check_online(c['ip'])
  return jsonify([{'name': c['name'], 'status': c['status']} for c in clients])


@app.route("/api/wg_status")
def api_wg_status():
  clients=list_clients()
  return jsonify({'wg_named': wg_status_named(wg_status(), clients)})

if __name__ == "__main__":
    # Assicurati che WG_CONFIG_DIR esista, altrimenti la pagina non mostra nulla
    if not os.path.isdir(WG_CONFIG_DIR):
        print(f"ATTENZIONE: la cartella {WG_CONFIG_DIR} non esiste.")
    app.run(host="0.0.0.0", port=5000, debug=True)
