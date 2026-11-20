Name:           modsecurity
Version:        3.0.17
Release:        1%{?dist}
Summary:        ModSecurity v3 library installed under /opt/modsecurity

License:        Apache-2.0
URL:            https://github.com/owasp-modsecurity/ModSecurity
Source0:        v%{version}.tar.gz

%global modsec_prefix /opt/modsecurity

BuildRequires:  devtoolset-9-gcc
BuildRequires:  devtoolset-9-gcc-c++
BuildRequires:  devtoolset-9-libstdc++-devel
BuildRequires:  pkgconfig
BuildRequires:  make
BuildRequires:  pcre2-devel
BuildRequires:  libxml2-devel
BuildRequires:  yajl-devel >= 2.0.0
BuildRequires:  curl-devel
BuildRequires:  zlib-devel

Requires:       pcre2
Requires:       libxml2
Requires:       yajl >= 2.0.0
Requires:       libcurl
Requires:       zlib

Provides:       libmodsecurity = %{version}-%{release}
Provides:       libmodsecurity%{?_isa} = %{version}-%{release}
Provides:       libmodsecurity-devel = %{version}-%{release}
Provides:       libmodsecurity-devel%{?_isa} = %{version}-%{release}
Provides:       modsecurity-devel = %{version}-%{release}
Provides:       modsecurity-devel%{?_isa} = %{version}-%{release}

%description
ModSecurity v3 library installed under /opt/modsecurity.

This package includes runtime libraries, headers, pkg-config files,
development files, and example configuration files in a single RPM
for local nginx builds.

The Source0 archive must be created from a complete git checkout after
initializing all required submodules and running build.sh on CentOS 7
or another system providing Autoconf 2.69 or later.

The generated configure script must be included in Source0 because
CentOS 6 provides an older Autoconf release.

%prep
%setup -q -n ModSecurity-%{version}

test -x configure || {
    echo "ERROR: generated configure script is missing."
    echo "Run ./build.sh before creating v%{version}.tar.gz."
    exit 1
}

test -f others/libinjection/src/libinjection_html5.c || {
    echo "ERROR: others/libinjection is incomplete."
    echo "Initialize all git submodules before creating Source0."
    exit 1
}

test -f others/mbedtls/tf-psa-crypto/utilities/base64.c || {
    echo "ERROR: others/mbedtls is incomplete."
    echo "Initialize all git submodules before creating Source0."
    exit 1
}

test -f modsecurity.conf-recommended || {
    echo "ERROR: modsecurity.conf-recommended is missing."
    exit 1
}

test -f unicode.mapping || {
    echo "ERROR: unicode.mapping is missing."
    exit 1
}

%build
. /opt/rh/devtoolset-9/enable

export CC=gcc
export CXX=g++
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags} -std=gnu++17"
export LDFLAGS="${LDFLAGS:-} -static-libstdc++ -static-libgcc"

%configure \
    --prefix=%{modsec_prefix} \
    --exec-prefix=%{modsec_prefix} \
    --bindir=%{modsec_prefix}/bin \
    --sbindir=%{modsec_prefix}/sbin \
    --includedir=%{modsec_prefix}/include \
    --libdir=%{modsec_prefix}/lib64 \
    --datadir=%{modsec_prefix}/share \
    --without-lmdb \
    --disable-examples

make %{?_smp_mflags}

%install
. /opt/rh/devtoolset-9/enable

rm -rf %{buildroot}

make install DESTDIR=%{buildroot}

mkdir -p %{buildroot}%{modsec_prefix}/include
mkdir -p %{buildroot}%{modsec_prefix}/lib64
mkdir -p %{buildroot}%{modsec_prefix}/lib64/pkgconfig
mkdir -p %{buildroot}%{modsec_prefix}/share

install -m 0644 modsecurity.conf-recommended \
    %{buildroot}%{modsec_prefix}/share/modsecurity.conf-recommended

install -m 0644 unicode.mapping \
    %{buildroot}%{modsec_prefix}/share/unicode.mapping

if [ -d %{buildroot}%{_includedir}/modsecurity ]; then
    rm -rf %{buildroot}%{modsec_prefix}/include/modsecurity
    mv %{buildroot}%{_includedir}/modsecurity \
        %{buildroot}%{modsec_prefix}/include/
fi

if [ -d %{buildroot}%{_includedir}/modsecurity_test ]; then
    rm -rf %{buildroot}%{modsec_prefix}/include/modsecurity_test
    mv %{buildroot}%{_includedir}/modsecurity_test \
        %{buildroot}%{modsec_prefix}/include/
fi

if [ -d %{buildroot}%{_libdir}/pkgconfig ]; then
    find %{buildroot}%{_libdir}/pkgconfig \
        -maxdepth 1 \
        -name '*.pc' \
        -exec mv -f {} %{buildroot}%{modsec_prefix}/lib64/pkgconfig/ \;
fi

if ls %{buildroot}%{_libdir}/libmodsecurity.so* >/dev/null 2>&1; then
    mv -f %{buildroot}%{_libdir}/libmodsecurity.so* \
        %{buildroot}%{modsec_prefix}/lib64/
fi

find %{buildroot} -name '*.la' -type f -delete

rm -f %{buildroot}%{modsec_prefix}/lib64/libmodsecurity.a
rm -f %{buildroot}%{_libdir}/libmodsecurity.a

[ -d %{buildroot}%{_includedir} ] && \
    find %{buildroot}%{_includedir} -type d -empty -delete || :

[ -d %{buildroot}%{_libdir}/pkgconfig ] && \
    find %{buildroot}%{_libdir}/pkgconfig -type d -empty -delete || :

[ -d %{buildroot}%{_libdir} ] && \
    find %{buildroot}%{_libdir} -type d -empty -delete || :

mkdir -p %{buildroot}%{_sysconfdir}/ld.so.conf.d

cat > %{buildroot}%{_sysconfdir}/ld.so.conf.d/modsecurity.conf <<'EOF'
/opt/modsecurity/lib64
EOF

test -d %{buildroot}%{modsec_prefix}/include/modsecurity || {
    echo "ERROR: ModSecurity headers are missing."
    find %{buildroot} -maxdepth 8 -type f | sort
    exit 1
}

test -f %{buildroot}%{modsec_prefix}/lib64/libmodsecurity.so || {
    echo "ERROR: libmodsecurity.so is missing."
    find %{buildroot} -maxdepth 8 -type f | sort
    exit 1
}

ls %{buildroot}%{modsec_prefix}/lib64/libmodsecurity.so.* \
    >/dev/null 2>&1 || {
    echo "ERROR: versioned libmodsecurity shared library is missing."
    find %{buildroot} -maxdepth 8 -type f | sort
    exit 1
}

ls %{buildroot}%{modsec_prefix}/lib64/pkgconfig/*.pc \
    >/dev/null 2>&1 || {
    echo "ERROR: ModSecurity pkg-config file is missing."
    find %{buildroot} -maxdepth 8 -type f | sort
    exit 1
}

test -f \
    %{buildroot}%{modsec_prefix}/share/modsecurity.conf-recommended || {
    echo "ERROR: modsecurity.conf-recommended is missing."
    find %{buildroot} -maxdepth 8 -type f | sort
    exit 1
}

test -f %{buildroot}%{modsec_prefix}/share/unicode.mapping || {
    echo "ERROR: unicode.mapping is missing."
    find %{buildroot} -maxdepth 8 -type f | sort
    exit 1
}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%doc LICENSE
%doc README.md

%{modsec_prefix}
%config(noreplace) %{_sysconfdir}/ld.so.conf.d/modsecurity.conf

%changelog
* Sat Aug 01 2026 Akiyoshi Kurita <weibu@redadmin.org> - 3.0.16-2
- Port ModSecurity 3.0.16 to CentOS 6
- Build with Developer Toolset 9 and C++17
- Use backported YAJL 2 from the local build repository
- Use PCRE1 and disable LMDB
- Use a configure-generated source archive

* Wed Jul 01 2026 Akiyoshi Kurita <weibu@redadmin.org> - 3.0.16-1
- Update to ModSecurity v3.0.16
- Rebuild complete source archive with submodules

* Sun Jun 21 2026 Akiyoshi Kurita <weibu@redadmin.org> - 3.0.15-2
- Install modsecurity.conf-recommended and unicode.mapping under /opt/modsecurity/share
- Keep nginx configuration under manual control

* Sat Jun 20 2026 Akiyoshi Kurita <weibu@redadmin.org> - 3.0.15-1
- Build ModSecurity v3 under /opt/modsecurity
- Include runtime and development files in one RPM
- Use submodule-expanded source archive
- Normalize headers, libraries, and pkg-config files under /opt/modsecurity
- Package the whole /opt/modsecurity tree
- Remove static archive files
