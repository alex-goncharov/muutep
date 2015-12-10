Name:		ngx_openresty
Version:	%{version}
Release:	%{release}
Summary:	a fast web app server by extending nginx
Group:		Productivity/Networking/Web/Servers
License:	BSD
URL:		openresty.org
Source0:	http://openresty.org/download/%{name}-%{version}.tar.gz

BuildRequires:	sed openssl-devel pcre-devel readline-devel
requires:       nginx
Requires:	openssl pcre readline
Requires(pre):	shadow-utils

%define user nginx
%define homedir %{_usr}/local/openresty

%description
OpenResty (aka. ngx_openresty) is a full-fledged web application server by bundling the standard Nginx core, lots of 3rd-party Nginx modules, as well as most of their external dependencies.


%prep
%setup -q

%build
./configure --with-pcre-jit --with-luajit
make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)

%{homedir}/luajit/*
%{homedir}/lualib/*
%{homedir}/nginx
%{homedir}/nginx/html/*
%{homedir}/nginx/logs
%{homedir}/nginx/sbin
%{homedir}/nginx/sbin/nginx
%{homedir}/bin/resty

%{homedir}/nginx/conf
%{homedir}/nginx/conf/fastcgi.conf.default
%{homedir}/nginx/conf/fastcgi_params.default
%{homedir}/nginx/conf/mime.types.default
%{homedir}/nginx/conf/nginx.conf.default
%{homedir}/nginx/conf/scgi_params.default
%{homedir}/nginx/conf/uwsgi_params.default

%config %{homedir}/nginx/conf/fastcgi.conf
%config %{homedir}/nginx/conf/fastcgi_params
%config %{homedir}/nginx/conf/koi-utf
%config %{homedir}/nginx/conf/koi-win
%config %{homedir}/nginx/conf/mime.types
%config %{homedir}/nginx/conf/nginx.conf
%config %{homedir}/nginx/conf/scgi_params
%config %{homedir}/nginx/conf/uwsgi_params
%config %{homedir}/nginx/conf/win-utf


%postun


%changelog

