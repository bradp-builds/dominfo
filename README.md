# dominfo

A bash script for retrieving comprehensive DNS and domain registration information.

## Features

- **WHOIS Registration Info** - Registrar, registration dates, updated date, domain status
- **DNS Records** - A, AAAA, NS, CNAME records
- **Mail Records** - MX, SPF, DMARC
- **www Subdomain** - Resolves www AAAA, A, and CNAME records
- **ASN/Owner Info** - Autonomous System Number and organization for IP addresses
- **Colorized Output** - Easy-to-read formatted results

## Requirements

- `bash` (4.0+)
- `whois` - WHOIS queries (registration reports only)
- `dig` - DNS lookups (authoritative servers first; Google DNS as fallback)
- `curl` - HTTPS root hints download and ASN/owner lookup through ip-api.com
- Standard GNU utilities: `grep`, `awk`, `sed`, `sort`, `date`, `timeout`, `head`, `cut`, `xargs`, `stat`, `mktemp`, `mkdir`, `mv`, `rm`

## Installation

```bash
git clone <repository-url>
cd dominfo
chmod +x dominfo
```

## Usage

```bash
./dominfo example.com           # Full report
./dominfo -a example.com        # IP addresses (A, AAAA, www)
./dominfo -m example.com        # Mail settings (MX, SPF, DMARC)
./dominfo -r example.com        # Registration info and name servers
./dominfo -n example.com        # Name servers (alias for -r)
./dominfo -s example.com        # SPF record (alias for -m)
./dominfo -d example.com        # DMARC record (alias for -m)
./dominfo --help                # Show help
```

## DNS freshness and failures

Each run follows DNS delegations from a root server to discover authoritative
servers. Record queries go directly to those servers with recursion disabled.
Delegated subdomains are discovered separately. Server discovery is reused only
within the current run; DNS record answers are not cached by this script.
Discovered nameserver A/AAAA addresses are also looked up through fresh traces.
Record queries use those numeric addresses rather than resolving server names
through the system resolver. Intermediate glue is not used as the final address
answer. BIND's `dig +trace` still manages its own intermediate lookups; this is
not a replacement for a complete resolver.

Each lookup prints the responding server. If authoritative discovery or queries
fail, the script tries Google (`8.8.8.8`) and labels the result as potentially
cached. An authoritative empty answer or NXDOMAIN does not trigger fallback.
Servers can briefly disagree while changes are being published; this script
reports the first successful authoritative response, rather than comparing them.

DNS attempts have short timeouts, each trace is limited to 15 seconds,
WHOIS to 15 seconds, and each ASN request to 8 seconds. Failed lookups are reported
separately from missing records. ASN information is best effort.

Input accepts a hostname or an HTTP/HTTPS URL, normalizes case, removes a leading
`www.` and trailing dot, and rejects multiple domains or malformed hostnames.
Use ASCII/punycode names for internationalized domains; explicit URL ports are
not supported.

Root bootstrap addresses come from the official [IANA root hints](https://www.iana.org/domains/root/files),
downloaded over HTTPS from `https://www.internic.net/domain/named.root`.
The file is cached for its local calendar date at `${XDG_CACHE_HOME:-$HOME/.cache}/dominfo/root-hints`.
Refresh happens on the first run on a different local date; there is no background
process. For example, hints saved at 10 PM are refreshed at 6 AM the next day.
Only root hints are cached across runs, so domain records and delegations are
still queried afresh. Root bootstrap uses the IPv4 addresses from the hints and
tries alternatives if a trace fails.

If refresh fails, expired hints are not used: the report falls back to Google
and labels its answers as potentially cached. If saving the cache fails, a
successful download can still be used for that run. Delete the cache file to
force an early refresh. Calendar-day caching bounds staleness; it does not guarantee
that a root address cannot change during that day. This script does not
validate DNSSEC; an authoritative flag is not cryptographic authentication.

## Checks

```bash
bash -n dominfo
shellcheck dominfo
python3 -m unittest discover -s tests -v
```

The tests use controlled DNS responses and do not require network access.

## Example Output

```
════════════════════════════════════════════════════════
  Domain Information: example.com
════════════════════════════════════════════════════════

[ Registration ]
  Registrar: MarkMonitor Inc.
  Registrar URL: https://www.markmonitor.com
  Registered: 2023-01-15 00:00:00 UTC
  Expires: 2028-01-15 00:00:00 UTC
  Updated: 2024-06-20 00:00:00 UTC
  Status:
    → clientTransferProhibited
    → serverTransferProhibited

  Name Servers:
    → ns1.example.com
    → ns2.example.com

[ IP Addresses ]

  IPv4:
    → 93.184.216.34 [AS15133 (Cloudflare LLC)]

  IPv6:
    → 2606:2800:220:1::248:1893 [AS15133 (Cloudflare LLC)]

  www:
    → CNAME: example.com

[ Mail Settings ]

  MX Records:
    → Priority 10: mail.example.com
    → Priority 20: mail2.example.com

  SPF:
    → v=spf1 include:_spf.example.com ~all

  DMARC:
    → v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com
```

## License

MIT
