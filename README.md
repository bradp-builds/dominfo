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
- `whois` - WHOIS queries
- `dig` - DNS lookups (uses Google DNS: 8.8.8.8)
- Standard GNU utilities: `grep`, `awk`, `sed`, `sort`, `date`
- `libmaxminddb` (optional) - For ASN lookup on IPs
  - Install: `sudo apt install libmaxminddb`
  - Database: Download GeoLite2-ASN from https://www.maxmind.com/en/geolite2/free-geolocation-data and place at `/var/lib/GeoIP/GeoLite2-ASN.mmdb`

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
