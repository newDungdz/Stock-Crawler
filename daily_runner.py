from main import run_crawler
from apscheduler.schedulers.blocking import BlockingScheduler

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    run_crawler()
    # Run every 1 minute for testing
    scheduler.add_job(run_crawler, 'interval', minutes=5)
    print("🕒 APScheduler started. Running every 5 minute for testing...")
    scheduler.start()
