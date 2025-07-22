import docker
import uuid 
import docker.errors
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class SandboxStatus(str, Enum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class Sandbox(BaseModel):
    """
    The Sandbox object interacts with docker API to create the gVisor sandbox
    the runtime specified is the runsc gvisor  
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    container_id : str | None = None
    docker_image: str = ""
    docker_volume: str = ""
    status: SandboxStatus = SandboxStatus.CREATED
    last_command: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    _docker_client: docker.DockerClient # = Field(exclude=True, default=None)
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True

    def __init__(self, docker_client: docker.DockerClient, **data):
        super().__init__(**data)
        self._docker_client = docker_client

    def start(self, container_image: str = "ubuntu:latest", volume_path: str | None = None, start_process: str = "/bin/bash"):

        if volume_path == None:
            volumes = None
        else:
            volumes = [volume_path]
        try:
            self.status = SandboxStatus.RUNNING
            container = self._docker_client.containers.run(
                image=container_image,
                volumes=volumes, 
                runtime='runsc',
                tty=True,
                command=start_process,
                detach=True,
                stdin_open=True
            )
            self.container_id = container.id 
            self.docker_image = container_image
            self.docker_volume = volume_path
            self.status = SandboxStatus.RUNNING

            return container
        except Exception as e:
            self.status = SandboxStatus.ERROR
            raise e
        


    def execute_command(self, command: str, stream: bool = True):
        if not self.container_id:
            raise ValueError("Container not started")
        if self.status != SandboxStatus.RUNNING:
            raise ValueError(f"Container not running (status: {self.status})")
        
        container = self._docker_client.containers.get(self.container_id)
        
        self.last_command = command

        try: 
            if stream:
                command_result = container.exec_run(
                    cmd=command, 
                    detach=False,
                    tty=True,
                    socket=True,
                    stream=True,
                )
                return {
                    "command": command,
                    "streaming": True, 
                    "stream": command_result.output
                }
            else:
                command_result = container.exec_run(
                    cmd=command,
                    detach=False,
                    tty=True
                )
                return {
                    "command": command,
                    "exit_code": command_result.exit_code,
                    "streaming": False, 
                    "output": command_result.output.decode('utf-8') if command_result.output else "",
                    "timed_out": False,
                }
            
        except Exception as e:
            return {
                "exit_code": -1,
                "output": f"Error: {str(e)}",
                "command": command,
                "timed_out": False,
                "streaming": False
            }
            

    def stop(self):
        if self.container_id:
            try: 
                container = self._docker_client.containers.get(self.container_id)        
                container.stop()
                self.status = SandboxStatus.STOPPED
            except docker.errors.NotFound:
                pass
        
    def cleanup(self):
        if self.container_id:
            try:
                container = self._docker_client.containers.get(self.container_id)
                container.remove(force=True)
                self.status = SandboxStatus.STOPPED
                self.container_id = None
            except docker.errors.NotFound:
                pass

    



