"""OpenAPI-ответы поверх явных DTO. Не меняет сериализацию приватных полей."""
from copy import deepcopy
from fastapi.openapi.utils import get_openapi
from sqlalchemy import Boolean, Integer, Float, JSON
from backend import models as m
from backend.taxonomy import SPECIALIZATIONS
from backend.account import router as account_router
from backend.fsp_oidc import router as fsp_router

def obj(properties, required=None):
    return {"type":"object","properties":properties,"required":list(properties) if required is None else required}
def ref(name): return {"$ref":f"#/components/schemas/{name}"}
def array(items): return {"type":"array","items":items}
S={"type":"string"}; N={"type":"number"}; B={"type":"boolean"}

def row_schema(model, exclude=()):
    props={}
    for col in model.__table__.columns:
        if col.name in exclude: continue
        kind=col.type
        field={"type":"boolean" if isinstance(kind,Boolean) else "integer" if isinstance(kind,Integer) else "number" if isinstance(kind,Float) else "object" if isinstance(kind,JSON) else "string"}
        if col.name=='skills': field=array(S)
        if col.name=='specialization': field={**S,'enum':list(SPECIALIZATIONS)}
        if col.name in ['grade','desired_grade']: field={**S,'enum':['junior','middle','senior']}
        if col.nullable: field={"anyOf":[field,{"type":"null"}]}
        props[col.name]=field
    return obj(props)

def install_contract(app):
    def openapi():
        if app.openapi_schema: return app.openapi_schema
        schema=get_openapi(title=app.title,version=app.version,description=app.description,routes=app.routes)
        models=schema.setdefault('components',{}).setdefault('schemas',{})
        for name, model in [('CompanyResult',m.Company),('NeedResult',m.Need),('VacancyResult',m.Vacancy),('SubmissionResult',m.Submission),('ApplicationResult',m.Application),('ChallengeResult',m.Challenge),('InvitationResult',m.Invitation)]:
            models[name]=row_schema(model)
        models['UserResult']=row_schema(m.User,('password_hash','created_at'))
        models['AchievementResult']=row_schema(m.Achievement,('candidate_id','external_id'))
        models['MatchResult']=obj({'score':N,'mode':S,'baseline_score':N,'learned_score':{'anyOf':[N,{'type':'null'}]},'blend':obj({'baseline':N,'learned':N}),'matched_skills':array(S),'missing_skills':array(S),'factors':array(obj({'key':S,'value':N,'contribution':N})),'explanation':array(S),'notice':S})
        profile=row_schema(m.Candidate,('contact','consent','fsp_id'))
        profile['properties'].update({'category':{'anyOf':[S,{'type':'null'}]},'achievements':array(ref('AchievementResult')),'contacts_unlocked':B,'grade_change_available_at':{'anyOf':[N,{'type':'null'}]},'contact':S,'email':S,'consent':B,'fsp_id':{'anyOf':[S,{'type':'null'}]},'match':ref('MatchResult')})
        profile['description']='Контакты и email отсутствуют до адресного согласия. consent/fsp_id доступны только владельцу. match возвращается в подборке.'
        models['ProfileResult']=profile
        attempt=row_schema(m.Attempt,('seed','questions'))
        attempt['properties'].update({'answers':{'type':'object','additionalProperties':S},'questions':array(obj({'id':S,'skill':S,'text':S,'difficulty':{'type':'integer'}})),'outcomes':array(obj({'id':S,'skill':S,'correct':B}))})
        models['AttemptResult']=attempt
        for name in ['VacancyResult','InvitationResult','ApplicationResult','ChallengeResult']:
            models[name]['properties']['company_name']=S
        models['InvitationResult']['properties'].update({'candidate_name':S,'contacts_unlocked':B,'candidate_contact':S,'candidate_email':S})
        models['ApplicationResult']['properties'].update({'candidate_name':S,'vacancy_title':S,'candidate':ref('ProfileResult')})
        models['ChallengeResult']['properties']['submissions']=array(ref('SubmissionResult'))
        models['MessageResult']=obj({'message':S,'demo_link':{'anyOf':[S,{'type':'null'}]}},['message'])
        models['RegisterResult']=obj({'message':S,'authenticated':B,'user':ref('UserResult'),'demo_link':{'anyOf':[S,{'type':'null'}]}},['message','authenticated'])
        models['ErrorResult']=obj({'detail':S,'fields':array(obj({'field':S,'code':S}))},['detail'])
        models['ResumeDraft']=obj({'name':S,'bio':S,'skills':array(S),'contact':S,'experience':{'anyOf':[{'type':'integer'},{'type':'null'}]},'desired_grade':{'anyOf':[S,{'type':'null'}]},'roles':array(S),'soft_skills':array(S),'notice':S})
        result_types={
          'register':ref('RegisterResult'),'verify':ref('UserResult'),'login':ref('UserResult'),'logout':ref('MessageResult'),'me':ref('UserResult'),'recover':ref('MessageResult'),'resend':ref('MessageResult'),'reset':ref('MessageResult'),'demo':ref('UserResult'),
          'profile':ref('ProfileResult'),'update_profile':ref('ProfileResult'),'company':ref('CompanyResult'),'update_company':ref('CompanyResult'),
          'attempts':array(ref('AttemptResult')),'start_attempt':ref('AttemptResult'),'save_answers':ref('AttemptResult'),'submit_attempt':ref('AttemptResult'),
          'create_need':ref('NeedResult'),'needs':array(ref('NeedResult')),'candidates':obj({'items':array(ref('ProfileResult')),'total':{'type':'integer'},'offset':{'type':'integer'},'limit':{'type':'integer'}}),'candidate_detail':ref('ProfileResult'),
          'invite':ref('InvitationResult'),'invitations':array(ref('InvitationResult')),'transition_invitation':ref('InvitationResult'),
          'vacancies':obj({'items':array(ref('VacancyResult')),'total':{'type':'integer'}}),'own_vacancies':array(ref('VacancyResult')),'publish':ref('VacancyResult'),'edit_vacancy':ref('VacancyResult'),'archive':ref('VacancyResult'),
          'apply':ref('ApplicationResult'),'applications':array(ref('ApplicationResult')),'transition_application':ref('ApplicationResult'),
          'challenges':array(ref('ChallengeResult')),'create_challenge':ref('ChallengeResult'),'submit_challenge':ref('SubmissionResult'),'review_submission':ref('SubmissionResult'),
          'link_fsp':ref('ProfileResult'),'unlink_fsp':ref('ProfileResult'),'import_pdf':ref('ResumeDraft'),'revoke_contact_grant':ref('MessageResult'),
          'contact_grants':array(obj({'company_id':S,'company_name':S,'reason':S,'created_at':N})),
          'health':obj({'status':S,'version':S,'demo':B,'email_verification':B,'password_recovery':B}),'ready':obj({'status':S,'database':S}),
          'catalog':obj({'specializations':array(obj({'id':S,'name':S,'skills':array(S)})),'grades':array(obj({'id':S,'name':S})),'demo':B}),
          'metrics':{'type':'object','description':'Воспроизводимый отчёт ml/metrics.json: синтетические выборки, метрики ранжирования и оценка банка. Схема расширяется с версиями бенчмарка.','additionalProperties':True},
        }
        schema['components']['securitySchemes']={'SessionCookie':{'type':'apiKey','in':'cookie','name':'razryad_session','description':'HttpOnly cookie после /auth/login. Перед изменением данных браузер передаёт Origin публичного сайта.'}}
        public={'health','ready','catalog','metrics','vacancies','register','verify','login','recover','resend','reset','demo'}
        for route in [*app.routes, *account_router.routes, *fsp_router.routes]:
            if not hasattr(route,'methods') or not route.path.startswith('/api/v1'): continue
            for method in route.methods:
                operation=schema.get('paths',{}).get(route.path,{}).get(method.lower())
                if not operation: continue
                operation['security']=[] if route.name in public else [{'SessionCookie':[]}]
                code=str(route.status_code or 200)
                if route.name=='export_profile': operation['responses'][code]={'description':'PDF с русским шрифтом','content':{'application/pdf':{'schema':{'type':'string','format':'binary'}}}}
                elif route.name == 'finish_fsp': operation['responses'] = {'303': {'description': 'Возврат в профиль после привязки или отмены', 'headers': {'Location': {'schema': S}}}}
                elif route.name in result_types: operation['responses'][code]={'description':'Успешный ответ; видимость персональных полей определяется ролью и адресным согласием.','content':{'application/json':{'schema':deepcopy(result_types[route.name])}}}
                errors={422:'Некорректные поля запроса'}
                if route.name not in public: errors.update({401:'Сессия истекла или отсутствует',403:'Роль не имеет доступа',404:'Ресурс не найден или принадлежит другому пользователю'})
                if method in {'POST','PUT','PATCH','DELETE'}: errors.update({403:'Недопустимый Origin или роль',409:'Конфликт состояния или дубликат',413:'Слишком большой запрос'})
                if '/auth/' in route.path or '/account' in route.path: errors[429]='Лимит попыток авторизации и управления аккаунтом'
                for error,description in errors.items(): operation['responses'][str(error)]={'description':description,'content':{'application/json':{'schema':ref('ErrorResult')}}}
        app.openapi_schema=schema
        return schema
    app.openapi=openapi
