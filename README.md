# dominfo

A bash script for retrieving comprehensive DNS and domain registration information.

## Features

- **WHOIS Registration Info** - Registrar, registration dates, domain status
- **DNS Records** - A, AAAA, MX, NS records
- **Email Security** - SPF and DMARC records
- **Colorized Output** - Easy-to-read formatted results

## Requirements

- `bash` (4.0+)
- `whois` - WHOIS queries
- `dig` - DNS lookups
- Standard GNU utilities: `grep`, `awk`, `sed`, `sort`, `date`

## Installation

```bash
git clone https://github.com/bradpbuilds/dominfo.git
cd dominfo
chmod +x dominfo
```

## Usage

```bash
./dominfo example.com           # Full report
./dominfo -a example.com         # A records only
./dominfo -m example.com         # MX records only
./dominfo -n example.com         # Name servers only
./dominfo -s example.com         # SPF record only
./dominfo -d example.com         # DMARC record only
./dominfo -r example.com         # Registration info only
./dominfo --help                 # Show help
```

## Example Output

```
════════════════════════════════════════════════════════
  Domain Information: example.com
════════════════════════════════════════════════════════

[ Registration Information ]
Registrar: Registrar.com
Registered: 2023-01-15 00:00:00 UTC
Expires: 2028-01-15 00:00:00 UTC
Status:
  → clientTransferProhibited
  → serverTransferProhibited

[ Name Servers ]
  → ns1.example.com
  → ns2.example.com

[ A Records (IPv4) ]
  → 93.184.216.34

[ MX Records (Mail) ]
  → Priority 0: mail.example.com
```

## License

MIT
