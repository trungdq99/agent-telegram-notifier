#!/usr/bin/env python3
"""
Unit and Integration Tests for Google Drive Upload & 10MB Threshold Routing
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Import modules to test
from gdrive import format_size, upload_file_to_drive
from notify import build_gdrive_file_message, send_telegram_file, load_env

class TestGDriveUpload(unittest.TestCase):

    def test_format_size(self):
        self.assertEqual(format_size(500), "500.0 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(10 * 1024 * 1024), "10.0 MB")
        self.assertEqual(format_size(25.5 * 1024 * 1024), "25.5 MB")
        self.assertEqual(format_size(1.5 * 1024 * 1024 * 1024), "1.5 GB")
        self.assertEqual(format_size(None), "N/A")

    def test_build_gdrive_file_message(self):
        msg = build_gdrive_file_message(
            filename="archive_dump.zip",
            size_formatted="25.4 MB",
            drive_link="https://drive.google.com/file/d/xyz/view",
            caption="Backup database build"
        )
        self.assertIn("File Dung Lượng Lớn Đã Tải Lên Google Drive", msg)
        self.assertIn("archive_dump.zip", msg)
        self.assertIn("25.4 MB", msg)
        self.assertIn("https://drive.google.com/file/d/xyz/view", msg)
        self.assertIn("Backup database build", msg)

    def test_upload_nonexistent_file(self):
        res = upload_file_to_drive("/path/to/nonexistent/file_xyz.dat")
        self.assertFalse(res["ok"])
        self.assertIn("không tồn tại", res["error"])

    @patch("notify.send_telegram")
    @patch("notify.urllib.request.urlopen")
    def test_small_file_dispatched_via_telegram(self, mock_urlopen, mock_send_telegram):
        """File <= 10MB should dispatch directly via Telegram Bot API (sendDocument)."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"ok": true, "result": {}}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            # 1 KB file
            f.write(b"A" * 1024)
            temp_path = f.name

        try:
            config = {"GDRIVE_THRESHOLD_MB": "10"}
            ok, res = send_telegram_file(
                bot_token="test_token",
                chat_id="test_chat",
                file_path=temp_path,
                config=config
            )
            self.assertTrue(ok)
            # Should NOT have called send_telegram (which is used for Drive links), but rather urllib for multipart
            mock_send_telegram.assert_not_called()
            mock_urlopen.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("notify.send_telegram")
    @patch("gdrive.upload_file_to_drive")
    def test_large_file_routes_to_gdrive(self, mock_gdrive_upload, mock_send_telegram):
        """File > 10MB should automatically route to Google Drive upload."""
        mock_gdrive_upload.return_value = {
            "ok": True,
            "file_id": "mock_id_123",
            "filename": "large_file.dat",
            "size_bytes": 12 * 1024 * 1024,
            "size_formatted": "12.0 MB",
            "share_link": "https://drive.google.com/file/d/mock_id_123/view"
        }
        mock_send_telegram.return_value = (True, "Success")

        with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as f:
            # Write 11 MB dummy content (seek to create sparse file without burning disk)
            f.seek(11 * 1024 * 1024)
            f.write(b"\0")
            temp_path = f.name

        try:
            config = {"GDRIVE_THRESHOLD_MB": "10"}
            ok, res = send_telegram_file(
                bot_token="test_token",
                chat_id="test_chat",
                file_path=temp_path,
                config=config,
                caption="Dữ liệu lớn"
            )
            self.assertTrue(ok)
            mock_gdrive_upload.assert_called_once()
            mock_send_telegram.assert_called_once()
            # Verify call args of send_telegram
            args, _ = mock_send_telegram.call_args
            msg_sent = args[2]
            self.assertIn("https://drive.google.com/file/d/mock_id_123/view", msg_sent)
            self.assertIn("12.0 MB", msg_sent)
            self.assertIn("Dữ liệu lớn", msg_sent)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("notify.send_telegram")
    @patch("gdrive.upload_file_to_drive")
    def test_force_gdrive_routes_even_small_file(self, mock_gdrive_upload, mock_send_telegram):
        """Flag force_gdrive=True should route to Google Drive even if file is small."""
        mock_gdrive_upload.return_value = {
            "ok": True,
            "file_id": "small_id_999",
            "filename": "small.txt",
            "size_bytes": 500,
            "size_formatted": "500.0 B",
            "share_link": "https://drive.google.com/file/d/small_id_999/view"
        }
        mock_send_telegram.return_value = (True, "Success")

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Short text")
            temp_path = f.name

        try:
            config = {"GDRIVE_THRESHOLD_MB": "10"}
            ok, res = send_telegram_file(
                bot_token="test_token",
                chat_id="test_chat",
                file_path=temp_path,
                config=config,
                force_gdrive=True
            )
            self.assertTrue(ok)
            mock_gdrive_upload.assert_called_once()
            mock_send_telegram.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch("notify.send_telegram")
    @patch("gdrive.upload_file_to_drive")
    def test_custom_threshold(self, mock_gdrive_upload, mock_send_telegram):
        """Custom gdrive_threshold should be respected."""
        mock_gdrive_upload.return_value = {
            "ok": True,
            "file_id": "cust_id_888",
            "filename": "cust.dat",
            "size_bytes": 3 * 1024 * 1024,
            "size_formatted": "3.0 MB",
            "share_link": "https://drive.google.com/file/d/cust_id_888/view"
        }
        mock_send_telegram.return_value = (True, "Success")

        with tempfile.NamedTemporaryFile(suffix=".dat", delete=False) as f:
            f.seek(3 * 1024 * 1024)
            f.write(b"\0")
            temp_path = f.name

        try:
            # 3MB file with 2MB threshold -> triggers Drive upload
            ok, res = send_telegram_file(
                bot_token="test_token",
                chat_id="test_chat",
                file_path=temp_path,
                gdrive_threshold=2.0
            )
            self.assertTrue(ok)
            mock_gdrive_upload.assert_called_once()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if __name__ == "__main__":
    unittest.main()
