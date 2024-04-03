from flask import Flask, render_template, request
import docker
import os
import subprocess
import tempfile

app = Flask(__name__)
client = docker.from_env()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        compose_file = request.form.get('compose_file')
        # Save the compose file to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_compose_file = os.path.join(temp_dir, 'docker-compose.yml')
            with open(temp_compose_file, 'w') as f:
                f.write(compose_file)
            # Execute the compose file
            subprocess.run(["docker-compose", "-f", temp_compose_file, "up", "-d"])
        return 'Contenedores lanzados'
    else:
        containers = client.containers.list(all=True)
        images = client.images.list()
        return render_template('index.html', containers=containers, images=images)

@app.route('/execute', methods=['POST'])
def execute_command():
    if request.method == 'POST':
        command = request.form['command']
        if command.startswith('docker'):
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            return render_template('log.html', stdout=stdout, stderr=stderr)
        else:
            return 'Comando no válido: solo se admiten comandos relacionados con Docker (docker)'
    return 'Comando no válido'

@app.route('/start/<string:id>')
def start(id):
    try:
        container = client.containers.get(id)
        container.start()
        return 'Contenedor iniciado'
    except docker.errors.NotFound:
        return 'Contenedor no encontrado'

@app.route('/stop/<string:id>')
def stop(id):
    try:
        container = client.containers.get(id)
        container.stop()
        return 'Contenedor detenido'
    except docker.errors.NotFound:
        return 'Contenedor no encontrado'

@app.route('/remove/<string:id>')
def remove(id):
    try:
        container = client.containers.get(id)
        container.remove()
        return 'Contenedor eliminado'
    except docker.errors.NotFound:
        return 'Contenedor no encontrado'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
