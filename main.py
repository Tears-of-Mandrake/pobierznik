import sys
import gi
import threading
import yt_dlp
import streamlink
import subprocess
import os
from urllib.parse import urlparse

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio, GObject, Gdk, GdkPixbuf

class QualityDialog(Gtk.Dialog):
    def __init__(self, parent, qualities):
        super().__init__(
            title="Select Stream Quality",
            transient_for=parent,
            use_header_bar=True,
            modal=True
        )
        
        self.selected_quality = None
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        content_area = self.get_content_area()
        content_area.append(content_box)
        
        label = Gtk.Label(label="Choose streaming quality:")
        content_box.append(label)
        
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.connect('row-activated', self.on_quality_selected)
        content_box.append(list_box)
        
        for quality in qualities:
            row = Gtk.ListBoxRow()
            row.quality = quality
            label = Gtk.Label(label=quality)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            label.set_margin_start(12)
            label.set_margin_end(12)
            row.set_child(label)
            list_box.append(row)
            
    def on_quality_selected(self, list_box, row):
        self.selected_quality = row.quality
        self.close()

class MPVQualityDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(
            title="Select Video Quality",
            transient_for=parent,
            use_header_bar=True,
            modal=True
        )
        
        self.selected_quality = None
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        content_area = self.get_content_area()
        content_area.append(content_box)
        
        label = Gtk.Label(label="Choose video quality:")
        content_box.append(label)
        
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.connect('row-activated', self.on_quality_selected)
        content_box.append(list_box)
        
        # Common video qualities with their ytdl-format strings
        qualities = [
            ("Best", "bestvideo+bestaudio/best"),
            ("2160p (4K)", "bestvideo[height<=2160]+bestaudio/best[height<=2160]"),
            ("1440p (2K)", "bestvideo[height<=1440]+bestaudio/best[height<=1440]"),
            ("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
            ("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
            ("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
            ("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]"),
            ("240p", "bestvideo[height<=240]+bestaudio/best[height<=240]"),
            ("Lowest", "worstvideo+worstaudio/worst")
        ]
        
        for label, format_str in qualities:
            row = Gtk.ListBoxRow()
            row.quality = format_str
            label = Gtk.Label(label=label)
            label.set_margin_top(6)
            label.set_margin_bottom(6)
            label.set_margin_start(12)
            label.set_margin_end(12)
            row.set_child(label)
            list_box.append(row)
            
    def on_quality_selected(self, list_box, row):
        self.selected_quality = row.quality
        self.close()

class DownloadPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window = window
        
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Description
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        desc_box.set_margin_bottom(12)
        self.append(desc_box)
        
        title = Gtk.Label()
        title.set_markup("<b>Video Download</b>")
        title.set_halign(Gtk.Align.START)
        desc_box.append(title)
        
        description = Gtk.Label(
            label="Download videos from various platforms including YouTube, Vimeo, and more.\n"
                  "Simply paste the video URL and click Download to save it locally, or Watch to play it directly in MPV with your preferred quality."
        )
        description.set_wrap(True)
        description.set_halign(Gtk.Align.START)
        description.add_css_class("caption")
        desc_box.append(description)
        
        # URL entry
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.append(url_box)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter video URL to download...")
        self.url_entry.set_hexpand(True)
        url_box.append(self.url_entry)
        
        # Watch button
        self.watch_button = Gtk.Button(label="Watch")
        self.watch_button.connect("clicked", self.on_watch_clicked)
        url_box.append(self.watch_button)
        
        # Download button
        self.download_button = Gtk.Button(label="Download")
        self.download_button.connect("clicked", self.on_download_clicked)
        self.download_button.add_css_class("suggested-action")
        url_box.append(self.download_button)
        
        # Progress area
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.append(self.progress_bar)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.append(self.status_label)
        
        # Downloads list
        downloads_label = Gtk.Label()
        downloads_label.set_markup("<b>Download History</b>")
        downloads_label.set_halign(Gtk.Align.START)
        downloads_label.set_margin_top(12)
        self.append(downloads_label)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.append(scrolled)
        
        self.downloads_list = Gtk.ListBox()
        self.downloads_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.downloads_list)
        
        # Store downloaded files info
        self.downloaded_files = {}  # Store filepath and title for each download

    def format_size(self, size):
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def strip_ansi(self, text):
        """Remove ANSI escape codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def format_progress_text(self, d):
        try:
            # Get the progress percentage
            progress = self.strip_ansi(d.get('_percent_str', '0%')).strip()
            
            # Get downloaded size and total size
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            # Format sizes
            if total > 0:
                downloaded_str = self.format_size(downloaded)
                total_str = self.format_size(total)
                size_text = f"({downloaded_str} of {total_str})"
            else:
                size_text = f"({self.format_size(downloaded)})"
            
            # Get speed
            speed = d.get('speed', 0) or 0
            speed_text = f"at {self.format_size(speed)}/s" if speed > 0 else ""
            
            # Combine all parts
            return f"{progress} {size_text} {speed_text}".strip()
        except Exception as e:
            print(f"Error formatting progress text: {e}")
            return "Downloading..."

    def show_quality_dialog(self):
        dialog = MPVQualityDialog(self.window)
        dialog.present()
        return dialog
        
    def on_watch_clicked(self, button):
        url = self.url_entry.get_text()
        if not url:
            return
            
        def stream_video(video_url):
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    stream_url = info.get('url')
                    if not stream_url:
                        # If direct URL is not available, try getting the best format
                        formats = info.get('formats', [])
                        if formats:
                            # Get the best format with both video and audio
                            best_format = None
                            for f in formats:
                                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                                    if best_format is None or f.get('quality', 0) > best_format.get('quality', 0):
                                        best_format = f
                            
                            if best_format:
                                stream_url = best_format['url']
                    
                    if not stream_url:
                        raise ValueError("Could not find a playable stream URL")
                    
                    # Use the configured video player
                    try:
                        play_video(stream_url)
                    except Exception as e:
                        GLib.idle_add(
                            self.show_error_dialog,
                            "Error Playing Video",
                            str(e)
                        )
            except Exception as e:
                GLib.idle_add(
                    self.show_error_dialog,
                    "Error",
                    f"Could not stream video: {str(e)}"
                )
                
        thread = threading.Thread(target=stream_video, args=(url,))
        thread.daemon = True
        thread.start()
        
    def on_quality_selected(self, dialog):
        selected_quality = dialog.selected_quality
        if selected_quality:
            url = self.url_entry.get_text()
            try:
                subprocess.Popen(['mpv', f'--ytdl-format={selected_quality}', url])
                self.status_label.set_text(f"Playing video in selected quality")
            except Exception as e:
                self.status_label.set_text(f"Error launching player: {str(e)}")
                
    def add_to_downloads_list(self, title, status, filepath=None):
        row = Gtk.ListBoxRow()
        
        # Main horizontal box
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.set_margin_top(6)
        main_box.set_margin_bottom(6)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        
        # Left side with title and status
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_hexpand(True)
        main_box.append(info_box)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(True)
        info_box.append(title_label)
        
        status_label = Gtk.Label(label=status)
        status_label.set_halign(Gtk.Align.START)
        status_label.add_css_class("caption")
        info_box.append(status_label)
        
        # Right side with action buttons
        if status == "Completed" and filepath:
            # Store file info
            self.downloaded_files[row] = {"title": title, "filepath": filepath}
            
            buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            main_box.append(buttons_box)
            
            # Play button
            play_button = Gtk.Button()
            play_button.set_icon_name("media-playback-start-symbolic")
            play_button.set_tooltip_text("Play video")
            play_button.connect("clicked", self.on_play_clicked, row)
            buttons_box.append(play_button)
            
            # Remove from list button
            remove_button = Gtk.Button()
            remove_button.set_icon_name("list-remove-symbolic")
            remove_button.set_tooltip_text("Remove from list")
            remove_button.connect("clicked", self.on_remove_clicked, row)
            buttons_box.append(remove_button)
            
            # Delete from disk button
            delete_button = Gtk.Button()
            delete_button.set_icon_name("user-trash-symbolic")
            delete_button.set_tooltip_text("Delete from disk")
            delete_button.add_css_class("destructive-action")
            delete_button.connect("clicked", self.on_delete_clicked, row)
            buttons_box.append(delete_button)
        
        row.set_child(main_box)
        self.downloads_list.prepend(row)
        
    def on_play_clicked(self, button, row):
        file_info = self.downloaded_files.get(row)
        if file_info and os.path.exists(file_info["filepath"]):
            thread = threading.Thread(target=self.play_video, args=(file_info["filepath"],))
            thread.daemon = True
            thread.start()
        
    def on_remove_clicked(self, button, row):
        if row in self.downloaded_files:
            del self.downloaded_files[row]
        self.downloads_list.remove(row)
        
    def on_delete_clicked(self, button, row):
        def delete_confirmation():
            dialog = Adw.MessageDialog.new(
                self.window,
                "Delete Video File",
                f"Are you sure you want to delete '{self.downloaded_files[row]['title']}'?\nThis action cannot be undone."
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("delete", "Delete")
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self.on_delete_response, row, button)
            dialog.present()
        
        GLib.idle_add(delete_confirmation)
    
    def on_delete_response(self, dialog, response, row, button):
        if response == "delete":
            file_info = self.downloaded_files.get(row)
            if file_info and os.path.exists(file_info["filepath"]):
                try:
                    os.remove(file_info["filepath"])
                    self.on_remove_clicked(button, row)
                except OSError as e:
                    error_dialog = Adw.MessageDialog.new(
                        self.window,
                        "Error Deleting File",
                        str(e)
                    )
                    error_dialog.add_response("ok", "OK")
                    error_dialog.present()
        dialog.close()
            
    def show_error_dialog(self, title, message):
        dialog = Adw.MessageDialog.new(
            self.window,
            title,
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def play_video(self, filepath):
        try:
            thread = threading.Thread(target=play_video, args=(filepath,))
            thread.daemon = True
            thread.start()
        except Exception as e:
            GLib.idle_add(
                self.show_error_dialog,
                "Error Playing Video",
                str(e)
            )
            
    def download_video(self, url, progress_bar, status_label):
        def progress_hook(d):
            if d['status'] == 'downloading':
                progress = self.strip_ansi(d.get('_percent_str', '0%')).replace('%', '').strip()
                try:
                    progress_float = float(progress) / 100
                    progress_text = self.format_progress_text(d)
                    
                    def update_ui():
                        progress_bar.set_fraction(progress_float)
                        progress_bar.set_show_text(True)
                        progress_bar.set_text(progress_text)
                        status_label.set_text(progress_text)
                    
                    GLib.idle_add(update_ui)
                except ValueError as e:
                    print(f"Error updating progress: {e}")
                    pass
        
        # Get options from settings
        ydl_opts = get_yt_dlp_options()
        ydl_opts['progress_hooks'] = [progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                GLib.idle_add(status_label.set_text, "Starting download...")
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Title')
                
                # Prepare filename based on format
                settings = Gio.Settings.new("com.tearsofmandrake.pobierznik")
                preferred_format = settings.get_string("preferred-format")
                
                if preferred_format == "audio":
                    # For audio-only downloads, force .mp3 extension
                    filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                else:
                    filename = ydl.prepare_filename(info)
                
                # Start download
                ydl.download([url])
                
                GLib.idle_add(status_label.set_text, "Download completed!")
                GLib.idle_add(progress_bar.set_fraction, 1.0)
                
                # Get the actual filepath after download
                filepath = os.path.abspath(filename)
                GLib.idle_add(self.add_to_downloads_list, title, "Completed", filepath)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            GLib.idle_add(status_label.set_text, error_msg)
            GLib.idle_add(self.add_to_downloads_list, url, "Failed")
            
    def on_download_clicked(self, button):
        url = self.url_entry.get_text()
        if not url:
            self.status_label.set_text("Please enter a URL")
            return
            
        thread = threading.Thread(target=self.download_video, args=(url, self.progress_bar, self.status_label))
        thread.daemon = True
        thread.start()
        
class BatchDownloadPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window = window
        
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Description
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        desc_box.set_margin_bottom(12)
        self.append(desc_box)
        
        title = Gtk.Label()
        title.set_markup("<b>Batch Download</b>")
        title.set_halign(Gtk.Align.START)
        desc_box.append(title)
        
        description = Gtk.Label(
            label="Download multiple videos at once from various platforms.\n"
                  "Enter URLs (one per line) in the text area below and click Download All to start downloading."
        )
        description.set_wrap(True)
        description.set_halign(Gtk.Align.START)
        description.add_css_class("caption")
        desc_box.append(description)
        
        # URLs text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_min_content_height(200)
        scrolled.set_vexpand(True)
        self.append(scrolled)
        
        self.batch_urls_view = Gtk.TextView()
        self.batch_urls_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.batch_urls_view.get_buffer().set_text("Enter URLs here (one per line)...")
        self.batch_urls_view.connect("notify::has-focus", self.on_batch_urls_focus_in)
        scrolled.set_child(self.batch_urls_view)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_margin_top(12)
        self.progress_bar.set_text("Ready")
        self.append(self.progress_bar)
        
        # Download button in its own box for centering
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_top(12)
        button_box.set_halign(Gtk.Align.CENTER)
        self.append(button_box)
        
        # Download button
        self.download_button = Gtk.Button(label="Download All")
        self.download_button.connect("clicked", self.on_batch_download_clicked)
        self.download_button.add_css_class("suggested-action")
        button_box.append(self.download_button)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.append(self.status_label)
        
        # Downloads list
        downloads_label = Gtk.Label()
        downloads_label.set_markup("<b>Download History</b>")
        downloads_label.set_halign(Gtk.Align.START)
        downloads_label.set_margin_top(12)
        self.append(downloads_label)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.append(scrolled)
        
        self.downloads_list = Gtk.ListBox()
        self.downloads_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.downloads_list)
        
        # Store downloaded files info
        self.downloaded_files = {}  # Store filepath and title for each download
        
    def format_size(self, size):
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def strip_ansi(self, text):
        """Remove ANSI escape codes from text"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def format_progress_text(self, d):
        try:
            # Get the progress percentage
            progress = self.strip_ansi(d.get('_percent_str', '0%')).strip()
            
            # Get downloaded size and total size
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            # Format sizes
            if total > 0:
                downloaded_str = self.format_size(downloaded)
                total_str = self.format_size(total)
                size_text = f"({downloaded_str} of {total_str})"
            else:
                size_text = f"({self.format_size(downloaded)})"
            
            # Get speed
            speed = d.get('speed', 0) or 0
            speed_text = f"at {self.format_size(speed)}/s" if speed > 0 else ""
            
            # Combine all parts
            return f"{progress} {size_text} {speed_text}".strip()
        except Exception as e:
            print(f"Error formatting progress text: {e}")
            return "Downloading..."

    def on_batch_urls_focus_in(self, widget, event):
        if widget.has_focus():
            buffer = widget.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            if text == "Enter URLs here (one per line)...":
                buffer.set_text("")
        return False
        
    def add_to_downloads_list(self, title, status, filepath=None):
        row = Gtk.ListBoxRow()
        
        # Main horizontal box
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.set_margin_top(6)
        main_box.set_margin_bottom(6)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        
        # Left side with title and status
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_hexpand(True)
        main_box.append(info_box)
        
        title_label = Gtk.Label(label=title)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_ellipsize(True)
        info_box.append(title_label)
        
        status_label = Gtk.Label(label=status)
        status_label.set_halign(Gtk.Align.START)
        status_label.add_css_class("caption")
        info_box.append(status_label)
        
        # Right side with action buttons
        if status == "Completed" and filepath:
            # Store file info
            self.downloaded_files[row] = {"title": title, "filepath": filepath}
            
            buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            main_box.append(buttons_box)
            
            # Play button
            play_button = Gtk.Button()
            play_button.set_icon_name("media-playback-start-symbolic")
            play_button.set_tooltip_text("Play video")
            play_button.connect("clicked", self.on_play_clicked, row)
            buttons_box.append(play_button)
            
            # Remove from list button
            remove_button = Gtk.Button()
            remove_button.set_icon_name("list-remove-symbolic")
            remove_button.set_tooltip_text("Remove from list")
            remove_button.connect("clicked", self.on_remove_clicked, row)
            buttons_box.append(remove_button)
            
            # Delete from disk button
            delete_button = Gtk.Button()
            delete_button.set_icon_name("user-trash-symbolic")
            delete_button.set_tooltip_text("Delete from disk")
            delete_button.add_css_class("destructive-action")
            delete_button.connect("clicked", self.on_delete_clicked, row)
            buttons_box.append(delete_button)
        
        row.set_child(main_box)
        self.downloads_list.prepend(row)
        
    def on_play_clicked(self, button, row):
        file_info = self.downloaded_files.get(row)
        if file_info and os.path.exists(file_info["filepath"]):
            thread = threading.Thread(target=self.play_video, args=(file_info["filepath"],))
            thread.daemon = True
            thread.start()
        
    def on_remove_clicked(self, button, row):
        if row in self.downloaded_files:
            del self.downloaded_files[row]
        self.downloads_list.remove(row)
        
    def on_delete_clicked(self, button, row):
        def delete_confirmation():
            dialog = Adw.MessageDialog.new(
                self.window,
                "Delete Video File",
                f"Are you sure you want to delete '{self.downloaded_files[row]['title']}'?\nThis action cannot be undone."
            )
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("delete", "Delete")
            dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
            dialog.connect("response", self.on_delete_response, row, button)
            dialog.present()
        
        GLib.idle_add(delete_confirmation)
    
    def on_delete_response(self, dialog, response, row, button):
        if response == "delete":
            file_info = self.downloaded_files.get(row)
            if file_info and os.path.exists(file_info["filepath"]):
                try:
                    os.remove(file_info["filepath"])
                    self.on_remove_clicked(button, row)
                except OSError as e:
                    error_dialog = Adw.MessageDialog.new(
                        self.window,
                        "Error Deleting File",
                        str(e)
                    )
                    error_dialog.add_response("ok", "OK")
                    error_dialog.present()
        dialog.close()
            
    def show_error_dialog(self, title, message):
        dialog = Adw.MessageDialog.new(
            self.window,
            title,
            message
        )
        dialog.add_response("ok", "OK")
        dialog.present()

    def play_video(self, filepath):
        try:
            thread = threading.Thread(target=play_video, args=(filepath,))
            thread.daemon = True
            thread.start()
        except Exception as e:
            GLib.idle_add(
                self.show_error_dialog,
                "Error Playing Video",
                str(e)
            )
            
    def on_batch_download_clicked(self, button):
        buffer = self.batch_urls_view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        
        if text.strip() == "" or text == "Enter URLs here (one per line)...":
            self.status_label.set_text("Please enter URLs to download")
            return
            
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        if not urls:
            self.status_label.set_text("No valid URLs found")
            return
            
        thread = threading.Thread(target=self.batch_download_videos, args=(urls,))
        thread.daemon = True
        thread.start()
        
    def download_video(self, url, progress_bar, status_label):
        def progress_hook(d):
            if d['status'] == 'downloading':
                progress = self.strip_ansi(d.get('_percent_str', '0%')).replace('%', '').strip()
                try:
                    progress_float = float(progress) / 100
                    progress_text = self.format_progress_text(d)
                    
                    def update_ui():
                        progress_bar.set_fraction(progress_float)
                        progress_bar.set_show_text(True)
                        progress_bar.set_text(progress_text)
                        status_label.set_text(progress_text)
                    
                    GLib.idle_add(update_ui)
                except ValueError as e:
                    print(f"Error updating progress: {e}")
                    pass
        
        # Get options from settings
        ydl_opts = get_yt_dlp_options()
        ydl_opts['progress_hooks'] = [progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                GLib.idle_add(status_label.set_text, "Starting download...")
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Unknown Title')
                
                # Prepare filename based on format
                settings = Gio.Settings.new("com.tearsofmandrake.pobierznik")
                preferred_format = settings.get_string("preferred-format")
                
                if preferred_format == "audio":
                    # For audio-only downloads, force .mp3 extension
                    filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
                else:
                    filename = ydl.prepare_filename(info)
                
                # Start download
                ydl.download([url])
                
                GLib.idle_add(status_label.set_text, "Download completed!")
                GLib.idle_add(progress_bar.set_fraction, 1.0)
                
                # Get the actual filepath after download
                filepath = os.path.abspath(filename)
                GLib.idle_add(self.add_to_downloads_list, title, "Completed", filepath)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            GLib.idle_add(status_label.set_text, error_msg)
            GLib.idle_add(self.add_to_downloads_list, url, "Failed")
            
    def batch_download_videos(self, urls):
        total_urls = len(urls)
        completed = 0
        
        GLib.idle_add(self.status_label.set_text, f"Downloading {total_urls} videos...")
        GLib.idle_add(self.progress_bar.set_fraction, 0.0)
        
        for url in urls:
            self.download_video(url, self.progress_bar, self.status_label)
            completed += 1
            progress = completed / total_urls
            GLib.idle_add(self.progress_bar.set_fraction, progress)
            
        GLib.idle_add(self.status_label.set_text, f"Completed downloading {completed} of {total_urls} videos")

class StreamPage(Gtk.Box):
    def __init__(self, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.window = window
        
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        
        # Description
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        desc_box.set_margin_bottom(12)
        self.append(desc_box)
        
        title = Gtk.Label()
        title.set_markup("<b>Live Stream Player</b>")
        title.set_halign(Gtk.Align.START)
        desc_box.append(title)
        
        description = Gtk.Label(
            label="Watch live streams from various platforms including Twitch, YouTube Live, and more.\n"
                  "Enter the stream URL, choose your preferred quality, and enjoy the stream using MPV player."
        )
        description.set_wrap(True)
        description.set_halign(Gtk.Align.START)
        description.add_css_class("caption")
        desc_box.append(description)
        
        # URL entry
        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.append(url_box)
        
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Enter stream URL...")
        url_box.append(self.url_entry)
        
        self.stream_button = Gtk.Button(label="Stream")
        self.stream_button.connect("clicked", self.on_stream_clicked)
        self.stream_button.add_css_class("suggested-action")
        url_box.append(self.stream_button)
        
        self.status_label = Gtk.Label()
        self.status_label.set_wrap(True)
        self.append(self.status_label)
        
        label = Gtk.Label()
        label.set_markup("<b>Recent Streams</b>")
        label.set_margin_top(12)
        self.append(label)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.append(scrolled)
        
        self.streams_list = Gtk.ListBox()
        self.streams_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.streams_list)
        
    def show_quality_dialog(self, streams):
        dialog = QualityDialog(self.window, list(streams.keys()))
        dialog.present()
        return dialog
        
    def on_stream_clicked(self, button):
        url = self.url_entry.get_text()
        if not url:
            self.status_label.set_text("Please enter a URL")
            return
            
        thread = threading.Thread(target=self.stream_video, args=(url,))
        thread.daemon = True
        thread.start()
        
    def stream_video(self, url):
        try:
            streams = streamlink.streams(url)
            if streams:
                def show_dialog():
                    dialog = self.show_quality_dialog(streams)
                    dialog.connect("close-request", lambda d: self.on_quality_selected(d, streams))
                
                GLib.idle_add(show_dialog)
            else:
                GLib.idle_add(self.status_label.set_text, "No streams found")
        except Exception as e:
            GLib.idle_add(self.status_label.set_text, f"Error: {str(e)}")
            
    def on_quality_selected(self, dialog, streams):
        selected_quality = dialog.selected_quality
        if selected_quality:
            stream_url = streams[selected_quality].url
            try:
                subprocess.Popen(['mpv', stream_url])
                GLib.idle_add(self.status_label.set_text, f"Playing stream in {selected_quality} quality")
                
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                box.set_margin_top(6)
                box.set_margin_bottom(6)
                box.set_margin_start(12)
                box.set_margin_end(12)
                
                label = Gtk.Label(label=self.url_entry.get_text())
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.START)
                label.set_ellipsize(True)
                box.append(label)
                
                quality_label = Gtk.Label(label=selected_quality)
                quality_label.add_css_class("caption")
                box.append(quality_label)
                
                row.set_child(box)
                self.streams_list.prepend(row)
                
            except Exception as e:
                GLib.idle_add(self.status_label.set_text, f"Error launching player: {str(e)}")

class PobierznikWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.set_title("Pobierznik")
        self.set_default_size(800, 600)
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(self.main_box)
        
        header = Adw.HeaderBar()
        self.main_box.append(header)
        
        view_switcher = Adw.ViewSwitcher()
        view_switcher.set_policy(Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(view_switcher)
        
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        header.pack_end(menu_button)
        
        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("About", "app.about")
        menu_button.set_menu_model(menu)
        
        self.stack = Adw.ViewStack()
        self.stack.set_vexpand(True)
        self.main_box.append(self.stack)
        
        # Add pages
        self.download_page = DownloadPage(self)
        self.stack.add_titled_with_icon(
            self.download_page,
            "download",
            "Download",
            "document-save-symbolic"
        )
        
        self.batch_download_page = BatchDownloadPage(self)
        self.stack.add_titled_with_icon(
            self.batch_download_page,
            "batch",
            "Batch Download",
            "view-list-symbolic"
        )
        
        self.stream_page = StreamPage(self)
        self.stack.add_titled_with_icon(
            self.stream_page,
            "stream",
            "Stream",
            "media-playback-start-symbolic"
        )
        
        view_switcher.set_stack(self.stack)

class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)
        
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_title("Preferences")
        
        # Load settings
        self.settings = Gio.Settings.new("com.tearsofmandrake.pobierznik")
        
        # Create pages
        self.general_page = Adw.PreferencesPage()
        self.general_page.set_title("General")
        self.general_page.set_icon_name("preferences-system-symbolic")
        self.add(self.general_page)
        
        # Player Settings Group
        player_group = Adw.PreferencesGroup()
        player_group.set_title("Video Player Settings")
        self.general_page.add(player_group)
        
        # Video Player Selection
        player_row = Adw.ComboRow()
        player_row.set_title("Video Player")
        player_row.set_subtitle("Choose default video player for playback")
        player_row.set_model(Gtk.StringList.new([
            "MPV",
            "VLC",
            "MPlayer",
            "Clapper",
            "QMPlay2",
            "Custom"
        ]))
        current_player = self.settings.get_string("video-player")
        players = {"mpv": 0, "vlc": 1, "mplayer": 2, "clapper": 3, "qmplay2": 4}
        player_row.set_selected(players.get(current_player, 5))
        player_row.connect("notify::selected", self.on_player_changed)
        player_group.add(player_row)
        
        # Custom Player Path
        custom_player_row = Adw.ActionRow()
        custom_player_row.set_title("Custom Player Path")
        custom_player_row.set_subtitle("Select executable for custom video player")
        
        custom_player_button = Gtk.Button()
        custom_player_button.set_label(self.settings.get_string("custom-player-path") or "Choose Player")
        custom_player_button.connect("clicked", self.on_custom_player_clicked)
        custom_player_row.add_suffix(custom_player_button)
        player_group.add(custom_player_row)
        
        # Download Settings Group
        download_group = Adw.PreferencesGroup()
        download_group.set_title("Download Settings")
        self.general_page.add(download_group)
        
        # Download Directory
        dir_row = Adw.ActionRow()
        dir_row.set_title("Download Directory")
        dir_row.set_subtitle("Choose where to save downloaded files")
        
        dir_button = Gtk.Button()
        dir_button.set_label(self.settings.get_string("download-directory") or "Choose Directory")
        dir_button.connect("clicked", self.on_directory_clicked)
        dir_row.add_suffix(dir_button)
        download_group.add(dir_row)
        
        # Speed Limit
        speed_row = Adw.ActionRow()
        speed_row.set_title("Speed Limit")
        speed_row.set_subtitle("Limit download speed (KB/s, 0 for unlimited)")
        
        speed_adj = Gtk.Adjustment(
            value=self.settings.get_int("download-speed-limit"),
            lower=0,
            upper=100000,
            step_increment=100
        )
        speed_spin = Gtk.SpinButton()
        speed_spin.set_adjustment(speed_adj)
        speed_spin.connect("value-changed", self.on_speed_changed)
        speed_row.add_suffix(speed_spin)
        download_group.add(speed_row)
        
        # Format Settings Group
        format_group = Adw.PreferencesGroup()
        format_group.set_title("Format Settings")
        self.general_page.add(format_group)
        
        # Preferred Format
        format_row = Adw.ComboRow()
        format_row.set_title("Preferred Format")
        format_row.set_subtitle("Choose default download format")
        format_row.set_model(Gtk.StringList.new([
            "Best Quality (Video + Audio)",
            "Audio Only (MP3)",
            "Custom Quality"
        ]))
        current_format = self.settings.get_string("preferred-format")
        format_row.set_selected(0 if current_format == "best" else 1 if current_format == "audio" else 2)
        format_row.connect("notify::selected", self.on_format_changed)
        format_group.add(format_row)
        
        # Audio Quality
        audio_row = Adw.ActionRow()
        audio_row.set_title("Audio Quality")
        audio_row.set_subtitle("Audio quality in kbps (for audio-only downloads)")
        
        audio_adj = Gtk.Adjustment(
            value=self.settings.get_int("audio-quality"),
            lower=64,
            upper=320,
            step_increment=32
        )
        audio_spin = Gtk.SpinButton()
        audio_spin.set_adjustment(audio_adj)
        audio_spin.connect("value-changed", self.on_audio_quality_changed)
        audio_row.add_suffix(audio_spin)
        format_group.add(audio_row)
        
        # Video Quality
        video_row = Adw.ComboRow()
        video_row.set_title("Video Quality")
        video_row.set_subtitle("Preferred video quality (for custom quality)")
        video_row.set_model(Gtk.StringList.new([
            "1080p",
            "720p",
            "480p",
            "360p"
        ]))
        current_quality = self.settings.get_string("video-quality")
        video_row.set_selected(0 if current_quality == "1080p" else 
                             1 if current_quality == "720p" else 
                             2 if current_quality == "480p" else 3)
        video_row.connect("notify::selected", self.on_video_quality_changed)
        format_group.add(video_row)
        
    def on_directory_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Choose Download Directory",
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Select", Gtk.ResponseType.OK)
        
        def on_response(dialog, response):
            if response == Gtk.ResponseType.OK:
                path = dialog.get_file().get_path()
                self.settings.set_string("download-directory", path)
                button.set_label(path)
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()
        
    def on_speed_changed(self, spin_button):
        self.settings.set_int("download-speed-limit", spin_button.get_value_as_int())
        
    def on_format_changed(self, combo_row, *args):
        formats = ["best", "audio", "custom"]
        self.settings.set_string("preferred-format", formats[combo_row.get_selected()])
        
    def on_audio_quality_changed(self, spin_button):
        self.settings.set_int("audio-quality", spin_button.get_value_as_int())
        
    def on_video_quality_changed(self, combo_row, *args):
        qualities = ["1080p", "720p", "480p", "360p"]
        self.settings.set_string("video-quality", qualities[combo_row.get_selected()])
        
    def on_player_changed(self, combo_row, *args):
        players = ["mpv", "vlc", "mplayer", "clapper", "qmplay2", "custom"]
        self.settings.set_string("video-player", players[combo_row.get_selected()])
        
    def on_custom_player_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Choose Video Player",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Select", Gtk.ResponseType.OK)
        
        def on_response(dialog, response):
            if response == Gtk.ResponseType.OK:
                path = dialog.get_file().get_path()
                self.settings.set_string("custom-player-path", path)
                button.set_label(path)
            dialog.destroy()
        
        dialog.connect("response", on_response)
        dialog.present()

class PobierznikApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
        
    def on_activate(self, app):
        self.win = PobierznikWindow(application=app)
        self.win.present()

    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        
    def on_preferences_action(self, widget, _):
        prefs = PreferencesWindow(parent=self.props.active_window)
        prefs.present()
        
    def on_about_action(self, widget, _):
        try:
            about = Adw.AboutWindow(
                transient_for=self.props.active_window,
                application_name="Pobierznik",
                application_icon="pobierznik",
                version="0.0.1",
                developer_name="Tears of Mandrake",
                website="https://github.com/Tears-of-Mandrake",
                issue_url="https://github.com/Tears-of-Mandrake/pobierznik/issues",
                developers=["Tears of Mandrake"],
                copyright=" 2025 Tears of Mandrake",
                license_type=Gtk.License.GPL_3_0,
                comments="A powerful video downloader and streaming application.\n\n"
                        "Features:\n"
                        "• Download videos from various platforms\n"
                        "• Stream videos directly using your preferred video player\n"
                        "• Batch download multiple videos\n"
                        "• Download history management\n"
                        "• Video quality selection"
            )
            about.present()
            
        except Exception as e:
            print(f"Error loading icon: {e}")
            # Fallback to default icon if loading fails
            about = Adw.AboutWindow(
                transient_for=self.props.active_window,
                application_name="Pobierznik",
                application_icon="video-display",
                version="0.0.1",
                developer_name="Tears of Mandrake",
                website="https://github.com/Tears-of-Mandrake",
                issue_url="https://github.com/Tears-of-Mandrake/pobierznik/issues",
                developers=["Tears of Mandrake"],
                copyright=" 2025 Tears of Mandrake",
                license_type=Gtk.License.GPL_3_0,
                comments="A powerful video downloader and streaming application.\n\n"
                        "Features:\n"
                        "• Download videos from various platforms\n"
                        "• Stream videos directly using your preferred video player\n"
                        "• Batch download multiple videos\n"
                        "• Download history management\n"
                        "• Video quality selection"
            )
            about.present()

def get_yt_dlp_options():
    settings = Gio.Settings.new("com.tearsofmandrake.pobierznik")
    
    # Base options
    options = {
        'quiet': False,
        'progress_hooks': [],  # This will be set by the download function
    }
    
    # Download directory
    download_dir = settings.get_string("download-directory")
    if download_dir:
        options['outtmpl'] = os.path.join(download_dir, '%(title)s.%(ext)s')
    else:
        options['outtmpl'] = '%(title)s.%(ext)s'
    
    # Speed limit
    speed_limit = settings.get_int("download-speed-limit")
    if speed_limit > 0:
        options['ratelimit'] = speed_limit * 1024  # Convert to bytes/s
    
    # Format settings
    preferred_format = settings.get_string("preferred-format")
    
    if preferred_format == "audio":
        options.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(settings.get_int("audio-quality")),
            }],
        })
    elif preferred_format == "custom":
        video_quality = settings.get_string("video-quality")
        height = video_quality.replace('p', '')
        options['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
    else:  # best
        options['format'] = 'bestvideo+bestaudio/best'
    
    return options

def play_video(filepath):
    """Play video using the configured video player"""
    settings = Gio.Settings.new("com.tearsofmandrake.pobierznik")
    player = settings.get_string("video-player")
    
    if player == "custom":
        player_path = settings.get_string("custom-player-path")
        if not player_path:
            raise ValueError("Custom player path not set")
        command = [player_path, filepath]
    else:
        # Add common player-specific arguments for better streaming
        if player == "mpv":
            command = [player, "--force-window=yes", filepath]
        elif player == "vlc":
            command = [player, "--play-and-exit", filepath]
        elif player == "mplayer":
            command = [player, "-really-quiet", filepath]
        elif player == "clapper":
            command = [player, filepath]
        elif player == "qmplay2":
            command = ["/usr/bin/QMPlay2", filepath]
        else:
            command = [player, filepath]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to play video: {str(e)}")
    except FileNotFoundError:
        raise RuntimeError(f"Video player '{command[0]}' not found. Please install it or choose a different player in preferences.")

def main():
    app = PobierznikApp(application_id="com.tearsofmandrake.pobierznik")
    app.create_action('preferences', app.on_preferences_action)
    app.create_action('about', app.on_about_action)
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
