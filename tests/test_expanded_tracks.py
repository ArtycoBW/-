import json
from pathlib import Path
import pytest
from sqlalchemy import select, delete
from backend import models as m
from backend.db import SessionLocal
from backend.taxonomy import SPECIALIZATIONS
from backend.assessment import generate_questions, evaluate, public_questions
from backend.assessment_tracks import track_questions
from backend.judge_catalog import populate
from tests.test_api import setup_db, account, vacancy_data

@pytest.mark.parametrize("spec", SPECIALIZATIONS)
def test_category_is_available_end_to_end_and_private(spec):
    candidate, cid=account("candidate",spec)
    employer,_=account("employer",spec)
    own=candidate.get('/api/v1/profile').json()
    payload={k:own[k] for k in ['name','city','bio','contact','desired_grade','experience','work_format','salary_min','published','consent']}
    payload.update(specialization=spec,skills=SPECIALIZATIONS[spec][1])
    assert candidate.put('/api/v1/profile',json=payload).status_code==200
    attempt=candidate.post('/api/v1/assessments',json={'specialization':spec,'grade':'middle'})
    assert attempt.status_code==201,attempt.text
    with SessionLocal() as db:
        saved=db.get(m.Attempt,attempt.json()['id'])
        answers={q['id']:q['answer'] for q in saved.questions}
        assert saved.bank_version=='2.0'
    assert all('answer' not in q for q in attempt.json()['questions'])
    result=candidate.post(f"/api/v1/assessments/{attempt.json()['id']}/submit",json={'answers':answers})
    assert result.status_code==200,result.text
    assert candidate.get('/api/v1/profile').json()['grade']=='middle'
    need=employer.post('/api/v1/needs',json={**vacancy_data(),'specialization':spec,'skills':SPECIALIZATIONS[spec][1]})
    assert need.status_code==201,need.text
    ranking=employer.get('/api/v1/candidates',params={'need_id':need.json()['id']}).json()['items']
    assert any(p['id']==cid and p['specialization']==spec for p in ranking)
    assert all('email' not in p and 'contact' not in p for p in ranking)
    assert candidate.get('/api/v1/candidates').status_code==403

def test_blueprints_are_reproducible_distinct_and_answers_finite():
    for spec in SPECIALIZATIONS:
        for grade in ['junior','middle','senior']:
            forms=[generate_questions(spec,grade,seed) for seed in range(30)]
            assert len({json.dumps(q,sort_keys=True) for q in forms})==30
            assert len({tuple(sorted((q['family'],q['difficulty']) for q in form)) for form in forms})==1
            for form in forms:
                assert len(form)==8 and len({q['id'] for q in form})==8
                assert evaluate(form,{q['id']:q['answer'] for q in form})[0]==100
                assert evaluate(form,{q['id']:'NaN' for q in form})[0]==0
                assert all('answer' not in q and 'explanation' not in q for q in public_questions(form))
    with pytest.raises(ValueError): generate_questions('unknown','junior',0)

def test_new_domain_answers_against_independent_examples():
    class Fixed:
        def __init__(self): self.values=iter([8,3,2])
        def randint(self,*_): return next(self.values)
    expected={'fullstack':[4,24,16,8],'mobile':[7200,7,16,4],'qa':[72,7,32,13],
              'devops':[7,24,6,36],'data_engineering':[8,32,12,17],
              'data_science':[19,30,1344,18],'cybersecurity':[18,14,16,14],
              'systems_analysis':[56,32,4,17]}
    for spec,values in expected.items():
        assert [q[2] for q in track_questions(spec,2,Fixed())]==values

def test_judge_dataset_preserves_changes_and_revoked_contacts():
    client,_=account('candidate','untouched')
    original=client.get('/api/v1/profile').json()
    first=populate()
    assert first['candidates']>=458 and first['vacancies']==204 and first['challenges']==88
    with SessionLocal() as db:
        assert set(db.scalars(select(m.Vacancy.specialization)))==set(SPECIALIZATIONS)
        assert set(db.scalars(select(m.Challenge.specialization)))==set(SPECIALIZATIONS)
        person=db.scalar(select(m.Candidate).join(m.User).where(m.User.email=='judge.qa@demo.razryad.ru'))
        person.bio='Изменено комиссией — сохранить'
        db.execute(delete(m.ContactGrant));db.commit()
    assert populate()==first
    assert client.get('/api/v1/profile').json()==original
    with SessionLocal() as db:
        assert not list(db.scalars(select(m.ContactGrant)))
        assert db.scalar(select(m.Candidate).join(m.User).where(m.User.email=='judge.qa@demo.razryad.ru')).bio=='Изменено комиссией — сохранить'

def test_frontend_catalog_matches_api_contract():
    data=json.loads(Path('frontend/src/lib/taxonomy.json').read_text('utf-8'))
    assert {v['id']:v['name'] for v in data}=={key:value[0] for key,value in SPECIALIZATIONS.items()}
