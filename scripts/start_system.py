"""
Shurokkha One-Click Startup Script
Usage: python scripts/start_system.py
Run from: r:/company-wise-projects-main/razorflow-gateway/
"""
import subprocess
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BACKEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend')
MODEL_PATH = os.path.join(BACKEND_DIR, 'app', 'ml', 'fraud_model.pkl')
DB_PATH = os.path.join(BACKEND_DIR, 'razorflow.db')

BANNER = """
╔══════════════════════════════════════════════════════════╗
║         Shurokkha Payment Gateway v1.0.0                 ║
║   Real-Time Payments + AI Fraud Detection Engine         ║
╠══════════════════════════════════════════════════════════╣
║  Dashboard:   http://127.0.0.1:8000/                     ║
║  API Docs:    http://127.0.0.1:8000/docs                 ║
║  Health:      http://127.0.0.1:8000/health               ║
╚══════════════════════════════════════════════════════════╝
"""

def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd or BACKEND_DIR, capture_output=False)
    if result.returncode != 0:
        print(f'[Error] Command failed: {" ".join(cmd)}')
        sys.exit(1)

def main():
    print(BANNER)
    
    # 1. Train ML model if needed
    if not os.path.exists(MODEL_PATH):
        print('[Setup] Training fraud detection ML model...')
        run([sys.executable, 'app/ml/train_model.py'])
    else:
        print('[Setup] ML model already trained. ✓')
    
    # 2. Seed database if empty
    seed_script = os.path.join(os.path.dirname(__file__), 'seed_data.py')
    print('[Setup] Seeding database...')
    subprocess.run([sys.executable, seed_script], cwd=BACKEND_DIR)
    
    # 3. Launch FastAPI server
    print('[Setup] Launching Shurokkha server...')
    print('[Setup] Press Ctrl+C to stop.\n')
    run([
        sys.executable, '-m', 'uvicorn',
        'app.main:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ])

if __name__ == '__main__':
    main()
