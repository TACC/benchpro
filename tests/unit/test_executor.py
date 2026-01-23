import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from benchpro.core.domain import Benchmark, Task, Job, ResourceRequest, TaskStatus
from benchpro.core.executor import Executor
from benchpro.core.scheduler import SlurmBackend

@pytest.fixture
def mock_result_store():
    return MagicMock()

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.system.default_walltime = 3600
    config.system.partition = "debug"
    config.system.account = "account"
    return config

@pytest.fixture
def basic_benchmark():
    task = Task(
        task_id="t1", 
        suite_id="s1", 
        resources=ResourceRequest(nodes=1, ranks_per_node=1),
        command="echo test"
    )
    return Benchmark(benchmark_id="b1", suite_id="s1", tasks=[task])

@pytest.mark.asyncio
async def test_run_benchmarks_local(mock_result_store, mock_config, basic_benchmark):
    executor = Executor(backend="local", result_store=mock_result_store, config=mock_config)
    
    # Mock _run_local_task to avoid actual subprocess
    executor._run_local_task = AsyncMock()
    
    await executor.run_benchmarks([basic_benchmark], suite_id="test_suite")
    
    assert executor._run_local_task.call_count == 1
    # Check that run was saved
    mock_result_store.save_run.assert_called_once()
    
@pytest.mark.asyncio
async def test_run_local_task_execution(mock_result_store, mock_config):
    executor = Executor(backend="local", result_store=mock_result_store, config=mock_config)
    task = Task(
        task_id="t1", 
        suite_id="s1", 
        resources=ResourceRequest(nodes=1),
        command="echo test",
        working_directory="/tmp"
    )
    
    # Mock subprocess
    process_mock = AsyncMock()
    process_mock.returncode = 0
    process_mock.wait.return_value = None
    
    with patch("asyncio.create_subprocess_exec", return_value=process_mock) as mock_exec:
        with patch("builtins.open", mock_open()):
             await executor._run_local_task(task, "run_id")
             
    assert task.status == TaskStatus.COMPLETED
    assert task.exit_code == 0
    mock_result_store.save_task.assert_called()

@pytest.mark.asyncio
async def test_run_local_task_failure(mock_result_store, mock_config):
    executor = Executor(backend="local", result_store=mock_result_store, config=mock_config)
    task = Task(task_id="t1", suite_id="s1", resources=ResourceRequest(nodes=1), command="fail")
    
    process_mock = AsyncMock()
    process_mock.returncode = 1
    process_mock.wait.return_value = None
    
    with patch("asyncio.create_subprocess_exec", return_value=process_mock):
        with patch("builtins.open", mock_open()):
            await executor._run_local_task(task, "run_id")
            
    assert task.status == TaskStatus.FAILED
    assert task.exit_code == 1

def test_slurm_submission_flow(mock_result_store, mock_config, basic_benchmark):
    # Mock Semaphore because __init__ tries to create it which requires a loop
    with patch("asyncio.Semaphore"):
        # Mock SlurmBackend
        with patch("benchpro.core.executor.SlurmBackend") as MockBackend:
            backend_instance = MockBackend.return_value
            backend_instance.submit_job.return_value = "job_123"
            
            executor = Executor(backend="slurm", result_store=mock_result_store, config=mock_config)
            
            # We need to run the async method synchronously for this test
            asyncio.run(executor.run_benchmarks([basic_benchmark], suite_id="test_suite"))
            
            # Verify submission
            backend_instance.submit_job.assert_called_once()
            job_arg = backend_instance.submit_job.call_args[0][0]
            assert isinstance(job_arg, Job)
            assert job_arg.scheduler_job_id == "job_123"

def test_slurm_dependency_chain(mock_result_store, mock_config):
    with patch("asyncio.Semaphore"):
        executor = Executor(backend="slurm", result_store=mock_result_store, config=mock_config)
        executor.scheduler = MagicMock()
        executor.scheduler.submit_job.side_effect = ["job_100", "job_101"]
        
        # Create 2 dependent jobs
        t1 = Task(task_id="t1", suite_id="s", resources=ResourceRequest(nodes=1), command="c1")
        t2 = Task(task_id="t2", suite_id="s", resources=ResourceRequest(nodes=1), command="c2")
        
        job1 = Job(job_id="j1", tasks=[t1], resources=t1.resources)
        job2 = Job(job_id="j2", tasks=[t2], resources=t2.resources, job_dependencies=["j1"])
        
        with patch("builtins.open", mock_open()):
            executor._submit_slurm_jobs([job1, job2], "run_id")
            
        assert executor.scheduler.submit_job.call_count == 2
        assert "#SBATCH --dependency=afterok:job_100" in job2.script_content

def test_generate_slurm_script(mock_result_store, mock_config):
    with patch("asyncio.Semaphore"):
        executor = Executor(backend="slurm", result_store=mock_result_store, config=mock_config)
        task = Task(
            task_id="t1", 
            suite_id="s1", 
            resources=ResourceRequest(nodes=2, ranks_per_node=4, time="00:10:00", gpus=1), 
            command="mpirun ./app",
            working_directory="/tmp"
        )
        job = Job(job_id="j1", tasks=[task], resources=task.resources)
        
        script = executor._generate_slurm_script(job, task, dependency_ids=["123", "456"])
        
        assert "#SBATCH --nodes=2" in script
        assert "#SBATCH --ntasks-per-node=4" in script
        assert "#SBATCH --time=00:10:00" in script
        assert "#SBATCH --gpus-per-node=1" in script
        assert "#SBATCH --dependency=afterok:123:456" in script
        assert "mpirun ./app" in script
