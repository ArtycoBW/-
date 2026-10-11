from backend.resume import extract_resume

def test_pdf_draft_recognizes_new_tracks_without_certifying_grade():
    draft=extract_resume('Резюме\nЕлена Миронова\nОпыт работы: 5 лет\nSenior\nАнализ данных и ML\nPython, Pandas, Scikit-learn. Командная работа, наставничество.\nelena@example.org')
    assert draft['name']=='Елена Миронова'
    assert draft['experience']==5 and draft['desired_grade']=='senior'
    assert set(draft['skills'])=={'Python','Pandas','Scikit-learn'}
    assert draft['roles']==['Анализ данных и ML']
    assert draft['soft_skills']==['Работа в команде','Наставничество']
    assert 'grade' not in draft

def test_skill_words_do_not_match_substrings_and_unknowns_are_empty():
    draft=extract_resume('Platform Gopher. PostgreSQL. TypeScript. GitHub.')
    assert draft['skills']==['PostgreSQL','TypeScript']
    assert draft['name']=='' and draft['experience'] is None
