from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.embedding import embed_text


def upsert_cafe(db: Session, cafe_data: dict) -> None:
    """Insert or update a cafe row, including its pgvector embedding.

    Uses ON CONFLICT (name) DO UPDATE so re-running the seed is idempotent.
    The cafes table must have a UNIQUE constraint on the name column.
    """
    embedding = embed_text(cafe_data["embed_text"])

    db.execute(
        text("""
            INSERT INTO cafes (
                name, neighborhood, address, google_maps_url,
                instagram, website,
                roast_profile, roast_confidence,
                brewing_methods, flavour_notes,
                bean_origin_style, wave,
                character, vibe,
                wifi, good_for_working, pet_friendly,
                your_notes, embed_text, embedding,
                data_complete, needs_visit
            ) VALUES (
                :name, :neighborhood, :address, :google_maps_url,
                :instagram, :website,
                :roast_profile, :roast_confidence,
                :brewing_methods, :flavour_notes,
                :bean_origin_style, :wave,
                :character, :vibe,
                :wifi, :good_for_working, :pet_friendly,
                :your_notes, :embed_text, :embedding,
                :data_complete, :needs_visit
            )
            ON CONFLICT (name) DO UPDATE SET
                neighborhood      = EXCLUDED.neighborhood,
                address           = EXCLUDED.address,
                google_maps_url   = EXCLUDED.google_maps_url,
                instagram         = EXCLUDED.instagram,
                website           = EXCLUDED.website,
                roast_profile     = EXCLUDED.roast_profile,
                roast_confidence  = EXCLUDED.roast_confidence,
                brewing_methods   = EXCLUDED.brewing_methods,
                flavour_notes     = EXCLUDED.flavour_notes,
                bean_origin_style = EXCLUDED.bean_origin_style,
                wave              = EXCLUDED.wave,
                character         = EXCLUDED.character,
                vibe              = EXCLUDED.vibe,
                wifi              = EXCLUDED.wifi,
                good_for_working  = EXCLUDED.good_for_working,
                pet_friendly      = EXCLUDED.pet_friendly,
                your_notes        = EXCLUDED.your_notes,
                embed_text        = EXCLUDED.embed_text,
                embedding         = EXCLUDED.embedding,
                data_complete     = EXCLUDED.data_complete,
                needs_visit       = EXCLUDED.needs_visit
        """),
        {
            "name":             cafe_data["name"],
            "neighborhood":     cafe_data.get("neighborhood"),
            "address":          cafe_data.get("address"),
            "google_maps_url":  cafe_data.get("google_maps_url"),
            "instagram":        cafe_data.get("instagram"),
            "website":          cafe_data.get("website"),
            "roast_profile":    cafe_data["roast_profile"]["value"],
            "roast_confidence": cafe_data["roast_profile"]["confidence"],
            "brewing_methods":  cafe_data["brewing_methods"]["value"],
            "flavour_notes":    cafe_data["flavour_notes"]["value"],
            "bean_origin_style": cafe_data["bean_origin_style"]["value"] if cafe_data.get("bean_origin_style") else None,
            "wave":             cafe_data.get("wave"),
            "character":        cafe_data.get("character"),
            "vibe":             cafe_data["vibe"]["value"],
            "wifi":             cafe_data["wifi"]["value"],
            "good_for_working": cafe_data.get("good_for_working"),
            "pet_friendly":     cafe_data.get("pet_friendly"),
            "your_notes":       cafe_data.get("your_notes"),
            "embed_text":       cafe_data["embed_text"],
            "embedding":        str(embedding),
            "data_complete":    cafe_data.get("data_complete"),
            "needs_visit":      cafe_data.get("needs_visit"),
        },
    )
    db.commit()


def search_cafes(db: Session, query: str, limit: int = 5) -> list[dict]:
    """Return the top {limit} cafes most similar to the query string.

    Uses pgvector's cosine-distance operator (<=>) so lower distance = better
    match. Similarity is returned as 1 - distance so higher = better.
    """
    embedding_str = str(embed_text(query))
    rows = db.execute(
        text(f"""
            WITH similarities AS (
                SELECT
                    id, name, neighborhood, address,
                    roast_profile, brewing_methods, flavour_notes,
                    vibe, wifi, good_for_working, pet_friendly,
                    your_notes, wave, character,
                    1 - (embedding <=> '{embedding_str}' ::vector) AS similarity
                FROM cafes
            )
            SELECT * FROM similarities
            ORDER BY similarity DESC
            LIMIT {int(limit)}
        """)
    ).fetchall()

    return [dict(row._mapping) for row in rows]
