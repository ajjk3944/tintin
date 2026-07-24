from database import init_db
from sensor_ai import train_models
from cost_ai import start_scanner
from scheduler_ai import add_job

def setup():
    print("Initializing Tensor Titan...")
    init_db()
    print("Database ready.")
    train_models()
    print("Models trained.")
    start_scanner()
    print("Cost scanner started.")
    for i in range(5):
        add_job(f"InitJob-{i+1}", priority=i+1)
    print("Initial jobs queued.")
    print("\nSetup complete! Now run:")
    print("  streamlit run dashboard.py")

if __name__ == "__main__":
    setup()
