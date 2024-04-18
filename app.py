from flask import Flask, render_template, request
import docker
import os , re
import tempfile
from docker.errors import NotFound

app = Flask(__name__)
client = docker.from_env()

def is_docker_daemon_running():
    try:
        client.ping()
        return True
    except docker.errors.DockerException:
        return False

@app.route('/', methods=['GET'])
def home():
    if is_docker_daemon_running():
        containers = client.containers.list(all=True)
        images = client.images.list()
        return render_template('index.html', containers=containers, images=images)
    else:
        return 'El demonio de Docker no está encendido. Por favor, inicia Docker y vuelve a intentarlo.'

@app.route('/docker-compose', methods=['GET', 'POST'])
def compose():
    if request.method == 'POST':
        compose_file = request.files.get('compose_file')
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_compose_file = os.path.join(temp_dir, 'docker-compose.yml')
            compose_file.save(temp_compose_file)
            subprocess.run(["docker-compose", "-f", temp_compose_file, "up", "-d"])
        return 'Contenedores lanzados'
    else:
        return render_template('docker_compose.html')

@app.route('/execute', methods=['GET', 'POST'])
def execute_command():
    if request.method == 'POST':
        command = request.form['command']
        if command.startswith('docker run'):
            # Parse the command to extract the image name and command arguments
            image_name = command.split()[2]
            command_args = command.split()[3:]
            # Create a container using the Docker API
            container = client.containers.run(image_name, command_args, detach=True)
            # Return the container ID
            return f'Container {container.id} created'
        elif command.startswith('docker exec'):
            # Parse the command to extract the container ID and command arguments
            container_id = command.split()[2]
            command_args = command.split()[3:]
            # Get the container using the Docker API
            container = client.containers.get(container_id)
            # Execute the command in the container using the Docker API
            result = container.exec_run(command_args)
            # Return the command output
            return f'Command output: {result.output.decode("utf-8")}'
        else:
            return 'Comando no válido: solo se admiten comandos relacionados con Docker (docker run, docker exec)'
    return render_template('log.html')

@app.route('/start/<string:id>')
def start(id):
    try:
        container = client.containers.get(id)
        container.start()
        return 'Contenedor iniciado'
    except NotFound:
        return 'Contenedor no encontrado'

@app.route('/stop/<string:id>')
def stop(id):
    try:
        container = client.containers.get(id)
        container.stop()
        return 'Contenedor detenido'
    except NotFound:
        return 'Contenedor no encontrado'

@app.route('/remove/<string:id>')
def remove(id):
    try:
        container = client.containers.get(id)
        container.remove()
        return 'Contenedor eliminado'
    except NotFound:
        return 'Contenedor no encontrado'

@app.route('/container/logs/<string:id>')
def container_logs(id):
    container = client.containers.get(id)
    logs = container.logs()
    logs_str = logs.decode('utf-8')
    # Procesar los logs para eliminar los caracteres de control y mostrarlos en formato de texto
    logs_lines = logs_str.split('\n')
    logs_processed = []
    for line in logs_lines:
        logs_processed.append(re.sub(r'\x1b\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]', '', line))

    return render_template('container_logs.html', logs=logs_processed)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
