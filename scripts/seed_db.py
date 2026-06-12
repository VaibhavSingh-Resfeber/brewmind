import json
import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.services.vector_store import upsert_cafe

DATA_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "cafes_seed.json"


def main() -> None:
    cafes = json.loads(DATA_PATH.read_text())

    db = SessionLocal()
    try:
        seeded = 0
        for cafe in cafes:
            print(f"Seeding: {cafe['name']}...")
            try:
                upsert_cafe(db, cafe)
                print("✅ Done")
                seeded += 1
            except Exception as e:
                print(f"❌ Failed to seed {cafe['name']}: {e}")

        print(f"\n🌱 Seeding complete — {seeded} cafes loaded into Supabase")
    finally:
        db.close()


if __name__ == "__main__":
    main()
