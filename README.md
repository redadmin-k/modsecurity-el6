# ModSecurity RPM for EL6

This repository provides an unofficial RPM package for ModSecurity v3 on Enterprise Linux 6 (EL6).

This package is intended for testing and verification of Nginx WAF integration using the ModSecurity-nginx connector.

**Dependency:** ModSecurity on EL6 requires the separately backported **YAJL 2.0.4 RPM** from [`redadmin-k/yajl-el6`](https://github.com/redadmin-k/yajl-el6). Install the EL6 YAJL runtime package along with ModSecurity; the standard EL6 repositories may not provide a compatible version.

**Important:** EL6 is end-of-life. This project does not restore vendor security support for EL6 and is not a recommendation to deploy EL6 in production.

## Overview

This RPM is designed to install ModSecurity under:

```text
/opt/modsecurity
```

Example runtime library path:

```text
/opt/modsecurity/lib64/libmodsecurity.so.3
```

The package is intended to include:

- ModSecurity runtime libraries
- ModSecurity headers
- pkg-config files
- Example configuration files
- ldconfig configuration for `/opt/modsecurity/lib64`

The package can be used together with an Nginx build that includes the ModSecurity-nginx connector, provided that both were built with compatible libraries and toolchains.

This RPM does **not** bundle YAJL. YAJL must be installed separately from the EL6 backport.

## Repository Layout

```text
README.md
SPEC/
RPMS/
Logs/
```

RPM files are stored under:

```text
RPMS/
```

## Required YAJL Dependency

ModSecurity v3 on EL6 requires **YAJL 2.0.4**, backported from the CentOS 7 source RPM `yajl-2.0.4-4.el7.src.rpm` for EL6.

YAJL backport repository:

https://github.com/redadmin-k/yajl-el6

Required packages:

- `yajl` — runtime library (`libyajl.so.2`), needed when running the ModSecurity build that links to YAJL
- `yajl-devel` — headers and development files, needed when **building** ModSecurity against YAJL

The `yajl-el6` repository is independent of this repository. Download or build its **EL6 RPMs**, not the original EL7 binaries. A normal EL6 installation may not have the appropriate YAJL packages available.

For a `mock` build, make the backported `yajl` and `yajl-devel` RPMs available through the EL6 mock buildroot or a local RPM repository before building ModSecurity.

## Install

### 1. Install the EL6 YAJL RPM

Obtain the built YAJL RPM from the [`yajl-el6`](https://github.com/redadmin-k/yajl-el6) repository. Replace `/path/to/yajl-el6` below with the directory containing your local checkout or downloaded RPMs.

```bash
sudo yum localinstall /path/to/yajl-el6/RPMS/x86_64/yajl-[0-9]*.rpm
```

The runtime package is required. If you are also compiling ModSecurity or another YAJL-dependent component, install the development package:

```bash
sudo yum localinstall /path/to/yajl-el6/RPMS/x86_64/yajl-devel-*.rpm
```

Check that YAJL was installed and its shared library can be resolved:

```bash
rpm -q yajl
ldconfig -p | grep libyajl
```

Expected library name (path may vary):

```text
libyajl.so.2 => /usr/lib64/libyajl.so.2
```

### 2. Install the ModSecurity RPM

Install the ModSecurity runtime RPM from this repository:

```bash
sudo yum localinstall RPMS/x86_64/modsecurity-[0-9]*.rpm
```

If RPMs are stored directly under `RPMS/`, adjust the path accordingly. Use `find RPMS -type f -name '*.rpm' | sort` to inspect the available files. Avoid installing debuginfo or optional development packages unintentionally.

You can also install the **YAJL runtime RPM and ModSecurity runtime RPM in one yum transaction**, which lets yum resolve the locally supplied YAJL dependency:

```bash
sudo yum localinstall \
  /path/to/yajl-el6/RPMS/x86_64/yajl-[0-9]*.rpm \
  RPMS/x86_64/modsecurity-[0-9]*.rpm
```

If yum reports other missing shared libraries, install the corresponding EL6-compatible dependencies. Do not substitute EL7 binary RPMs for EL6 packages.

## Verify Installation

Check installed YAJL and ModSecurity packages:

```bash
rpm -q yajl modsecurity
rpm -ql modsecurity | grep /opt/modsecurity
```

Check that both runtime libraries are visible to the dynamic linker:

```bash
ldconfig -p | grep -E 'libmodsecurity|libyajl'
```

Expected example:

```text
libmodsecurity.so.3 => /opt/modsecurity/lib64/libmodsecurity.so.3
```

If the library does not appear, run:

```bash
sudo ldconfig
```

Then verify that the library and its dependencies can be resolved:

```bash
ldd /opt/modsecurity/lib64/libmodsecurity.so.3
```

Any `not found` entry indicates a missing runtime dependency. In particular, verify that `libyajl.so.2` resolves to the installed EL6 YAJL backport.

## Example Paths

Main installation directory:

```text
/opt/modsecurity
```

Library directory:

```text
/opt/modsecurity/lib64
```

Header directory:

```text
/opt/modsecurity/include
```

pkg-config directory:

```text
/opt/modsecurity/lib64/pkgconfig
```

Example configuration files:

```text
/opt/modsecurity/share/modsecurity.conf-recommended
/opt/modsecurity/share/unicode.mapping
```

ldconfig configuration:

```text
/etc/ld.so.conf.d/modsecurity.conf
```

These paths describe the intended RPM layout; confirm them against the built package using `rpm -ql`.

## Nginx Integration Notes

This package only installs ModSecurity itself.

To use ModSecurity with Nginx, Nginx must be built with the ModSecurity-nginx connector.

When building Nginx, make sure the build can find ModSecurity under:

```text
/opt/modsecurity
```

For example:

```bash
export PKG_CONFIG_PATH=/opt/modsecurity/lib64/pkgconfig
```

Confirm that Nginx was built with the ModSecurity-nginx connector:

```bash
nginx -V 2>&1 | grep -i modsecurity
```

For a statically compiled connector, the configure arguments may include:

```text
--add-module=ModSecurity-nginx
```

Alternatively, a dynamically built connector may appear as `--add-dynamic-module=...`; verify that the `.so` module is loaded by Nginx.

If Nginx is linked directly against `libmodsecurity.so.3`, check its dependencies:

```bash
ldd /usr/sbin/nginx | grep modsecurity
```

Expected example for a directly linked build:

```text
libmodsecurity.so.3 => /opt/modsecurity/lib64/libmodsecurity.so.3
```

If the connector is a dynamic Nginx module, check that module with `ldd` instead. The absence of `libmodsecurity` from `ldd /usr/sbin/nginx` does not necessarily indicate a problem for dynamically loaded modules.

## ModSecurity Rule Engine

Before enabling blocking mode, run ModSecurity in detection-only mode and review logs carefully.

Example:

```apache
SecRuleEngine DetectionOnly
```

After sufficient verification, blocking mode can be enabled if appropriate.

```apache
SecRuleEngine On
```

## Basic Configuration Example

Create an Nginx ModSecurity configuration directory:

```bash
sudo mkdir -p /etc/nginx/modsec
```

Copy the recommended configuration:

```bash
sudo cp /opt/modsecurity/share/modsecurity.conf-recommended /etc/nginx/modsec/modsecurity.conf
sudo cp /opt/modsecurity/share/unicode.mapping /etc/nginx/modsec/unicode.mapping
```

For initial testing, set detection-only mode:

```bash
sudo sed -i 's/^SecRuleEngine .*/SecRuleEngine DetectionOnly/' /etc/nginx/modsec/modsecurity.conf
```

Example `/etc/nginx/modsec/main.conf`:

```apache
Include /etc/nginx/modsec/modsecurity.conf
```

Example Nginx server configuration:

```nginx
server {
    listen 80;
    server_name example.local;

    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsec/main.conf;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
    }
}
```

Test Nginx configuration:

```bash
sudo nginx -t
```

Restart Nginx with the EL6 SysVinit service command:

```bash
sudo service nginx restart
```

If Nginx was built or installed manually without a SysVinit service script, use its own management procedure instead.

## OWASP Core Rule Set

OWASP Core Rule Set (CRS) is not bundled in this package.

CRS should be installed or placed manually.

A typical include layout is:

```apache
Include /etc/nginx/modsec/modsecurity.conf
Include /etc/nginx/modsec/crs-setup.conf
Include /etc/nginx/modsec/rules/*.conf
```

CRS 3.3.x may serve as a starting point for compatibility testing with ModSecurity v3. It is not guaranteed to be compatible with every EL6 build or local ruleset.

CRS 4.x may also work, but it should be validated separately before use.

## Simple Test

After Nginx is configured with ModSecurity, OWASP CRS, and blocking mode enabled, a simple SQL injection test can be used:

```bash
curl -i 'http://127.0.0.1/?id=1%20UNION%20SELECT%201,2,3'
```

If an enabled rule matches and an appropriate disruptive action is configured, the response may be:

```text
HTTP/1.1 403 Forbidden
```

A `403` response is **not guaranteed** by this test request alone. If the request is detected but still returns `200`, check the loaded CRS rules, anomaly thresholds, rule actions, audit logs, and local exclusions.

## Target Environment

Intended target environment (not a claim of completed testing):

- EL6 x86_64 (CentOS 6 / RHEL 6)
- ModSecurity v3.0.16 (target source version; build success must be verified)
- Nginx with the ModSecurity-nginx connector
- YAJL 2.0.4 EL6 backport from `redadmin-k/yajl-el6` (required dependency)

Build approach:

- Build Tool: `mock`
- Example Mock Config: `centos+epel-6-x86_64` (if present; archived EL6 repositories or a custom mock configuration may be required)

EL6's default GCC 4.4.x is not sufficient for many modern C++ components. Depending on the source and dependencies, a newer toolchain and backported development libraries may be required. **Install `yajl-devel` from the EL6 backport in the build environment**; installing the YAJL runtime package on the host alone does not satisfy ModSecurity's build-time headers requirement.

Because EL6 is end-of-life, repository metadata and packages may no longer be available from normal mirrors. Use appropriate archives and verify dependency versions and package provenance. A successful build does not establish security support or runtime compatibility.

## Production Notes

**EL6 is end-of-life and should not be treated as a supported production platform.** Prefer migrating to a supported operating system. Any EL6 deployment requires an explicit risk decision and compensating controls.

For integration verification:

1. Install or provide the `yajl-el6` backport (`yajl-devel` in the buildroot, `yajl` on the test host).
2. Build and inspect the ModSecurity RPM and its dependencies.
3. Install YAJL and ModSecurity in an isolated EL6 test environment.
4. Install or use an Nginx build with ModSecurity-nginx support.
5. Configure OWASP CRS manually.
6. Start with `SecRuleEngine DetectionOnly`.
7. Review audit logs and verify rule execution.
8. Add local exclusions for false positives.
9. Only consider `SecRuleEngine On` after testing and risk review.
10. Keep CRS configuration and local exclusions under version control.

ModSecurity and CRS should be treated as one layer of defense, not as a replacement for application fixes, patching, access control, rate limiting, or regular security updates.

## Disclaimer

This repository is unofficial.

It is not provided, maintained, endorsed, or supported by AlmaLinux OS Foundation, CentOS, Red Hat, OWASP, Trustwave, ModSecurity, nginx.org, or any upstream project.

Use this repository at your own risk.

The author provides no warranty of any kind.

Please test carefully in an isolated verification environment before using it on any system handling real traffic.

## License

ModSecurity is licensed under the Apache License 2.0.

See the upstream ModSecurity project for details:

https://github.com/owasp-modsecurity/ModSecurity

Packaging files in this repository are provided for RPM build and integration testing purposes.

Unless otherwise stated, packaging files in this repository are released under the Apache License 2.0.

