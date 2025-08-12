import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .models import RunPodJobRequest, RunPodJobResponse

logger = logging.getLogger(__name__)

class RunPodClient:
    """Client for managing RunPod GPU instances"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.runpod.ai/graphql"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Configuration
        self.default_template_id = None
        self.max_wait_time = 300  # 5 minutes
        self.poll_interval = 10   # 10 seconds
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GraphQL request to RunPod API"""
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                raise Exception(f"RunPod API error: {result['errors']}")
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"RunPod API request failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"RunPod request error: {str(e)}")
            raise
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List available RunPod templates"""
        query = """
        query {
            myself {
                podTemplates {
                    id
                    name
                    imageName
                    containerDiskInGb
                    volumeInGb
                    runtime {
                        uptimeInSeconds
                        ports {
                            ip
                            isIpPublic
                            privatePort
                            publicPort
                            type
                        }
                    }
                }
            }
        }
        """
        
        try:
            result = self._make_request(query)
            templates = result.get("myself", {}).get("podTemplates", [])
            
            logger.info(f"Found {len(templates)} RunPod templates")
            return templates
            
        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            return []
    
    def create_pod(self, template_id: str, name: str = None) -> Dict[str, Any]:
        """Create a new RunPod instance"""
        query = """
        mutation createPod($input: PodFindAndDeployOnDemandInput!) {
            podFindAndDeployOnDemand(input: $input) {
                id
                imageName
                env
                machineId
                machine {
                    podHostId
                }
            }
        }
        """
        
        variables = {
            "input": {
                "cloudType": "ALL",
                "gpuCount": 1,
                "volumeInGb": 10,
                "containerDiskInGb": 20,
                "minVcpuCount": 2,
                "minMemoryInGb": 8,
                "gpuTypeId": "NVIDIA GeForce RTX 3070",
                "name": name or f"yoloe-{int(time.time())}",
                "imageName": "runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04",
                "dockerArgs": "",
                "ports": "8000/http",
                "volumeMountPath": "/workspace",
                "env": [
                    {"key": "JUPYTER_PASSWORD", "value": "rp123456789"},
                    {"key": "RUNPOD_TCP_PORT_22", "value": "22"}
                ],
                "templateId": template_id
            }
        }
        
        try:
            result = self._make_request(query, variables)
            pod_data = result.get("podFindAndDeployOnDemand")
            
            if pod_data:
                logger.info(f"Created RunPod instance: {pod_data['id']}")
                return pod_data
            else:
                raise Exception("Failed to create pod - no data returned")
                
        except Exception as e:
            logger.error(f"Failed to create pod: {str(e)}")
            raise
    
    def get_pod_status(self, pod_id: str) -> Dict[str, Any]:
        """Get status of a RunPod instance"""
        query = """
        query getPod($podId: String!) {
            pod(id: $podId) {
                id
                name
                runtime {
                    uptimeInSeconds
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                        type
                    }
                    gpus {
                        id
                        gpuUtilPercent
                        memoryUtilPercent
                    }
                }
                machine {
                    podHostId
                }
            }
        }
        """
        
        variables = {"podId": pod_id}
        
        try:
            result = self._make_request(query, variables)
            pod_data = result.get("pod")
            
            if pod_data:
                return pod_data
            else:
                raise Exception(f"Pod {pod_id} not found")
                
        except Exception as e:
            logger.error(f"Failed to get pod status: {str(e)}")
            raise
    
    def terminate_pod(self, pod_id: str) -> bool:
        """Terminate a RunPod instance"""
        query = """
        mutation terminatePod($podId: String!) {
            podTerminate(id: $podId)
        }
        """
        
        variables = {"podId": pod_id}
        
        try:
            result = self._make_request(query, variables)
            success = result.get("podTerminate")
            
            if success:
                logger.info(f"Terminated RunPod instance: {pod_id}")
                return True
            else:
                logger.warning(f"Failed to terminate pod: {pod_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to terminate pod: {str(e)}")
            return False
    
    def wait_for_pod_ready(self, pod_id: str, timeout: int = None) -> Dict[str, Any]:
        """Wait for pod to be ready and return connection info"""
        timeout = timeout or self.max_wait_time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                pod_status = self.get_pod_status(pod_id)
                runtime = pod_status.get("runtime")
                
                if runtime and runtime.get("ports"):
                    # Pod is running and has ports exposed
                    logger.info(f"Pod {pod_id} is ready")
                    return pod_status
                
                logger.info(f"Waiting for pod {pod_id} to be ready...")
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.warning(f"Error checking pod status: {str(e)}")
                time.sleep(self.poll_interval)
        
        raise TimeoutError(f"Pod {pod_id} did not become ready within {timeout} seconds")
    
    def submit_detection_job(self, request: RunPodJobRequest) -> RunPodJobResponse:
        """Submit a detection job to RunPod"""
        try:
            # Create pod if needed
            pod_id = self.create_pod(request.template_id)["id"]
            
            # Wait for pod to be ready
            pod_status = self.wait_for_pod_ready(pod_id)
            
            # Get connection info
            runtime = pod_status.get("runtime", {})
            ports = runtime.get("ports", [])
            
            if not ports:
                raise Exception("No ports available on pod")
            
            # Find HTTP port
            http_port = None
            for port in ports:
                if port.get("type") == "http":
                    http_port = port
                    break
            
            if not http_port:
                raise Exception("No HTTP port found on pod")
            
            # Construct service URL
            ip = http_port.get("ip")
            public_port = http_port.get("publicPort")
            service_url = f"http://{ip}:{public_port}"
            
            # Submit job to the pod's YOLOE service
            job_data = {
                "job_type": request.job_type,
                "files": [f.dict() for f in request.files],
                "prompt": request.prompt
            }
            
            response = requests.post(
                f"{service_url}/detect/{request.job_type}",
                json=job_data,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            return RunPodJobResponse(
                job_id=result.get("job_id", pod_id),
                status="submitted",
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to submit detection job: {str(e)}")
            # Clean up pod if creation succeeded
            if 'pod_id' in locals():
                self.terminate_pod(pod_id)
            raise
    
    def get_job_results(self, job_id: str, pod_id: str = None) -> Dict[str, Any]:
        """Get results from a detection job"""
        try:
            if pod_id:
                pod_status = self.get_pod_status(pod_id)
                runtime = pod_status.get("runtime", {})
                ports = runtime.get("ports", [])
                
                if ports:
                    http_port = next((p for p in ports if p.get("type") == "http"), None)
                    if http_port:
                        ip = http_port.get("ip")
                        public_port = http_port.get("publicPort")
                        service_url = f"http://{ip}:{public_port}"
                        
                        response = requests.get(
                            f"{service_url}/jobs/{job_id}",
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            return response.json()
            
            # Fallback - job not found or pod not accessible
            return {
                "job_id": job_id,
                "status": "unknown",
                "error": "Unable to retrieve job results"
            }
            
        except Exception as e:
            logger.error(f"Failed to get job results: {str(e)}")
            return {
                "job_id": job_id,
                "status": "error",
                "error": str(e)
            }
    
    def cleanup_idle_pods(self, max_idle_time: int = 3600) -> int:
        """Clean up pods that have been idle for too long"""
        # This would implement logic to find and terminate idle pods
        # For now, return 0 as a placeholder
        logger.info("Cleanup idle pods - not implemented yet")
        return 0

