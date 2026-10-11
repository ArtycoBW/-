"""Safety checks for the unattended domain verifier; no live network or email."""
import importlib.util
from email.message import EmailMessage
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('domain_release', Path(__file__).with_name('domain-release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseSafetyTests(unittest.TestCase):
    def message(self, origin=release.ORIGIN, sender=release.MAILBOX, recipient=release.MAILBOX, mode='verify'):
        message=EmailMessage()
        message['From'],message['To']=sender,recipient
        message['Subject']='Разряд — подтверждение действия'
        message.set_content(f'{origin}/auth?mode={mode}&token='+ 'a'*32)
        return message.as_bytes()

    def test_only_our_exact_origin_and_expected_kind(self):
        self.assertIsNotNone(release.token_from_message(self.message(), 'verify'))
        self.assertIsNone(release.token_from_message(self.message(origin=release.ORIGIN+'.example.org'), 'verify'))
        self.assertIsNone(release.token_from_message(self.message(mode='reset'), 'verify'))
        self.assertIsNone(release.token_from_message(self.message(sender='other@example.org'), 'verify'))
        self.assertIsNone(release.token_from_message(self.message(recipient='owner@example.org'), 'verify'))

    def test_notification_requires_fresh_success(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(release,'STATE',Path(folder)), patch.object(release.smtplib,'SMTP') as smtp:
            release.save('mail-e2e.json',{'passed':True,'origin':release.ORIGIN,'at':0})
            with self.assertRaises(RuntimeError):release.notify({})
            smtp.assert_not_called()

    def test_notification_ledger_prevents_duplicate(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(release,'STATE',Path(folder)), patch.object(release.smtplib,'SMTP') as smtp:
            release.save('notification.json',{'state':'pending'})
            with self.assertRaises(RuntimeError):release.notify({})
            smtp.assert_not_called()

    def test_preexisting_test_marker_stops_account_mutation(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(release,'STATE',Path(folder)), patch.object(release.httpx,'Client') as client:
            release.save('test-account.json',{'created':True})
            with self.assertRaises(RuntimeError):release.verify_mail({})
            client.assert_not_called()


if __name__=='__main__':unittest.main()
