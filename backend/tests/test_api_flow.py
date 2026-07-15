"""
End-to-end API tests covering:
  * Task 6  — conversation flow + context management
  * Task 8  — user authentication
  * Task 9  — adaptive responses driven by quiz performance history
  * Task 10 — feedback loop (collect + aggregate thumbs up/down)
"""


# ---------------------------------------------------------------- Task 8 ----
def test_register_login_and_me(client):
    reg = client.post("/api/auth/register", json={
        "username": "alice_t", "email": "alice_t@example.com", "password": "secret12",
    })
    assert reg.status_code == 201
    token = reg.get_json()["token"]

    login = client.post("/api/auth/login", json={
        "email": "alice_t@example.com", "password": "secret12",
    })
    assert login.status_code == 200
    assert login.get_json()["token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["user"]["username"] == "alice_t"


def test_wrong_password_rejected(client):
    client.post("/api/auth/register", json={
        "username": "bob_t", "email": "bob_t@example.com", "password": "secret12",
    })
    bad = client.post("/api/auth/login", json={
        "email": "bob_t@example.com", "password": "wrongpass",
    })
    assert bad.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/chat/sessions").status_code == 401


# ---------------------------------------------------------------- Task 6 ----
def test_chat_message_and_context_followup(client, auth):
    headers, _ = auth
    first = client.post("/api/chat/message", headers=headers,
                        json={"message": "What are Python data types?"})
    assert first.status_code == 200
    body = first.get_json()
    sid = body["session_id"]
    assert body["bot_message"]["content"].strip()
    assert body["bot_message"]["detected_intent"]

    # Follow-up in the same session should resolve via context and still answer.
    followup = client.post("/api/chat/message", headers=headers,
                          json={"message": "tell me more", "session_id": sid})
    assert followup.status_code == 200
    assert followup.get_json()["bot_message"]["content"].strip()


# --------------------------------------------------------------- Task 10 ----
def test_feedback_loop_collects_and_aggregates(client, auth):
    headers, _ = auth
    msg = client.post("/api/chat/message", headers=headers,
                     json={"message": "Explain a for loop"}).get_json()
    bot_id = msg["bot_message"]["id"]

    up = client.post(f"/api/chat/messages/{bot_id}/feedback", headers=headers,
                    json={"feedback": 1})
    assert up.status_code == 200
    assert up.get_json()["message"]["feedback"] == 1

    stats = client.get("/api/chat/feedback/stats", headers=headers).get_json()
    assert stats["up"] >= 1
    assert stats["satisfaction_rate"] == 1.0

    # Flip to thumbs-down, then clear.
    client.post(f"/api/chat/messages/{bot_id}/feedback", headers=headers, json={"feedback": -1})
    stats = client.get("/api/chat/feedback/stats", headers=headers).get_json()
    assert stats["down"] >= 1


def test_feedback_rejects_invalid_value(client, auth):
    headers, _ = auth
    msg = client.post("/api/chat/message", headers=headers,
                     json={"message": "What is a function"}).get_json()
    bot_id = msg["bot_message"]["id"]
    bad = client.post(f"/api/chat/messages/{bot_id}/feedback", headers=headers,
                     json={"feedback": 99})
    assert bad.status_code == 400


# ---------------------------------------------------------------- Task 9 ----
def test_quiz_performance_adapts_chat_complexity(client, auth):
    """The closed loop: ace a quiz -> level rises -> chat explains at that level."""
    headers, _ = auth

    # 1. A brand-new user is served beginner-level explanations.
    before = client.post("/api/chat/message", headers=headers,
                        json={"message": "What is a variable?"}).get_json()
    assert before["bot_message"]["complexity_level"] == "beginner"

    # 2. Take a quiz and answer everything correctly.
    quiz = client.get("/api/quiz/start", headers=headers).get_json()
    questions = quiz["questions"]
    assert questions, "adaptive quiz returned no questions"
    answers = [{
        "skill_id": q.get("skill_id", "variables"),
        "question_text": q.get("question", ""),
        "selected_index": q["correct_index"],   # all correct
        "correct_index": q["correct_index"],
        "difficulty": q.get("difficulty", "easy"),
        "explanation": q.get("explanation", ""),
    } for q in questions]

    submit = client.post("/api/quiz/submit", headers=headers, json={"answers": answers}).get_json()
    assert submit["percentage"] == 100.0
    assert submit["new_level"] == "advanced"

    # 3. Progress is recorded.
    summary = client.get("/api/progress/summary", headers=headers).get_json()
    assert summary["overall"]["percentage"] == 100.0

    # 4. The SAME chat question is now answered at the advanced level.
    after = client.post("/api/chat/message", headers=headers,
                       json={"message": "What is a variable?"}).get_json()
    assert after["bot_message"]["complexity_level"] == "advanced"
