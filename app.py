from flask import Flask, render_template, request
import docker
import os
import subprocess

app = Flask(__name__)
client = docker.from_env()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        compose_file = request.form.get('compose_file')
        subprocess.run(["docker-compose", "-f", compose_file, "up", "-d"])
        return 'Contenedores lanzados'
    else:
        containers = client.containers.list(all=True)
        images = client.images.list()
        return render_template('index.html', containers=containers, images=images)

@app.route('/execute', methods=['POST'])
def execute_command():
    if request.method == 'POST':
        command = request.form['command']
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate()
        return render_template('log.html', stdout=stdout, stderr=stderr)
    return 'Comando no válido'

@app.route('/start/<string:id>')
def start(id):
    container = client.containers.get(id)
    container.start()
    return 'Contenedor iniciado'

@app.route('/stop/<string:id>')
def stop(id):
    container = client.containers.get(id)
    container.stop()
    return 'Contenedor detenido'

@app.route('/remove/<string:id>')
def remove(id):
    container = client.containers.get(id)
    container.remove()
    return 'Contenedor eliminado'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)