import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'dominfo'
FUNCTIONS = SCRIPT.read_text().split('\ndomain=""\n')[0]


class DominfoTests(unittest.TestCase):
    def run_query(self, scenario, record='A'):
        with tempfile.TemporaryDirectory() as tmp:
            dig = Path(tmp) / 'dig'
            dig.write_text('''#!/bin/bash
printf '%s\\n' "$*" >> "$CALLS"
if [[ "$*" == *+trace* ]]; then
    [[ "$SCENARIO" == root_failover && "$1" == @198.41.0.4 ]] && exit 9
    if [[ "$3" == NS ]]; then
        printf 'com. 1 IN NS a.gtld.example.\\nexample.com. 1 IN NS ns1.example.com.\\nexample.com. 1 IN NS ns2.example.com.\\n'
    else
        # Stale intermediate glue must never be used as the terminal answer.
        printf '%s 1 IN A 192.0.2.99\\n' "$2"
        printf ';; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1\\n'
        if [[ "$SCENARIO" == address_failure ]]; then
            printf ';; flags: qr; QUERY: 1, ANSWER: 0\\n'
        else
            printf ';; flags: qr aa; QUERY: 1, ANSWER: 1\\n'
            if [[ "$3" == A ]]; then
                ip=192.0.2.53
                [[ "$2" == ns2.example.com. ]] && ip=192.0.2.54
                printf '%s 60 IN A %s\\n' "$2" "$ip"
            fi
        fi
    fi
    exit
fi
if [[ "$1" == @192.0.2.53 && "$SCENARIO" == failover ]]; then exit 9; fi
if [[ "$1" != @8.8.8.8 && "$SCENARIO" == fallback ]]; then
    printf ';; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 1\\n'
    exit
fi
if [[ "$SCENARIO" == failure ]]; then exit 9; fi
status=NOERROR
[[ "$SCENARIO" == negative ]] && status=NXDOMAIN
printf ';; ->>HEADER<<- opcode: QUERY, status: %s, id: 1\\n' "$status"
flags='qr aa'
[[ "$SCENARIO" == referral && "$1" != @8.8.8.8 ]] && flags=qr
printf ';; flags: %s; QUERY: 1, ANSWER: 0\\n' "$flags"
if [[ "$SCENARIO" != negative && "$SCENARIO" != empty ]]; then
    printf 'example.com. 60 IN CNAME target.example.\\ntarget.example. 60 IN A 192.0.2.1\\n'
fi
printf ';; SERVER: %s#53\\n' "${1#@}"
''')
            dig.chmod(0o755)
            calls = Path(tmp) / 'calls'
            env = dict(os.environ, PATH=f'{tmp}:{os.environ["PATH"]}',
                       SCENARIO=scenario, CALLS=str(calls))
            code = FUNCTIONS + '''
domain=example.com
root_ips=$'198.41.0.4\\n192.33.4.12'
authoritative_ns=$(find_authoritative_ns "$domain")
query_dns "''' + record + '''" "$domain"
result=$?
printf 'RESULT=%s\\n' "$dns_result"
exit "$result"
'''
            result = subprocess.run(['bash', '-c', code], env=env,
                                    text=True, capture_output=True)
            return result, calls.read_text()

    def test_authoritative_and_address_filtering(self):
        result, calls = self.run_query('normal')
        self.assertEqual(result.returncode, 0)
        self.assertIn('RESULT=192.0.2.1\n', result.stdout)
        self.assertIn('ns1.example.com. (192.0.2.53#53)', result.stdout)
        self.assertNotIn('@a.gtld.example.', calls)
        self.assertNotIn('@8.8.8.8', calls)
        self.assertIn('+norecurse', calls)
        self.assertNotIn('@ns', calls)
        self.assertNotIn('@192.0.2.99', calls)

    def test_root_failover(self):
        result, calls = self.run_query('root_failover')
        self.assertEqual(result.returncode, 0)
        self.assertIn('@192.33.4.12', calls)
        self.assertIn('RESULT=192.0.2.1', result.stdout)

    def test_authoritative_failover(self):
        result, calls = self.run_query('failover')
        self.assertEqual(result.returncode, 0)
        self.assertIn('ns2.example.com. (192.0.2.54#53)', result.stdout)
        self.assertNotIn('@8.8.8.8', calls)

    def test_negative_and_empty_answers_do_not_fallback(self):
        for scenario in ('negative', 'empty'):
            with self.subTest(scenario=scenario):
                result, calls = self.run_query(scenario)
                self.assertEqual(result.returncode, 0)
                self.assertIn('RESULT=\n', result.stdout)
                self.assertNotIn('@8.8.8.8', calls)

    def test_google_fallback_is_labeled(self):
        result, calls = self.run_query('fallback')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Google fallback; potentially cached', result.stdout)
        self.assertIn('@192.0.2.54', calls)
        self.assertIn('+recurse', calls)

    def test_non_authoritative_response_is_not_accepted(self):
        result, calls = self.run_query('referral')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Google fallback; potentially cached', result.stdout)
        self.assertIn('@192.0.2.54', calls)

    def test_nameserver_address_failure_uses_google(self):
        result, calls = self.run_query('address_failure')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Google fallback; potentially cached', result.stdout)
        self.assertNotIn('@192.0.2.99', calls)
        self.assertNotIn('@ns', calls)

    def test_total_failure_is_explicit(self):
        result, _ = self.run_query('failure')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DNS lookup failed', result.stderr)

    def test_invalid_input(self):
        for args in (['one.com', 'two.com'], ['https://'], ['bad..com'],
                     ['bad_name.com'], ['example.com:443'], ['example.com..'],
                     ['example.com\nignored']):
            with self.subTest(args=args):
                result = subprocess.run(['bash', str(SCRIPT), *args],
                                        text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Error:', result.stderr)

    def test_utc_timestamp(self):
        result = subprocess.run(
            ['bash', '-c', FUNCTIONS + '\nconvert_timestamp 2026-01-15T12:00:00Z'],
            env=dict(os.environ, TZ='America/New_York'), text=True, capture_output=True)
        self.assertEqual(result.stdout.strip(), '2026-01-15 07:00:00 EST')


class RootHintsTests(unittest.TestCase):
    HINTS = 'A.ROOT-SERVERS.NET. 3600000 A 192.0.2.10\n'
    NOW = 1768474800  # 2026-01-15 06:00 America/New_York (11:00 UTC)

    def check_cache(self, age=None, download=None, fail=False, cached=None):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cache = folder / 'dominfo' / 'root-hints'
            cache.parent.mkdir()
            if age is not None:
                cache.write_text(self.HINTS if cached is None else cached)
                timestamp = self.NOW - age
                os.utime(cache, (timestamp, timestamp))
            curl = folder / 'curl'
            curl.write_text('#!/bin/bash\nprintf "called\\n" >> "$CALLS"\n'
                            '[[ "$FAIL" == yes ]] && exit 22\n'
                            'printf "%s" "$DOWNLOAD"\n')
            curl.chmod(0o755)
            date = folder / 'date'
            date.write_text('#!/bin/bash\n'
                            'if [[ "$1" == +%s ]]; then printf "%s\\n" "$NOW"; '
                            'else exec /usr/bin/date "$@"; fi\n')
            date.chmod(0o755)
            calls = folder / 'calls'
            env = dict(os.environ, PATH=f'{tmp}:{os.environ["PATH"]}',
                       XDG_CACHE_HOME=tmp, CALLS=str(calls),
                       NOW=str(self.NOW), TZ="America/New_York",
                       FAIL='yes' if fail else 'no',
                       DOWNLOAD=self.HINTS if download is None else download)
            code = FUNCTIONS + '\nload_root_hints\nstatus=$?\nprintf "%s\\n" "$root_ips"\nexit "$status"'
            result = subprocess.run(['bash', '-c', code], env=env,
                                    text=True, capture_output=True)
            return result, calls.exists(), cache.read_text() if cache.exists() else None

    def test_fresh_cache_skips_download(self):
        result, downloaded, _ = self.check_cache(age=60, fail=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(downloaded)
        self.assertEqual(result.stdout.strip(), '192.0.2.10')

    def test_same_local_date_reuses_cache(self):
        # 1 AM and 6 AM are both January 15 in the configured local timezone.
        result, downloaded, _ = self.check_cache(age=5 * 3600, fail=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(downloaded)

    def test_missing_or_expired_cache_downloads(self):
        for age in (None, 8 * 3600, 86400):
            with self.subTest(age=age):
                result, downloaded, cached = self.check_cache(age=age)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(downloaded)
                self.assertEqual(cached, self.HINTS)

    def test_failed_refresh_does_not_use_or_replace_expired_hints(self):
        result, downloaded, cached = self.check_cache(age=8 * 3600, fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(downloaded)
        self.assertEqual(result.stdout.strip(), '')
        self.assertIn('Google fallback', result.stderr)
        self.assertEqual(cached, self.HINTS)

    def test_invalid_download_is_rejected(self):
        for content in ('<html>Error</html>', 'A.ROOT-SERVERS.NET. 1 A evil.example.',
                        'A.ROOT-SERVERS.NET. 1 A 999.0.0.1'):
            with self.subTest(content=content):
                result, _, cached = self.check_cache(download=content)
                self.assertNotEqual(result.returncode, 0)
                self.assertIsNone(cached)

    def test_corrupt_or_future_dated_cache_refreshes(self):
        for age, content in ((60, 'bad cache'), (-3600, self.HINTS)):
            with self.subTest(age=age):
                result, downloaded, _ = self.check_cache(age=age, cached=content)
                self.assertEqual(result.returncode, 0)
                self.assertTrue(downloaded)


if __name__ == '__main__':
    unittest.main()
