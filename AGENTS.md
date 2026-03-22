# AGENTS.md

## Project Overview

This is a bash script project (`dominfo`) that provides DNS and domain registration information lookup. It queries WHOIS data, DNS records (A, AAAA, MX, NS, SPF, DMARC) for a given domain, and optionally enriches IPs with ASN/owner information.

---

## Build/Lint/Test Commands

### Syntax Checking
```bash
bash -n dominfo           # Check bash syntax without executing
```

### Linting (Recommended)
```bash
shellcheck dominfo        # Comprehensive bash script linting
```

### Running the Script
```bash
./dominfo example.com              # Full report
./dominfo -a example.com            # A records only
./dominfo -m example.com            # MX records only
./dominfo -n example.com            # Name servers only
./dominfo -s example.com            # SPF record only
./dominfo -d example.com            # DMARC record only
./dominfo -r example.com            # Registration info only
./dominfo --help                    # Show help
```

---

## Code Style Guidelines

### Shell/Bash Conventions

**Shebang and Permissions**
- Use `#!/bin/bash` for bash scripts
- Scripts must be executable (`chmod +x dominfo`)

**Variable Naming**
- Use lowercase with underscores: `domain`, `whois_output`
- Constants can be uppercase: `RED`, `GREEN`, `NC`
- Always quote variables containing paths or user input

**Functions**
- Use lowercase with underscores: `get_registration_info`, `print_header`
- Define functions before use (no forward declarations)
- Use `local` for function-local variables
- Prefer `function_name()` syntax (not `function name`)

**Conditionals**
- Always use `[[ ]]` for string comparisons (not `[ ]`)
- Use `[[ $var =~ regex ]]` for pattern matching
- Quote variables: `[[ "$var" == "value" ]]`
- Use `=~` for regex matching (Bash 3+)

**Loops**
- Use `while read -r` for reading lines (always use `-r`)
- Prefer `for` loops for known iterations
- Use `done < <(command)` to avoid subshell issues

**Error Handling**
- Redirect stderr: `command 2>/dev/null`
- Check exit status: `if [ $? -eq 0 ]` or `if command; then`
- Exit with meaningful codes: `exit 0` (success), `exit 1` (error)

**Command Substitution**
- Prefer `$(command)` over backticks: `$(echo "$var")`
- Nest command substitutions when needed

---

## Common Patterns in This Project

**Color Output**
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'  # No Color
echo -e "${RED}Error message${NC}"
```

**Domain Input Normalization**
```bash
domain=$(echo "$domain" | sed -e 's|^https\?://||' -e 's|^www\.||' -e 's|/$||' | awk -F/ '{print $1}')
```

**Parsing Whois/DNS Output**
```bash
# Extract field after colon, preserve multi-word values
grep -i "Registrar:" | head -1 | awk -F': ' '{for(i=2;i<=NF;i++) printf "%s ", $i; print ""}' | xargs

# Sort and deduplicate
grep -i "Domain Status:" | grep -v "(" | sed 's/^[^:]*: *//' | sort -f -u
```

**Argument Parsing**
```bash
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            domain="$1"
            ;;
    esac
    shift
done
```

---

## Dependencies

The script requires these system utilities:
- `whois` - WHOIS queries
- `dig` - DNS lookups (Google DNS: 8.8.8.8)
- `date` - Timestamp conversion
- Standard GNU utilities: `grep`, `awk`, `sed`, `sort`
- `mmdblookup` (optional) - ASN lookup for IPs (from libmaxminddb package)
  - Database: `/var/lib/GeoIP/GeoLite2-ASN.mmdb`

---

## Git Workflow

```bash
git add dominfo
git commit -m "Descriptive commit message"
git push origin main
```

Commit message style: Use present tense, imperative mood ("Add feature" not "Added feature").
