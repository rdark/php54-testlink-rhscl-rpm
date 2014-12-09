%{?scl:%scl_package testlink}
%{!?scl:%global pkg_name %{name}}

%define testlinkdir %{_root_localstatedir}/www/%{pkg_name}
%define web_user    apache
%define web_group   apache
%define upload_area %{testlinkdir}/upload_area
# somewhere buried are arch-dependent binaries..
%define _binaries_in_noarch_packages_terminate_build   0
# disable python bytecompiling
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

# This macro was added in Fedora 20. Use the old version if it's undefined
# on older Fedoras and RHELs.
# https://fedoraproject.org/wiki/Changes/UnversionedDocdirs
%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{pkg_name}-%{version}}

Name:       %{?scl_prefix}testlink
Version:    1.9.12
Release:    2%{?dist}
Summary:    Open Source Test Management
Group:      Applications/Internet
License:    GPLv2+
URL:        http://sourceforge.net/projects/testlink
Source0:    http://downloads.sourceforge.net/%{pkg_name}/%{pkg_name}-%{version}.tar.gz
Source1:    config_db.inc.php
Patch0:     0001-custom_config_example-set_logging-set_upload.patch
Patch1:     6620-admin-rights-test-plan-management.patch
BuildArch:  noarch
Requires:   %{?scl_prefix}php
Requires:   %{?scl_prefix}php-gd
Requires:   %{?scl_prefix}php-mysql
Requires:   %{?scl_prefix}php-ldap
# conflict with system PHP (apache needs to only have one php loaded)
Conflicts:  php
# conflict with testlink (as we use _root_ for logging and application root)
Conflicts:  testlink

%description
The application provides Test specification, Test plans and execution,
Reporting, Requirements specification and collaborate with well-known bug
trackers.

%prep
%setup -n %{pkg_name}-%{version} -q
# set default logging + upload location
%patch0 -p0
%if "%{version}" == "1.9.12"
# patch for broken test plan management in 1.9.12
%patch1 -p0
%endif

%build
# nope

%install
rm -rf %{buildroot}
%{__mkdir} -p %{buildroot}%{_root_sysconfdir}/%{pkg_name}
%{__mkdir} -p %{buildroot}/%{testlinkdir}
%{__mkdir} -p %{buildroot}%{upload_area}
%{__mkdir} -p %{buildroot}%{_root_localstatedir}/log/%{pkg_name}

# remove logs
%{__rm} -rf logs/
# remove upload_area
%{__rm} -rf upload_area/
# sloppy repo management - remove intellij idea files
%{__rm} -rf .idea/
# sloppy repo management - remove eclipse project files
%{__rm} -f .project
# remove .gitignore
%{__rm} -f .gitignore

# move/symlink config files to /etc
%{__cp} -f custom_config.inc.php.example %{buildroot}%{_root_sysconfdir}/%{pkg_name}/custom_config.inc.php
%{__rm} -f custom_config.inc.php.example
# copy source1 to config dir
%{__cp} -f %{S:1} %{buildroot}%{_root_sysconfdir}/%{pkg_name}/config_db.inc.php
%{__cp} -rf cfg %{buildroot}%{_root_sysconfdir}/%{pkg_name}/
%{__rm} -rf cfg
pushd %{buildroot}/%{testlinkdir}
%{__ln_s} -f %{_root_sysconfdir}/%{pkg_name}/custom_config.inc.php custom_config.inc.php
%{__ln_s} -f %{_root_sysconfdir}/%{pkg_name}/cfg cfg
cd %{buildroot}%{_root_sysconfdir}/%{pkg_name}
find cfg/ -type f | sed 's,^,\%attr(0640\,root\,%{web_group}) %config(noreplace) %{_root_sysconfdir}/%{pkg_name}/,' > %{_builddir}/file.list.%{pkg_name}
popd

# copy over all files
cp -pr * %{buildroot}%{testlinkdir}/
pushd %{buildroot}%{testlinkdir}/
find . -type d | sed '1,2d;s,^\.,\%attr(0755\,root\,root) \%dir %{testlinkdir},' >> %{_builddir}/file.list.%{pkg_name}
find . -type f | sed 's,^\.,\%attr(0644\,root\,root) %{testlinkdir},' >> %{_builddir}/file.list.%{pkg_name}
popd
# delete directories that need specific permissions
sed -i '\!%%dir %{upload_area}!d' %{_builddir}/file.list.%{pkg_name}
sed -i '\!%%dir %{testlinkdir}/gui/templates_c!d' %{_builddir}/file.list.%{pkg_name}
# quote any filenames with spaces as files directive fails on these
sed -i 's/[[:space:]]\(\/.*[^/]\+[[:space:]][^/]\+\)\(\..*\)$/ "\1\2"/' %{_builddir}/file.list.%{pkg_name}

%clean
rm -rf %{buildroot}

%files -f %{_builddir}/file.list.%{pkg_name}
%defattr(-,root,root,-)
%doc CHANGELOG LICENSE README BUYING_SUPPORT.TXT CODE_REUSE docs/*
%attr(0770,%{web_user},%{web_group}) %{upload_area}
%attr(0770,%{web_user},%{web_group}) %{_root_localstatedir}/log/%{pkg_name}
%attr(0640,root,%{web_group}) %config(noreplace) %{_root_sysconfdir}/%{pkg_name}/custom_config.inc.php
%attr(0640,root,%{web_group}) %config(noreplace) %{_root_sysconfdir}/%{pkg_name}/config_db.inc.php
%dir %attr(0755,root,root) %{testlinkdir}
%dir %attr(0755,%{web_user},%{web_group}) %{testlinkdir}/gui/templates_c
# mark symlinks as config
%config %{testlinkdir}/custom_config.inc.php
%config %{testlinkdir}/cfg

%changelog
* Tue Dec 09 2014 Richard Clark <rclark@telnic.org> - 1.9.12-2
- Patch for broken test case management for admin users
  (http://mantis.testlink.org/view.php?id=6620)

* Mon Dec 01 2014 Richard Clark <rclark@telnic.org> - 1.9.12-1
- Rework inital package by aodhav
- Port to SCL (due to requirement for php 5.4)
