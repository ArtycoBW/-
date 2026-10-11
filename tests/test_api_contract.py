from backend.main import app
from fastapi.testclient import TestClient
from backend.taxonomy import SPECIALIZATIONS

def test_public_catalog_returns_all_supported_directions():
    response = TestClient(app).get('/api/v1/catalog')
    assert response.status_code == 200
    payload = response.json()
    assert {item['id'] for item in payload['specializations']} == set(SPECIALIZATIONS)
    assert all(item['name'] and item['skills'] for item in payload['specializations'])
    assert len(payload['grades']) == 3

def test_all_api_success_responses_have_schemas_and_no_password_fields():
    schema=app.openapi()
    for path, methods in schema['paths'].items():
        for method, operation in methods.items():
            if method not in {'get','post','put','patch','delete'}: continue
            for status,response in operation['responses'].items():
                if status.startswith('2'):
                    assert any(media.get('schema') for media in response['content'].values()),(path,method)
            if path not in ['/api/v1/health','/api/v1/ready','/api/v1/catalog','/api/v1/metrics','/api/v1/vacancies'] and '/auth/' not in path:
                assert operation['security']==[{'SessionCookie':[]}]
    assert 'password_hash' not in str(schema['components']['schemas']['UserResult'])
    assert 'seed' not in schema['components']['schemas']['AttemptResult']['properties']
    assert 'contact' not in schema['components']['schemas']['ProfileResult']['required']
    assert schema['paths']['/api/v1/auth/verify']['post']['responses']['200']['content']['application/json']['schema']['$ref'].endswith('/UserResult')
