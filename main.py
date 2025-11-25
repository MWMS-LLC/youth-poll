# main.py
# main.py (updated: unified /api/vote handler that uses responses, checkbox_responses, other_responses)
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union
import logging
from datetime import datetime, timezone
import zlib
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import db module and handle errors gracefully
try:
    from backend.db import connection_pool, db_check, db_ssl_status
    logger.info("Successfully imported db module")
except Exception as e:
    logger.error(f"Failed to import db module: {e}")
    raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    try:
        # Test database connection
        db_check()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")

app = FastAPI(lifespan=lifespan)

# ------------------ CORS setup ------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://myworldmysay.com",
    "https://www.myworldmysay.com",
    "https://api.myworldmysay.com",
    "https://teen.myworldmysay.com",
    "https://youth.myworldmysay.com",
    "https://parents.myworldmysay.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ DB helper (local to main.py) ------------------
def execute_query(query: str, params: tuple = None, fetch: bool = True):
    """
    Execute a SQL query using the shared connection_pool from backend.db.
    Returns list[dict] when fetch=True, otherwise commits and returns True.
    """
    conn = None
    cursor = None
    try:
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        if fetch:
            cols = [d[0] for d in cursor.description] if cursor.description else []
            rows = cursor.fetchall() if cursor.description else []
            return [dict(zip(cols, row)) for row in rows]
        else:
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Database operation failed")
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                connection_pool.putconn(conn)
            except Exception:
                pass

# ------------------ Health ------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-check")
def get_db_check():
    return {"ok": db_check()}

@app.get("/db-ssl-status")
def get_db_ssl_status():
    return {"ssl": db_ssl_status()}

# ------------------ Categories ------------------
@app.get("/api/categories")
def get_categories():
    query = """
        SELECT *
        FROM categories
        ORDER BY id
    """
    return {"categories": execute_query(query)}

# ------------------ Blocks ------------------
@app.get("/api/categories/{category_id}/blocks")
def get_blocks(category_id: int):
    query = """
        SELECT *
        FROM blocks
        WHERE category_id = %s
        ORDER BY block_number
    """
    return {"blocks": execute_query(query, (category_id,))}

# ------------------ Questions ------------------
@app.get("/api/blocks/{block_code}/questions")
async def get_questions_by_block(block_code: str):
    try:
        # Split "1_1" → category_id=1, block_number=1
        parts = block_code.split('_')
        if len(parts) != 2:
            raise ValueError("Invalid block code format")

        category_id = int(parts[0])
        block_number = int(parts[1])

        query = """
            SELECT *
            FROM questions
            WHERE category_id = %s
              AND block_number = %s
            ORDER BY question_number
        """
        results = execute_query(query, (category_id, block_number))

        # ✅ Wrap like categories/blocks/options
        return {"questions": results}

    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database operation failed: {e}")


# ------------------ Options ------------------
@app.get("/api/questions/{question_code}/options")
def get_options(question_code: str):
    query = """
        SELECT *
        FROM options
        WHERE question_code = %s
        ORDER BY option_select
    """
    return {"options": execute_query(query, (question_code,))}

# ------------------ Soundtracks (stubbed safely) ------------------
@app.get("/api/soundtracks")
def get_soundtracks():
    query = "SELECT * FROM soundtracks ORDER BY id"
    results = execute_query(query)
    return {"soundtracks": results}

@app.get("/api/soundtracks/playlists")
def get_soundtrack_playlists():
    query = "SELECT DISTINCT playlist_tag FROM soundtracks WHERE playlist_tag IS NOT NULL"
    results = execute_query(query)
    playlists = [row["playlist_tag"] for row in results if row.get("playlist_tag")]
    return {"playlists": playlists}

# ------------------ Users ------------------
@app.post("/api/users")
def create_user(user_uuid: str, year_of_birth: int):
    query = """
        INSERT INTO users (user_uuid, year_of_birth)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """
    execute_query(query, (user_uuid, year_of_birth), fetch=False)
    return {"message": "User created or already exists"}




# ------------------ Separate vote handler (single, checkbox, other) ------------------
def get_metadata(q_code, opt_select=None):
    if opt_select:
        rows = execute_query(
            """
            SELECT q.question_text, q.question_number,
                   q.category_id, c.category_name, c.category_text, q.block_number,
                   o.option_select, o.option_code, o.option_text
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            JOIN options o ON q.question_code = o.question_code
            WHERE q.question_code = %s AND o.option_select = %s
            """,
            (q_code, opt_select)
        )
    else:
        rows = execute_query(
            """
            SELECT q.question_text, q.question_number,
                   q.category_id, c.category_name, c.category_text, q.block_number
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            WHERE q.question_code = %s
            """,
            (q_code,)
        )
    return rows[0] if rows else None


# ----------------------------
# Vote submission (single, checkbox, free text)
# ----------------------------
# ----------------------------
# Submit vote
# ----------------------------
@app.post("/api/vote/single")
def submit_single_vote(vote: dict):
    """Handle single-choice votes - stores in responses table"""
    user_uuid = vote.get("user_uuid")
    question_code = vote.get("question_code")
    option_select = vote.get("option_select")
    other_text = vote.get("other_text")

    if not user_uuid or not question_code or not option_select:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Lookup question metadata
    meta = get_metadata(question_code)
    if not meta:
        raise HTTPException(status_code=404, detail="Question not found")

    # Normalize "Other" values
    OTHER_KEY = "OTHER"
    if option_select and isinstance(option_select, str) and option_select.strip().upper() == OTHER_KEY:
        option_select = OTHER_KEY

    if other_text:
        other_text = other_text.strip()

    # Insert single-choice vote
    execute_query(
        """
        INSERT INTO responses
        (user_uuid, question_code, question_text, question_number,
        category_id, category_name, category_text, block_number,
        option_id, option_select, option_code, option_text,
        created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """,
        (
            user_uuid, question_code, meta["question_text"], meta["question_number"],
            meta["category_id"], meta["category_name"], meta["category_text"], meta["block_number"],
            None, option_select, f"{question_code}_{option_select}", option_select
        ),
        fetch=False
    )

    # If user selected OTHER and typed free text, also store it
    if option_select == "OTHER" and other_text:
        execute_query(
            """
            INSERT INTO other_responses
            (user_uuid, question_code, question_text, question_number,
            category_id, category_name, category_text, block_number,
            other_text, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            """,
            (
                user_uuid, question_code,
                meta["question_text"], meta["question_number"],
                meta["category_id"], meta["category_name"], meta["category_text"], meta["block_number"],
                other_text,
            ),
            fetch=False,
        )

    return {"message": "Single-choice vote recorded", "question_code": question_code}

# Checkbox vote endpoint
@app.post("/api/vote/checkbox")
def submit_checkbox_vote(vote: dict):
    """Handle checkbox votes - stores in checkbox_responses table with weights"""
    user_uuid = vote.get("user_uuid")
    question_code = vote.get("question_code")
    option_selects = vote.get("option_selects", [])
    other_text = vote.get("other_text")

    if not user_uuid or not question_code or not option_selects:
        raise HTTPException(status_code=400, detail="Missing required fields")

    if len(option_selects) == 0:
        raise HTTPException(status_code=400, detail="No checkbox options provided")

    # Lookup question metadata
    meta = get_metadata(question_code)
    if not meta:
        raise HTTPException(status_code=404, detail="Question not found")

    # Normalize "Other" values
    OTHER_KEY = "OTHER"
    option_selects = [OTHER_KEY if isinstance(v, str) and v.strip().upper() == OTHER_KEY else v for v in option_selects]

    if other_text:
        other_text = other_text.strip()

    # Calculate weight (each option gets equal weight)
    weight = 1.0 / len(option_selects)

    # Insert each selected option
    for opt in option_selects:
        execute_query(
            """
            INSERT INTO checkbox_responses
            (user_uuid, question_code, question_text, question_number,
            category_id, category_name, category_text, block_number,
            option_id, option_select, option_code, option_text,
            weight, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            """,
            (
                user_uuid, question_code, meta["question_text"], meta["question_number"],
                meta["category_id"], meta["category_name"], meta["category_text"], meta["block_number"],
                None, opt, f"{question_code}_{opt}", opt, weight
            ),
            fetch=False
        )

        # If "OTHER" was selected and free text exists, also store it
        if opt == "OTHER" and other_text:
            execute_query(
                """
                INSERT INTO other_responses
                (user_uuid, question_code, question_text, question_number,
                category_id, category_name, category_text, block_number,
                other_text, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                """,
                (
                    user_uuid, question_code,
                    meta["question_text"], meta["question_number"],
                    meta["category_id"], meta["category_name"], meta["category_text"], meta["block_number"],
                    other_text,
                ),
                fetch=False,
            )

    return {"message": "Checkbox vote(s) recorded", "question_code": question_code}

# Other text vote endpoint
@app.post("/api/vote/other")
def submit_other_vote(vote: dict):
    """Handle other text votes - stores in other_responses and creates placeholder in responses"""
    user_uuid = vote.get("user_uuid")
    question_code = vote.get("question_code")
    other_text = vote.get("other_text")

    if not user_uuid or not question_code or not other_text:
        raise HTTPException(status_code=400, detail="Missing required fields")

    other_text = other_text.strip()
    if not other_text:
        raise HTTPException(status_code=400, detail="Other text cannot be empty")

    # Lookup question metadata
    meta = get_metadata(question_code)
    if not meta:
        raise HTTPException(status_code=404, detail="Question not found")

    OTHER_KEY = "OTHER"

    # Store the free text
    execute_query(
        """
        INSERT INTO other_responses
        (user_uuid, question_code, question_text, question_number,
        category_id, category_name, category_text, block_number,
        other_text, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """,
        (
            user_uuid, question_code,
            meta["question_text"], meta["question_number"],
            meta["category_id"], meta["category_name"], meta["category_text"], meta["block_number"],
            other_text,
        ),
        fetch=False,
    )

    # Create a placeholder in responses so charts show "Other"
    execute_query(
        """
        INSERT INTO responses
        (user_uuid, question_code, question_text, question_number,
        category_id, category_name, category_text, block_number,
        option_id, option_select, option_code, option_text,
        created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """,
        (
            user_uuid, question_code,
            meta["question_text"], meta["question_number"],
            meta["category_id"], meta["category_name"], meta["category_text"], meta["block_number"],
            None, OTHER_KEY, f"{question_code}_{OTHER_KEY}", "Other",
        ),
        fetch=False,
    )

    return {"message": "Other text response recorded", "question_code": question_code}



# ----------------------------
# Results aggregation
# ----------------------------
# ----------------------------
# Results aggregation
# ----------------------------
@app.get("/api/results/{question_code}")
def get_results(question_code: str):
    """
    Aggregates results for a question:
      - Single-choice from responses
      - Checkbox from checkbox_responses
      - Total responses reported as integer (number of distinct users)
    """

    # Get all option definitions for the question
    option_rows = execute_query(
        """
        SELECT option_select, option_code, option_text
        FROM options
        WHERE question_code = %s
        ORDER BY id
        """,
        (question_code,)
    ) or []

    # Single-choice counts
    single_counts = execute_query(
        """
        SELECT option_select, COUNT(*)::float as votes
        FROM responses
        WHERE question_code = %s
        GROUP BY option_select
        """,
        (question_code,)
    ) or []

    # Checkbox counts (safe cast + handle empty case)
    checkbox_counts = execute_query(
        """
        SELECT option_select, COALESCE(SUM(weight),0)::float as votes
        FROM checkbox_responses
        WHERE question_code = %s
        GROUP BY option_select
        """,
        (question_code,)
    ) or []


    # --- Merge counts into one dict ---
    counts = {}
    for row in single_counts + checkbox_counts:
        sel = row["option_select"]
        counts[sel] = counts.get(sel, 0) + row["votes"]

    # --- Build results list from canonical options ---
    results = []
    for opt in option_rows:
        sel = opt["option_select"]
        votes = counts.get(sel, 0)
        results.append({
            "option_select": opt["option_select"],  # keep display form from options table
            "option_code": opt["option_code"],
            "option_text": opt["option_text"],
            "votes": votes
        })

    # --- Total responses as integer (count all answers, not unique users) ---
    # Count all responses: one per row in responses table, one per row in checkbox_responses table
    total_result = execute_query(
        """
        SELECT COUNT(*) AS n FROM (
            SELECT user_uuid
            FROM responses
            WHERE question_code = %s
            UNION ALL
            SELECT user_uuid
            FROM checkbox_responses
            WHERE question_code = %s
        ) AS all_votes
        """,
        (question_code, question_code)
    )
    
    total = int(total_result[0]["n"]) if total_result else 0

    return {
        "question_code": question_code,
        "results": results,
        "total_responses": total
    }






# ------------------ Age Validation ------------------
@app.post("/api/validate-age")
def validate_age(payload: dict):
    try:
        year_of_birth = payload.get("year_of_birth")

        if not year_of_birth or not str(year_of_birth).isdigit():
            raise HTTPException(status_code=400, detail="Invalid year of birth")

        yob = int(year_of_birth)
        current_year = datetime.now().year
        age = current_year - yob

        if age < 13:
            return {"valid": False, "reason": "too_young"}
        elif age > 120:
            return {"valid": False, "reason": "invalid_year"}
        else:
            return {"valid": True, "age": age}

    except Exception as e:
        logger.error(f"Age validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Age validation failed: {e}")

# ------------------ Playlists ------------------
@app.get("/api/playlists")
def get_playlists():
    query = "SELECT * FROM playlists ORDER BY id"
    results = execute_query(query)
    return {"playlists": results}

@app.get("/api/playlists/{playlist_id}")
def get_playlist(playlist_id: int):
    query = "SELECT * FROM playlists WHERE id = %s"
    results = execute_query(query, (playlist_id,))
    if not results:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"playlist": results[0]}

@app.get("/api/playlists/{playlist_id}/songs")
def get_playlist_songs(playlist_id: int):
    query = """
        SELECT ps.*, s.*
        FROM playlist_songs ps
        JOIN soundtracks s ON ps.song_id = s.id
        WHERE ps.playlist_id = %s
        ORDER BY ps.order_number
    """
    results = execute_query(query, (playlist_id,))
    return {"songs": results}
