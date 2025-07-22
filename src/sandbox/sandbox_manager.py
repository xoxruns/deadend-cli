import docker
import uuid
from ..sandbox.sandbox import Sandbox, SandboxStatus
from typing import Dict



class SandboxManager:
    """The sandbox manager is responsible of managing the sandboxes running 
    verifying the status and shutting down the sandbox
    """
    

    def __init__(self):
        self.docker_client = docker.from_env()
        self.sandboxes: Dict[uuid.UUID, Sandbox] = {}


    def create_sandbox(self, image: str = "ubuntu:latest"):
        sandbox_id = uuid.uuid4()

        new_sb = Sandbox(
            docker_client=self.docker_client,
            id=sandbox_id
        )
        new_sb.start(container_image=image)

        self.sandboxes[sandbox_id] = new_sb
        return new_sb
    
    def get_sandbox(self, sandbox_id: uuid.UUID) -> Sandbox | None:
        return self.sandboxes.get(sandbox_id)
    
    def execute_in_sandbox(self, sandbox_id: uuid.UUID, command: str):
        if self.sandboxes[sandbox_id] != None and self.sandboxes[sandbox_id].status == SandboxStatus.RUNNING:
            try: 
                sandbox = self.sandboxes[sandbox_id]
                output = sandbox.execute_command(command=command)
                return output
            except Exception as e: 
                raise e 
        else: 
            raise ValueError(f"Sandbox with ID {sandbox_id} not found or status not running.")
        
    def stop_all(self):
        for sandbox_id in self.sandboxes.keys():
            self.sandboxes[sandbox_id].stop()
    

