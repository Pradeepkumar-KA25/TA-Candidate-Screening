from app.core.database import get_engine
from app.models.kanini_resume_db import KaniniResume
from sqlalchemy.orm import Session
import json

# Get the first resume
engine = get_engine()
with Session(engine) as session:
    resume = session.query(KaniniResume).first()
    
    if resume:
        print("Full parsed_data:")
        print(json.dumps(resume.parsed_data, indent=2, default=str))
