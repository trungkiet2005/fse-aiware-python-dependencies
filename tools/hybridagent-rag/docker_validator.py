"""
Docker Validator: Test solutions in actual Docker containers
"""

import docker
import tempfile
import os
import time
from typing import Dict, Any, Tuple


class DockerValidator:
    """
    Validates dependency solutions by actually installing and testing in Docker
    """
    
    def __init__(self, timeout: int = 60):
        """
        Initialize Docker validator
        
        Args:
            timeout: Max time (seconds) for each test
        """
        self.timeout = timeout
        try:
            self.client = docker.from_env()
            self.available = True
            print("[DockerValidator] Docker client initialized")
        except Exception as e:
            print(f"[DockerValidator] WARNING: Docker not available: {e}")
            self.available = False
    
    def validate_solution(
        self,
        code: str,
        packages: Dict[str, str],
        python_version: str = "3.8"
    ) -> Tuple[bool, str, float]:
        """
        Validate solution by testing in Docker
        
        Args:
            code: Python code to test
            packages: Dict of package:version
            python_version: Python version to use
            
        Returns:
            (success, message, execution_time)
        """
        if not self.available:
            return False, "Docker not available", 0.0
        
        start_time = time.time()
        
        try:
            # Create temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code to file
                code_file = os.path.join(tmpdir, "snippet.py")
                with open(code_file, 'w') as f:
                    f.write(code)
                
                # Create requirements.txt
                req_file = os.path.join(tmpdir, "requirements.txt")
                with open(req_file, 'w') as f:
                    for pkg, ver in packages.items():
                        f.write(f"{pkg}=={ver}\n")
                
                # Create Dockerfile
                dockerfile = os.path.join(tmpdir, "Dockerfile")
                with open(dockerfile, 'w') as f:
                    f.write(f"""FROM python:{python_version}-slim

WORKDIR /app

# Copy files
COPY requirements.txt .
COPY snippet.py .

# Install packages
RUN pip install --no-cache-dir -r requirements.txt

# Try to import (syntax check)
RUN python -c "import snippet"

CMD ["python", "snippet.py"]
""")
                
                # Build image
                print(f"[DockerValidator] Building image (Python {python_version})...")
                image, build_logs = self.client.images.build(
                    path=tmpdir,
                    tag="hybridagent-test",
                    rm=True,
                    forcerm=True
                )
                
                # Run container
                print(f"[DockerValidator] Running container...")
                container = self.client.containers.run(
                    image.id,
                    remove=True,
                    detach=False,
                    timeout=self.timeout
                )
                
                execution_time = time.time() - start_time
                
                # Clean up image
                try:
                    self.client.images.remove(image.id, force=True)
                except:
                    pass
                
                return True, "SUCCESS", execution_time
                
        except docker.errors.BuildError as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            if "Could not find a version" in error_msg:
                return False, "Package version not found", execution_time
            elif "No matching distribution" in error_msg:
                return False, "Package not available", execution_time
            else:
                return False, f"Build failed: {error_msg[:100]}", execution_time
                
        except docker.errors.ContainerError as e:
            execution_time = time.time() - start_time
            return False, f"Runtime error: {str(e)[:100]}", execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Error: {str(e)[:100]}", execution_time
    
    def batch_validate(
        self,
        solutions: list,
        show_progress: bool = True
    ) -> list:
        """
        Validate multiple solutions
        
        Args:
            solutions: List of (code, packages, python_version, snippet_id)
            show_progress: Show progress bar
            
        Returns:
            List of validation results
        """
        results = []
        
        for i, (code, packages, python_version, snippet_id) in enumerate(solutions, 1):
            if show_progress:
                print(f"\n[{i}/{len(solutions)}] Testing {snippet_id}...")
            
            success, message, exec_time = self.validate_solution(
                code, packages, python_version
            )
            
            results.append({
                'snippet_id': snippet_id,
                'docker_success': success,
                'docker_message': message,
                'docker_time': exec_time
            })
            
            if show_progress:
                status = "✅" if success else "❌"
                print(f"{status} {message} ({exec_time:.2f}s)")
        
        return results
