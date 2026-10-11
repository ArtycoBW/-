"""Public preflight and real mail E2E for the separate domain deployment.

Default is read-only. Never edits Docker, DNS, existing accounts or private config.
--verify-mail creates one owned, unpublished test account and removes it via API.
--notify sends the explicitly requested owner email once, after a recent E2E pass.
Private state is in ignored .local/domain-release; tokens are never logged.
"""
import argparse
import email
from email import policy
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr
import imaplib
import json
from pathlib import Path
import re
import secrets
import smtplib
import ssl
import time
from urllib.parse import parse_qs, urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.local/domain-release'
ORIGIN = 'https://razryad.agropulseai.ru'
LEGACY = 'https://especially-eng-finally-walt.trycloudflare.com'
MAILBOX = 'noreply@agropulseai.ru'
EXPECTED_NS = {'brodie.ns.cloudflare.com', 'rosalie.ns.cloudflare.com'}


class CheckFailure(RuntimeError):
    """A static, secret-free diagnostic defined by this verifier."""


def save(name, value):
    STATE.mkdir(parents=True, exist_ok=True)
    target = STATE / name
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)


def require(condition, label):
    if not condition:
        raise CheckFailure(label)


def settings():
    values = {}
    for line in (ROOT / '.local/domain-api.env').read_text(encoding='utf-8-sig').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    require(values.get('PUBLIC_ORIGIN') == ORIGIN, 'Unexpected origin')
    require(values.get('SMTP_USERNAME') == MAILBOX, 'Unexpected mailbox')
    require(values.get('SMTP_HOST') == 'smtp.timeweb.ru', 'Unexpected SMTP host')
    require(values.get('SMTP_STARTTLS') == 'true', 'SMTP TLS required')
    require(values.get('EXPOSE_DEMO_MAIL') == 'false', 'Demo links must remain private')
    return values


def dns(client, resolver, name, kind):
    response = client.get(resolver, params={'name': name, 'type': kind}, headers={'Accept': 'application/dns-json'})
    response.raise_for_status()
    result = response.json()
    require(result.get('Status') == 0, f'DNS pending: {name}/{kind}')
    return [a['data'].rstrip('.') for a in result.get('Answer', []) if a['type'] == {'A':1,'NS':2,'MX':15,'TXT':16}[kind]]


def preflight():
    result = {'at': time.time(), 'ready': False, 'checks': {}, 'errors': []}
    with httpx.Client(timeout=20, follow_redirects=False) as client:
        for index, resolver in enumerate(['https://dns.google/resolve', 'https://cloudflare-dns.com/dns-query']):
            for kind, name in [('NS','agropulseai.ru'), ('A','razryad.agropulseai.ru'), ('MX','agropulseai.ru'), ('TXT','agropulseai.ru'), ('TXT','dkim._domainkey.agropulseai.ru')]:
                key = f'{index}:{kind}:{name}'
                try:
                    values = dns(client, resolver, name, kind)
                    result['checks'][key] = values
                    require(bool(values), f'Empty DNS: {kind}:{name}')
                    if kind == 'NS': require(set(values) == EXPECTED_NS, 'NS propagation pending')
                    if kind == 'MX': require(any('mx1.timeweb.ru' in v for v in values), 'MX mismatch')
                    if kind == 'TXT' and name == 'agropulseai.ru':
                        spf = [v for v in values if 'v=spf1' in v]
                        require(len(spf) == 1 and 'include:_spf.timeweb.ru' in spf[0], 'SPF mismatch')
                    if name.startswith('dkim.'): require(any('p=' in v for v in values), 'DKIM missing')
                except Exception as exc:
                    result['errors'].append(f'{key}: {type(exc).__name__}')
        for label, url in [('legacy',LEGACY+'/api/v1/health'), ('site',ORIGIN), ('health',ORIGIN+'/api/v1/health'), ('ready',ORIGIN+'/api/v1/ready')]:
            try:
                response = client.get(url)
                require(response.status_code == 200, f'{label} HTTP status')
                if label == 'ready': require(response.json().get('database') == 'ok', 'Database not ready')
                if label == 'site': require('text/html' in response.headers.get('content-type',''), 'HTML required')
                result['checks'][label] = response.status_code
            except Exception as exc:
                result['errors'].append(f'{label}: {type(exc).__name__}')
    result['ready'] = not result['errors']
    save('preflight.json', result)
    return result


def connect_mail(cfg):
    connection = imaplib.IMAP4_SSL('imap.timeweb.ru', 993, ssl_context=ssl.create_default_context(), timeout=20)
    connection.login(MAILBOX, cfg['SMTP_PASSWORD'])
    require(connection.select('INBOX', readonly=True)[0] == 'OK', 'Cannot select test inbox')
    return connection


def next_uid(connection):
    status, data = connection.status('INBOX', '(UIDNEXT)')
    require(status == 'OK', 'Cannot read mailbox UIDNEXT')
    match = re.search(rb'UIDNEXT (\d+)', data[0])
    require(match is not None, 'Mailbox UIDNEXT missing')
    return int(match[1])


def token_from_message(raw, mode):
    message = email.message_from_bytes(raw, policy=policy.default)
    if parseaddr(str(message.get('From','')))[1].lower() != MAILBOX or parseaddr(str(message.get('To','')))[1].lower() != MAILBOX:
        return None
    if str(message.get('Subject','')) != 'Разряд — подтверждение действия': return None
    texts = [part.get_content() for part in message.walk() if part.get_content_type() == 'text/plain']
    for url in re.findall(r'https://[^\s<>]+', '\n'.join(texts)):
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        if f'{parsed.scheme}://{parsed.netloc}' == ORIGIN and parsed.path == '/auth' and query.get('mode') == [mode]:
            tokens = query.get('token', [])
            if len(tokens) == 1 and re.fullmatch(r'[A-Za-z0-9_-]{20,200}', tokens[0]): return tokens[0], url
    return None


def wait_message(cfg, first_uid, mode):
    # Only fresh test messages addressed from and to this mailbox are fetched.
    for _ in range(18):
        with connect_mail(cfg) as connection:
            status, data = connection.uid('search', None, f'(UID {first_uid}:* FROM "{MAILBOX}" TO "{MAILBOX}")')
            require(status == 'OK', 'Cannot search test messages')
            for uid in data[0].split():
                if int(uid) < first_uid: continue  # IMAP reversed ranges can return the last old UID.
                status, parts = connection.uid('fetch', uid, '(BODY.PEEK[])')
                require(status == 'OK', 'Cannot read test message')
                for part in parts:
                    if isinstance(part, tuple):
                        found = token_from_message(part[1], mode)
                        if found: return found
        time.sleep(10)
    raise CheckFailure('Test email delivery timeout')


def api(client, path, body=None, *, status=200, method='POST'):
    response = client.request(method, ORIGIN+'/api/v1'+path, json=body)
    require(response.status_code == status, f'{method} {path}: HTTP {response.status_code}, expected {status}')
    return response


def verify_mail(cfg):
    require(not (STATE/'test-account.json').exists(), 'Previous test account needs explicit review; no existing account will be altered')
    require(cfg.get('EMAIL_VERIFICATION_REQUIRED') == 'true' and cfg.get('PASSWORD_RECOVERY_ENABLED') == 'true', 'Domain mail flags are disabled')
    save('mail-e2e.json', {'at':time.time(), 'passed':False, 'origin':ORIGIN})
    password, new_password = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
    proof = {'at':time.time(), 'email':MAILBOX, 'name':'Проверка доставки '+secrets.token_hex(8), 'password':password, 'new_password':new_password, 'created':False}
    save('test-account.json', proof)
    with httpx.Client(timeout=30, headers={'Origin': ORIGIN}, follow_redirects=False) as client:
        with connect_mail(cfg) as connection: first_uid = next_uid(connection)
        response = api(client, '/auth/register', {'email':MAILBOX,'password':password,'role':'candidate','name':proof['name'],'consent':True},status=201)
        proof['created'] = True
        save('test-account.json', proof)
        require(response.json().get('authenticated') is False and response.json().get('demo_link') is None, 'Verification gate or token privacy failed')
        api(client, '/auth/login', {'email':MAILBOX,'password':password},status=403)
        token, link = wait_message(cfg, first_uid, 'verify')
        page = client.get(link)
        require(page.status_code == 200, 'Verification page unavailable')
        verified = api(client, '/auth/verify', {'token':token})
        require(verified.json().get('verified') is True, 'Verification failed')
        proof['id'] = verified.json()['id']
        save('test-account.json', proof)
        cookie = verified.headers.get('set-cookie','').lower()
        require(all(flag in cookie for flag in ['secure','httponly','samesite=lax']), 'Session cookie security failed')
        require(api(client, '/auth/me',method='GET').json()['id'] == proof['id'], 'Wrong identity')
        api(client, '/auth/verify', {'token':token},status=400)
        api(client, '/auth/logout')
        api(client, '/auth/login', {'email':MAILBOX,'password':password})
        with connect_mail(cfg) as connection: first_uid = next_uid(connection)
        recovery = api(client, '/auth/recover', {'email':MAILBOX})
        require(recovery.json().get('demo_link') is None, 'Recovery token exposed')
        reset_token, reset_link = wait_message(cfg, first_uid, 'reset')
        require(client.get(reset_link).status_code == 200, 'Recovery page unavailable')
        api(client, '/auth/reset', {'token':reset_token,'password':new_password})
        api(client, '/auth/me', method='GET',status=401)
        api(client, '/auth/login', {'email':MAILBOX,'password':password},status=401)
        api(client, '/auth/login', {'email':MAILBOX,'password':new_password})
        api(client, '/auth/reset', {'token':reset_token,'password':new_password},status=400)
        require(api(client, '/auth/me',method='GET').json()['id'] == proof['id'], 'Cleanup ownership mismatch')
        api(client, '/account', {'password':new_password,'confirmation':'УДАЛИТЬ'}, method='DELETE')
        api(client, '/auth/me',method='GET',status=401)
    (STATE/'test-account.json').unlink()  # Exact owned local file; the API removed only this account.
    result = {'at':time.time(),'passed':True,'origin':ORIGIN,'checks':['registration gate','SMTP and IMAP delivery','HTTPS verification page','one-time confirmation','secure session','login','password recovery delivery','session revocation','one-time reset','own test account removed']}
    save('mail-e2e.json',result)
    return result


def notify(cfg):
    require(not (STATE/'notification.json').exists(), 'Notification already sent or pending: inspect ledger; do not duplicate')
    result = json.loads((STATE/'mail-e2e.json').read_text(encoding='utf-8'))
    require(result.get('passed') and result.get('origin') == ORIGIN and 0 <= time.time()-result['at'] < 3600, 'A successful E2E in the last hour is required')
    require(cfg.get('EMAIL_VERIFICATION_REQUIRED') == 'true' and cfg.get('PASSWORD_RECOVERY_ENABLED') == 'true', 'Mail flags must remain enabled')
    recipient = json.loads((STATE/'owner-notification.json').read_text(encoding='utf-8'))['recipient']
    require(bool(re.fullmatch(r'[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+', recipient)), 'Invalid owner recipient')
    message = EmailMessage()
    message['From'], message['To'] = cfg['SMTP_FROM'], recipient
    message['Subject'] = 'Разряд — сайт работает, подтверждение почты проверено'
    message['Date'], message['Message-ID'] = formatdate(localtime=False), make_msgid(domain='agropulseai.ru')
    message.set_content(f'Артур, сайт Разряд доступен:\n{ORIGIN}\n\nПроверены публичный HTTPS, готовность API и базы, регистрация с доставкой письма, одноразовое подтверждение почты, вход и восстановление пароля. Подтверждение выполняется по ссылке из письма. Тестовый аккаунт удалён.\n\nАдрес, отправленный комиссии, сохранён:\n{LEGACY}\n\nПроверьте сайт со своей стороны и напишите в чат, всё ли работает.\n')
    # Record intent before SMTP: an interrupted send must never cause a blind duplicate.
    save('notification.json', {'at':time.time(),'state':'pending','recipient':recipient,'message_id':message['Message-ID']})
    with smtplib.SMTP(cfg['SMTP_HOST'], int(cfg.get('SMTP_PORT','587')), timeout=30) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(MAILBOX,cfg['SMTP_PASSWORD'])
        require(not smtp.send_message(message), 'Recipient rejected')
    save('notification.json', {'at':time.time(),'state':'sent','recipient':recipient,'message_id':message['Message-ID']})
    return {'notification':'sent'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--verify-mail', action='store_true')
    mode.add_argument('--notify', action='store_true')
    args = parser.parse_args()
    result = preflight()
    print(json.dumps({'ready': result['ready'], 'errors': result['errors'], 'status_file': str(STATE/'preflight.json')}, ensure_ascii=True), flush=True)
    if not result['ready']: return 2
    if args.verify_mail: result = verify_mail(settings())
    elif args.notify: result = notify(settings())
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        # No exception body: HTTP/mail exceptions may include credentials or raw tokens.
        diagnostic = str(exc) if isinstance(exc, CheckFailure) else type(exc).__name__
        save('failure.json', {'at':time.time(), 'diagnostic':diagnostic})
        print('Check failed; private state retained for inspection. '+diagnostic)
        raise SystemExit(1)
