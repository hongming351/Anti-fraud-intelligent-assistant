import os
import time
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.crud import update_total_training_samples
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from dashscope import FineTune, File
from app.config import settings

DASHSCOPE_API_KEY = settings.DASHSCOPE_API_KEY
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY not found in environment")

def upload_training_file(file_path):
    """上传训练文件到百炼平台"""
    try:
        file_id = File.upload(file_path, purpose='fine-tune')
        print(f"文件 {file_path} 上传成功，file_id: {file_id}")
        return file_id
    except Exception as e:
        print(f"上传失败: {e}")
        return None

def create_fine_tuning_job(training_file_id):
    """创建 LoRA 微调任务"""
    try:
        job = FineTune.create(
            model='qwen2.5-vl-32b-instruct',
            training_file_ids=[training_file_id],
            hyper_parameters={
                'n_epochs': 3,
                'batch_size': 8,
                'learning_rate': '1e-4',
                'lora_rank': 8,
                'lora_alpha': 32
            },
            training_type='efficient_sft'
        )
        print(f"微调任务创建成功，job_id: {job.id}")
        return job
    except Exception as e:
        print(f"创建任务失败: {e}")
        return None

def wait_for_job_completion(job_id, check_interval=60, timeout=3600):
    """等待任务完成"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            status = FineTune.get(job_id)
            print(f"任务状态: {status.status}")
            if status.status == 'SUCCEEDED':
                print("微调任务成功完成！")
                return True
            elif status.status in ['FAILED', 'CANCELED']:
                print(f"任务失败或已取消，状态: {status.status}")
                return False
            time.sleep(check_interval)
        except Exception as e:
            print(f"查询状态失败: {e}")
            return False
    print("等待超时，任务可能仍在执行")
    return False