Name:           pobierznik
Version:        0.0.1
Release:        1
Summary:        A powerful video downloader and streaming application
License:        GPL-3.0
URL:            https://github.com/Tears-of-Mandrake/pobierznik
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  python3dist(pip)
BuildRequires:  python3dist(setuptools)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  desktop-file-utils

Requires:       python3dist(yt-dlp)
Requires:       python3dist(pygobject)
Requires:       gtk4
Requires:       libadwaita-common
Requires:       typelib(Adw)
Requires:       python-gi
Requires:       python-gobject3
Requires:       glib2
Requires:       streamlink

%description
Pobierznik is a powerful and user-friendly video downloader and streaming application
built with GTK4 and libadwaita. It supports downloading videos from various platforms
like YouTube, Vimeo, and more. Features include batch downloading, streaming, download
history management, and configurable video quality settings.

Pobierznik – a name inspired by Old Polish and Slavic word formation, referencing historical noun forms that denoted a person performing a specific action (e.g., miecznik – swordsmith, garncarz – potter). The word pobierać is deeply rooted in the Polish language, meaning both "to download" and "to acquire." Pobierznik is a unique and familiar-sounding application for downloading and playing video streams, serving as a frontend for Streamlink. The name evokes the spirit of old craftsmen and simplicity, blending tradition with modern technology.

%prep
%autosetup -n %{name}-%{version} -p1

%build
# Create the executable script
cat > pobierznik << EOF
#!/bin/sh
exec python3 /usr/share/tears-of-mandrake/pobierznik/main.py "\$@"
EOF

%install
# Create directories
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/tears-of-mandrake/pobierznik
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/128x128/apps
mkdir -p %{buildroot}%{_datadir}/glib-2.0/schemas

# Install Python files
install -m 755 main.py %{buildroot}%{_datadir}/tears-of-mandrake/pobierznik/

# Install executable
install -m 755 pobierznik %{buildroot}%{_bindir}/

# Install desktop file
cat > %{buildroot}%{_datadir}/applications/com.tearsofmandrake.pobierznik.desktop << EOF
[Desktop Entry]
Name=Pobierznik
Comment=Download and stream videos from various platforms
Exec=pobierznik
Icon=pobierznik
Terminal=false
Type=Application
Categories=AudioVideo;Video;Network;
Keywords=video;stream;download;youtube;
StartupNotify=true
EOF

# Install icon
install -m 644 pobierznik.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/pobierznik.png

# Install GSchema
install -m 644 com.tearsofmandrake.pobierznik.gschema.xml %{buildroot}%{_datadir}/glib-2.0/schemas/

%post
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &> /dev/null || :
/usr/bin/update-desktop-database &> /dev/null || :
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%postun
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &> /dev/null || :
/usr/bin/update-desktop-database &> /dev/null || :
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &> /dev/null || :

%files
%license LICENSE
%doc README.md
%{_bindir}/pobierznik
%{_datadir}/tears-of-mandrake/pobierznik/
%{_datadir}/applications/com.tearsofmandrake.pobierznik.desktop
%{_datadir}/icons/hicolor/128x128/apps/pobierznik.png
%{_datadir}/glib-2.0/schemas/com.tearsofmandrake.pobierznik.gschema.xml

%changelog
* Wed Jan 31 2025 Tears of Mandrake, Damian Marcin Szymański <angrypenguinpoland@gmail.com> - 0.0.1-1
- Initial package release
