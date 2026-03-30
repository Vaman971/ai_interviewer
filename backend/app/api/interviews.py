"""Interview API routes: full interview lifecycle management.

Covers creation, file uploads, AI pipeline execution, question delivery,
answer evaluation, scoring, and results retrieval.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, Form, File
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.database import get_db
from backend.app.db.redis import get_redis
from backend.app.models.interview import Interview, InterviewStatus
from backend.app.models.result import Result
from backend.app.models.user import User
from backend.app.schemas.interview import (
    AnswerEvaluation,
    InterviewCreate,
    InterviewListResponse,
    InterviewResponse,
    QuestionResponse,
    SubmitAnswer,
)
from backend.app.schemas.result import ResultResponse
from backend.app.services.auth_service import get_current_user
from backend.app.services.file_service import extract_text_from_file, save_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post(
    "",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview(
    data: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Interview:
    """Create a new interview session.

    Args:
        data: Interview settings (type, personality, difficulty).
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The newly created interview.
    """
    interview = Interview(
        user_id=current_user.id,
        jd_text=data.jd_text,
        interview_type=data.interview_type,
        personality_mode=data.personality_mode,
        difficulty_level=data.difficulty_level,
    )
    db.add(interview)
    await db.flush()
    await db.refresh(interview)
    return interview


@router.post("/{interview_id}/upload-resume", response_model=InterviewResponse)
async def upload_resume(
    interview_id: str,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Interview:
    """Upload a resume file for an interview session.

    Saves the file and extracts its text content.

    Args:
        interview_id: UUID of the interview.
        file: Uploaded resume file (PDF or TXT).
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The updated interview.

    Raises:
        HTTPException: If the interview is not found or doesn't belong to the user.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)

    filename, filepath = await save_upload(file, subfolder=interview.id)
    text = extract_text_from_file(filepath)

    interview.resume_filename = filename
    interview.resume_text = text
    await db.flush()
    await db.refresh(interview)
    
    # Invalidate Cache
    await _invalidate_interview_cache(interview.id)
    return interview


@router.post("/{interview_id}/upload-jd", response_model=InterviewResponse)
async def upload_jd(
    interview_id: str,
    jd_text: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Interview:
    """Upload a job description as text or file.

    Args:
        interview_id: UUID of the interview.
        jd_text: Plain-text job description.
        file: Optional uploaded JD file.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The updated interview.

    Raises:
        HTTPException: If neither text nor file is provided.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)

    if file:
        _, filepath = await save_upload(file, subfolder=interview.id)
        interview.jd_text = extract_text_from_file(filepath)
    elif jd_text:
        interview.jd_text = jd_text
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either jd_text or a file",
        )

    await db.flush()
    await db.refresh(interview)
    
    await _invalidate_interview_cache(interview.id)
    return interview


@router.post("/{interview_id}/start", response_model=InterviewResponse)
async def start_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Interview:
    """Start an interview by running the AI preparation pipeline.

    Analyses the resume and JD, identifies skill gaps, and generates
    personalised interview questions.

    Args:
        interview_id: UUID of the interview.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The updated interview with status ``questions_ready``.

    Raises:
        HTTPException: If resume or JD text is missing.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)

    if not interview.resume_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a resume before starting",
        )
    if not interview.jd_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload a job description before starting",
        )

    interview.status = InterviewStatus.ANALYZING.value

    try:
        from agents.orchestrator import run_preparation_pipeline

        result = await run_preparation_pipeline(
            resume_text=interview.resume_text,
            jd_text=interview.jd_text,
            interview_type=interview.interview_type,
            difficulty=interview.difficulty_level,
        )

        interview.resume_analysis = json.dumps(result.get("resume_analysis", {}))
        interview.jd_analysis = json.dumps(result.get("jd_analysis", {}))
        interview.skill_gap_report = json.dumps(result.get("skill_gap", {}))
        interview.questions = json.dumps(result.get("questions", []))
        interview.status = InterviewStatus.QUESTIONS_READY.value

    except Exception as exc:
        logger.exception("Preparation pipeline failed: %s", exc)
        interview.status = InterviewStatus.FAILED.value
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI pipeline error: {exc}",
        )

    await db.flush()
    await db.refresh(interview)
    await _invalidate_interview_cache(interview.id)
    return interview


@router.get("/{interview_id}/next-question", response_model=QuestionResponse)
async def get_next_question(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the next interview question.

    Args:
        interview_id: UUID of the interview.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The next question with its metadata.

    Raises:
        HTTPException: If no questions are available or all have been asked.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)

    if not interview.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview has not been started yet",
        )

    questions = json.loads(interview.questions)
    idx = interview.current_question_index

    if idx >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All questions have been asked",
        )

    question = questions[idx]

    if interview.status == InterviewStatus.QUESTIONS_READY.value:
        interview.status = InterviewStatus.IN_PROGRESS.value
        await db.flush()
        await _invalidate_interview_cache(interview.id)

    return {
        "question_index": idx,
        "question_text": question.get("question", question.get("question_text", question.get("text", ""))),
        "question_type": question.get("type", question.get("question_type", "general")),
        "difficulty": question.get("difficulty", interview.difficulty_level),
        "total_questions": len(questions),
    }


@router.post("/{interview_id}/submit-answer", response_model=AnswerEvaluation)
async def submit_answer(
    interview_id: str,
    data: SubmitAnswer,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Submit and evaluate a candidate's answer.

    Appends the Q/A pair to the transcript and runs real-time evaluation.

    Args:
        interview_id: UUID of the interview.
        data: The answer payload.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        Evaluation score, feedback, and optional follow-up.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)
    questions = json.loads(interview.questions or "[]")

    if data.question_index >= len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question index",
        )

    question = questions[data.question_index]

    # Update transcript
    transcript = json.loads(interview.transcript or "[]")
    transcript.append({
        "question_index": data.question_index,
        "question": question.get("question", question.get("question_text", "")),
        "answer": data.answer_text,
        "time_taken": data.time_taken_seconds,
        "warnings": data.warnings,
    })
    interview.transcript = json.dumps(transcript)
    interview.current_question_index = data.question_index + 1

    try:
        from agents.interviewer_agent import evaluate_single_answer

        evaluation = await evaluate_single_answer(
            question_text=question.get("question", question.get("question_text", "")),
            answer_text=data.answer_text,
            jd_context=interview.jd_text or "",
            personality_mode=interview.personality_mode,
        )
        
        # --- ADAPTIVE QUESTIONING LOGIC ---
        # If the score is less than 8 and the AI generated a follow-up, 
        # inject it as the immediate next question in the overall queue.
        if evaluation.get("score", 5.0) < 8.0 and evaluation.get("follow_up"):
            logger.info("Adaptive logic triggered: Injecting follow-up question.")
            follow_up_q = {
                "question": evaluation["follow_up"],
                "type": "follow_up",
                "difficulty": "adaptive"
            }
            # Insert the follow-up right after the current question
            questions.insert(data.question_index + 1, follow_up_q)
            
            # Re-index all questions
            for i, q in enumerate(questions):
                q["question_index"] = i
                
            interview.questions = json.dumps(questions)

    except Exception as exc:
        logger.warning("Agent evaluation failed, using fallback: %s", exc)
        evaluation = {
            "score": 5.0,
            "feedback": "Answer recorded successfully.",
            "follow_up": None,
        }

    await db.flush()
    await db.refresh(interview)
    await _invalidate_interview_cache(interview.id)

    return {
        "question_index": data.question_index,
        "score": evaluation.get("score", 5.0),
        "feedback": evaluation.get("feedback", ""),
        "follow_up": evaluation.get("follow_up"),
        "encouragement": evaluation.get("encouragement", ""),
    }


@router.post("/{interview_id}/complete", response_model=ResultResponse)
async def complete_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Result:
    """Complete an interview and generate final scores and feedback.

    Runs the scoring and feedback pipelines, then stores the result.

    Args:
        interview_id: UUID of the interview.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The populated result record.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)

    try:
        from agents.orchestrator import run_scoring_pipeline

        pipeline_result = await run_scoring_pipeline(
            transcript=json.loads(interview.transcript or "[]"),
            questions=json.loads(interview.questions or "[]"),
            jd_text=interview.jd_text or "",
            resume_analysis=json.loads(interview.resume_analysis or "{}"),
        )
    except Exception as exc:
        logger.exception("Scoring pipeline failed: %s", exc)
        pipeline_result = _fallback_scoring()

    scores = pipeline_result.get("scores", {})
    feedback_data = pipeline_result.get("feedback", {})
    questions_list = json.loads(interview.questions or "[]")
    transcript_list = json.loads(interview.transcript or "[]")
    
    # Aggregate all warnings from the transcript
    all_warnings = []
    for turn in transcript_list:
        warnings = turn.get("warnings", [])
        if warnings:
            all_warnings.extend(warnings)

    result = Result(
        interview_id=interview.id,
        overall_score=scores.get("overall", 0),
        technical_score=scores.get("technical", 0),
        behavioral_score=scores.get("behavioral", 0),
        communication_score=scores.get("communication", 0),
        problem_solving_score=scores.get("problem_solving", 0),
        score_breakdown=json.dumps(scores.get("breakdown", {})),
        feedback=json.dumps(feedback_data.get("summary", "")),
        skill_gaps=json.dumps(feedback_data.get("skill_gaps", [])),
        improvement_plan=json.dumps(feedback_data.get("improvement_plan", "")),
        strengths=json.dumps(scores.get("strengths", [])),
        weaknesses=json.dumps(scores.get("weaknesses", [])),
        cheating_flags=json.dumps(list(set(all_warnings))),
        total_questions=len(questions_list),
        questions_answered=len(transcript_list),
    )

    db.add(result)
    interview.status = InterviewStatus.SCORED.value
    await db.flush()
    await db.refresh(result)
    await _invalidate_interview_cache(interview.id)
    return result


@router.get("/{interview_id}/results", response_model=ResultResponse)
async def get_results(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Result:
    """Retrieve the final results for a completed interview.

    Args:
        interview_id: UUID of the interview.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        The result record.

    Raises:
        HTTPException: If results are not yet available.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)

    result_query = await db.execute(
        select(Result).where(Result.interview_id == interview.id)
    )
    result = result_query.scalar_one_or_none()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Results not available yet. Complete the interview first.",
        )
    return result

@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_single_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a single interview by ID using Redis Cache."""
    cache_key = f"interview:{interview_id}"
    
    try:
        r = await get_redis()
        cached = await r.get(cache_key)
        if cached:
            data = json.loads(cached)
            if data.get("user_id") != current_user.id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorised")
            return data
    except HTTPException:
        raise
    except Exception:
        r = None

    interview = await _get_user_interview(interview_id, current_user.id, db)
    
    # Cache mapping
    if r is not None:
        try:
            from backend.app.schemas.interview import InterviewResponse
            schema = InterviewResponse.model_validate(interview)
            await r.setex(cache_key, 3600, schema.model_dump_json())
        except Exception:
            pass

    return interview


@router.get("", response_model=InterviewListResponse)
async def list_interviews(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List the current user's interview sessions.

    Args:
        skip: Number of records to skip (pagination offset).
        limit: Maximum number of records to return.
        current_user: The authenticated user.
        db: Async database session.

    Returns:
        Dictionary with ``interviews`` list and ``total`` count.
    """
    count_result = await db.execute(
        select(func.count())
        .select_from(Interview)
        .where(Interview.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    query = (
        select(Interview)
        .where(Interview.user_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    interviews_result = await db.execute(query)
    interviews = list(interviews_result.scalars().all())

    return {"interviews": interviews, "total": total}

@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(
    interview_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an interview session.

    Args:
        interview_id: UUID of the interview.
        current_user: The authenticated user.
        db: Async database session.
    """
    interview = await _get_user_interview(interview_id, current_user.id, db)
    await db.delete(interview)
    await db.commit()
    await _invalidate_interview_cache(interview_id)
    return None

# ── Private Helpers ─────────────────────────────────────────────


async def _get_user_interview(
    interview_id: str,
    user_id: str,
    db: AsyncSession,
) -> Interview:
    """Fetch an interview and verify ownership.

    Args:
        interview_id: UUID of the interview.
        user_id: UUID of the requesting user.
        db: Async database session.

    Returns:
        The interview instance.

    Raises:
        HTTPException: If not found or not owned by the user.
    """
    result = await db.execute(
        select(Interview).where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()

    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )
    if interview.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorised to access this interview",
        )
    return interview

async def _invalidate_interview_cache(interview_id: str) -> None:
    """Helper to wipe active interview caches when a mutation occurs."""
    try:
        r = await get_redis()
        await r.delete(f"interview:{interview_id}")
    except Exception:
        pass


def _fallback_scoring() -> dict:
    """Return a default scoring result when the AI pipeline fails."""
    return {
        "scores": {
            "overall": 50,
            "technical": 50,
            "behavioral": 50,
            "communication": 50,
            "problem_solving": 50,
            "strengths": ["Completed the interview"],
            "weaknesses": ["Scores generated from fallback — AI was unavailable"],
            "breakdown": {},
        },
        "feedback": {
            "summary": "Interview completed. Detailed AI feedback was unavailable.",
            "skill_gaps": [],
            "improvement_plan": "Retry the interview to receive AI-generated feedback.",
        },
    }
