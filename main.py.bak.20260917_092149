import asyncio
from core.master_pipeline import MasterPipeline, HealthController
async def main():
    pipe = MasterPipeline(HealthController())
    await pipe.run_pipeline()
if __name__ == "__main__":
    asyncio.run(main())
