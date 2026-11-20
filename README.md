# ModSecurity RPM for EL6

This repository provides an unofficial RPM package for ModSecurity v3 on Enterprise Linux 6 (EL6).

This package is intended for testing and verification of Nginx WAF integration using the ModSecurity-nginx connector.

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

## Install

Install the built RPM package with:

```bash
sudo yum localinstall RPMS/*.rpm
```

If RPM files are stored under an architecture subdirectory, use:

```bash
sudo yum localinstall RPMS/x86_64/*.rpm
```

To inspect RPMs across subdirectories before installing:

```bash
find RPMS -type f -name '*.rpm' | sort
```

Install the appropriate runtime RPM (and its required dependencies). Do not blindly install every RPM if the directory also contains debuginfo, devel, or other optional packages.

## Verify Installation

Check installed files:

```bash
rpm -ql modsecurity | grep /opt/modsecurity
```

Check that the runtime library is visible to the dynamic linker:

```bash
ldconfig -p | grep libmodsecurity
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

Any `not found` entry indicates a missing runtime dependency.

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

Build approach:

- Build Tool: `mock`
- Example Mock Config: `centos+epel-6-x86_64` (if present; archived EL6 repositories or a custom mock configuration may be required)

EL6's default GCC 4.4.x is not sufficient for many modern C++ components. Depending on the source and dependencies, a newer toolchain and backported development libraries may be required.

Because EL6 is end-of-life, repository metadata and packages may no longer be available from normal mirrors. Use appropriate archives and verify dependency versions and package provenance. A successful build does not establish security support or runtime compatibility.

## Production Notes

**EL6 is end-of-life and should not be treated as a supported production platform.** Prefer migrating to a supported operating system. Any EL6 deployment requires an explicit risk decision and compensating controls.

For integration verification:

1. Build and inspect the ModSecurity RPM and its dependencies.
2. Install the RPM in an isolated EL6 test environment.
3. Install or use an Nginx build with ModSecurity-nginx support.
4. Configure OWASP CRS manually.
5. Start with `SecRuleEngine DetectionOnly`.
6. Review audit logs and verify rule execution.
7. Add local exclusions for false positives.
8. Only consider `SecRuleEngine On` after testing and risk review.
9. Keep CRS configuration and local exclusions under version control.

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

