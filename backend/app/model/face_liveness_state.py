from sqlalchemy import Column, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.data.database import Base

class FaceLivenessState(Base):
    __tablename__ = "face_liveness_state"

    id = Column(Integer, primary_key=True)
    face_id = Column(Integer, ForeignKey("faces.face_id"), nullable=False) 
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)      
    movement_history = Column(ARRAY(Text), default=list)                    
    required_sequence = Column(ARRAY(Text), default=lambda: ["LEFT", "RIGHT"])
    next_expected_move = Column(Text, default="LEFT")
    finished = Column(Boolean, default=False)

    face = relationship("Face", back_populates="liveness_states")
