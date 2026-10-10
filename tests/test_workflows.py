from concurrent.futures import ThreadPoolExecutor
import pytest
from tests.test_api import account, offer, vacancy_data, setup_db


def test_simultaneous_invitation_only_one_record():
    _, cid=account("candidate",grade="middle")
    employer,_=account("employer")
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:employer.post("/api/v1/invitations",json=offer(cid)), range(2)))
    assert sorted(r.status_code for r in responses)==[201,409]
    assert len(employer.get("/api/v1/invitations").json())==1


def test_simultaneous_test_start_returns_same_attempt():
    candidate,_=account("candidate")
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:candidate.post("/api/v1/assessments",json={"specialization":"backend","grade":"middle"}),range(2)))
    assert all(r.status_code==201 for r in responses)
    assert responses[0].json()['id']==responses[1].json()['id']


def test_need_cannot_escape_its_category():
    employer,_=account("employer")
    need=employer.post("/api/v1/needs",json=vacancy_data()).json()
    assert employer.get(f"/api/v1/candidates?need_id={need['id']}&grade=senior").status_code==422


def test_challenge_is_owned_review_and_does_not_change_grade():
    candidate,_=account("candidate",grade="middle")
    employer,_=account("employer")
    other,_=account("employer","2")
    c=employer.post("/api/v1/challenges",json={"title":"Надёжная очередь","description":"Опишите подход к атомарной обработке повторяющихся событий.","specialization":"backend","rubric":"Корректность 50, граничные случаи 30, тестирование 20"})
    assert c.status_code==201
    cid=c.json()['id']
    response=candidate.post(f"/api/v1/challenges/{cid}/submissions",json={"answer":"Используем транзакцию, уникальный ключ события и таблицу обработанных событий."})
    assert response.status_code==201
    sid=response.json()['id']
    assert candidate.post(f"/api/v1/challenges/{cid}/submissions",json={"answer":"Повторное решение не должно создавать дубликат."}).status_code==409
    review={"score":90,"feedback":"Хорошо описана атомарность. Добавьте тест конкурентной доставки."}
    assert other.post(f"/api/v1/submissions/{sid}/review",json=review).status_code==404
    assert employer.post(f"/api/v1/submissions/{sid}/review",json=review).status_code==200
    assert candidate.get("/api/v1/profile").json()['grade']=='middle'
    assert candidate.get("/api/v1/challenges").json()[0]['submissions'][0]['score']==90
